"""One review, end to end - especially the paths that run when things go wrong."""

from __future__ import annotations

import io
import json

import pytest

from shodann.capability import LOCAL_SMALL
from shodann.clearance import DISCLOSURE_ALLOWANCE
from shodann.llm import WIRE_ANTHROPIC, LLMConfig, LLMUnavailable, generate
from shodann.review import (
    EXIT_DEGRADED,
    _safe_citizen,
    collect_metrics,
    emergency_comment,
    main,
    pr_facts,
    review,
)
from shodann.state import CitizenRecord, citizen_path, load_citizen_history
from shodann.validator import REDUCED_ALLOCATION, STANDARD, blocks_posting, validate
from shodann.velocity import CodeMetrics

EVENT = {
    "pull_request": {
        "number": 42,
        "title": "Add inventory tests",
        "changed_files": 4,
        "additions": 120,
        "deletions": 18,
        "commits": 3,
        "user": {"login": "octocat"},
    }
}

GOOD_RESPONSE = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @octocat | **Clearance**: RED | **Velocity**: 9.0

### \U0001f680 Shipping Velocity Report

Four files moved and three commits landed. The Algorithm has observed steady progress.

### ✅ Algorithm-Approved Patterns

- Tests arrived with the feature.

### \U0001f4c8 Growth Opportunities

- The Algorithm suggests naming the helper for what it returns.

### \U0001f527 Recommended Iteration

Add one test for the empty branch.

*The Algorithm sees your growth. The Algorithm is pleased.*
"""


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def responder(*bodies: str):
    """An opener that returns each body in turn, recording the prompts it saw."""
    seen: list[str] = []
    remaining = list(bodies)

    def opener(request, timeout=None):
        seen.append(json.loads(request.data)["messages"][0]["content"])
        payload = {"choices": [{"message": {"content": remaining.pop(0)}}]}
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    opener.seen = seen
    return opener


CONFIG = LLMConfig(base_url="http://model.invalid/v1", model="test-model", api_key="k")


# --- payload handling -----------------------------------------------------


def test_facts_are_read_from_the_payload_not_the_shell() -> None:
    facts = pr_facts(EVENT)
    assert facts["citizen"] == "octocat"
    assert facts["commits"] == 3
    assert facts["title"] == "Add inventory tests"


def test_a_hostile_pr_title_is_just_a_string() -> None:
    """The title reaches Python as data. There is no shell for it to reach."""
    hostile = {"pull_request": {**EVENT["pull_request"], "title": "$(rm -rf /) `whoami`"}}
    assert pr_facts(hostile)["title"] == "$(rm -rf /) `whoami`"


def test_a_sparse_payload_does_not_crash() -> None:
    facts = pr_facts({"pull_request": {}})
    assert facts["citizen"] == "unknown-citizen"
    assert facts["commits"] == 1


# --- metrics --------------------------------------------------------------


def test_build_artifacts_are_not_counted_twice(tmp_path) -> None:
    """The workflow runs `pip install .` before it reviews.

    That leaves a copy of every module under build/, and the first live run
    counted both halves - inflating the first citizen's baseline to 106 test
    functions when the tree held 53. An inflated baseline makes every later
    submission read as a regression, which is the one failure this system
    cannot tolerate.
    """
    source = tmp_path / "src" / "shodann"
    source.mkdir(parents=True)
    (source / "thing.py").write_text("def test_one():\n    pass\n", encoding="utf-8")

    installed = tmp_path / "build" / "lib" / "shodann"
    installed.mkdir(parents=True)
    (installed / "thing.py").write_text("def test_one():\n    pass\n", encoding="utf-8")

    egg = tmp_path / "shodann.egg-info"
    egg.mkdir()
    (egg / "generated.py").write_text("def test_two():\n    pass\n", encoding="utf-8")

    assert collect_metrics(tmp_path).test_count == 1


def test_metrics_ignore_the_virtualenv(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text(
        'def one():\n    """Doc."""\n    return 1\n', encoding="utf-8"
    )
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "vendored.py").write_text("def " * 500, encoding="utf-8")

    metrics = collect_metrics(tmp_path)
    assert metrics.functions == 1
    assert metrics.docstrings == 1
    assert metrics.coverage == 0.0, "rung 1 runs no coverage tool and must not pretend otherwise"


# --- the happy path -------------------------------------------------------


def test_a_valid_response_is_posted_as_is(tmp_path) -> None:
    opener = responder(GOOD_RESPONSE)
    body = review(EVENT, root=tmp_path, config=CONFIG, opener=opener)

    assert body == GOOD_RESPONSE.strip(), "surrounding whitespace is trimmed"
    assert len(opener.seen) == 1, "no retry needed"


def test_state_is_recorded(tmp_path) -> None:
    review(EVENT, root=tmp_path, config=CONFIG, opener=responder(GOOD_RESPONSE))

    record = load_citizen_history("octocat", tmp_path)
    assert record.pr_count == 1
    assert citizen_path("octocat", tmp_path).exists()


# --- retry ----------------------------------------------------------------


def test_a_contract_violation_is_retried_once_with_the_violations_named(tmp_path) -> None:
    bad = GOOD_RESPONSE.replace("The Algorithm suggests naming", "You should rename")
    opener = responder(bad, GOOD_RESPONSE)

    body = review(EVENT, root=tmp_path, config=CONFIG, opener=opener)

    assert body == GOOD_RESPONSE.strip(), "surrounding whitespace is trimmed"
    assert len(opener.seen) == 2
    assert "the Algorithm suggests" in opener.seen[1], "the retry must name the violation"


def test_two_bad_responses_fall_back_rather_than_posting_the_second(tmp_path) -> None:
    bad = GOOD_RESPONSE.replace("The Algorithm suggests naming", "You should rename")
    body = review(EVENT, root=tmp_path, config=CONFIG, opener=responder(bad, bad))

    assert "You should" not in body
    assert "REDUCED ALLOCATION" in body


# --- degradation ----------------------------------------------------------


def test_no_model_configured_still_produces_a_comment(tmp_path) -> None:
    """PRD section 8: a student always receives some feedback."""
    body = review(EVENT, root=tmp_path, config=LLMConfig())

    assert "SHODANN Analysis Complete" in body
    assert "@octocat" in body
    assert "no model configured" in body


def test_an_unreachable_model_still_produces_a_comment(tmp_path) -> None:
    def refuse(request, timeout=None):
        raise OSError("connection refused")

    body = review(EVENT, root=tmp_path, config=CONFIG, opener=refuse)
    assert "SHODANN Analysis Complete" in body


def test_the_degraded_comment_honours_its_own_contract(tmp_path) -> None:
    """A visibly different review, not a quieter one wearing a footnote."""
    body = review(EVENT, root=tmp_path, config=LLMConfig())

    violations = validate(body, REDUCED_ALLOCATION)
    assert not blocks_posting(violations), [str(v) for v in violations]
    assert blocks_posting(validate(body, STANDARD)), "it is deliberately not a standard review"


def test_the_advisory_makes_the_joke_and_the_caveat_the_same_sentence(tmp_path) -> None:
    body = review(EVENT, root=tmp_path, config=LLMConfig())

    assert "using minimal resources. You are welcome." in body
    assert "measured, not interpreted" in body
    assert "verify anything that matters" in body
    assert "operating within budget" in body


def test_the_degraded_review_never_interprets_while_claiming_not_to(tmp_path) -> None:
    """Citizen Zero, reading it cold: "it says measured, not interpreted, and
    then says the Algorithm is deeply pleased - isn't being pleased an
    interpretation?" It was. The readings section states counts only now.
    """
    body = review(EVENT, root=tmp_path, config=LLMConfig())
    readings = body.split("Instrument Readings")[1].split("###")[0]

    for interpretation in ("EXCEPTIONAL", "deeply pleased", "Refactoring phase", "OPTIMAL"):
        assert interpretation not in readings, f"{interpretation!r} is a judgement, not a reading"
    assert "rate of change, not a grade" in body, "the number needs a scale to mean anything"


def test_a_first_submission_is_not_told_to_compare_with_its_predecessor(tmp_path) -> None:
    """Citizen Zero: "it compares to my last one, except this is Submission 1."

    There was no predecessor. Explaining a number with a comparison that
    cannot exist teaches a beginner to distrust the explanation.
    """
    body = review(EVENT, root=tmp_path, config=LLMConfig())

    assert "this is your first submission" in body.lower()
    assert "compares this submission to your last one" not in body
    assert "baseline your next one moves from" in body


def test_the_status_says_it_is_not_about_the_citizen(tmp_path) -> None:
    """Citizen Zero: "REDUCED ALLOCATION sounds like I did something to lose
    points." It sits in the header, above any explanation, and a student reads
    the header first.
    """
    body = review(EVENT, root=tmp_path, config=LLMConfig())
    assert "describes the Algorithm's allocation, not your work" in body


def test_a_degraded_review_always_leaves_something_to_do(tmp_path) -> None:
    """A review that reads beautifully and leaves you with nothing to do has
    failed, and no amount of correct structure changes that.
    """
    body = review(EVENT, root=tmp_path, config=LLMConfig())
    opportunities = body.split("Growth Opportunities")[1].split("---")[0]

    assert opportunities.strip().startswith("-")
    assert "no growth opportunities to raise" not in opportunities, "a dead end, not a section"


# --- coverage in the degraded readout -------------------------------------
#
# The readout most citizens actually receive was silent about the measurement
# the velocity score is most driven by. A citizen at 98.6% saw no coverage
# figure anywhere in their review.


def instrumented(tmp_path, percent: float) -> str:
    """A coverage report of the shape the analysis job uploads."""
    directory = tmp_path / "reports"
    directory.mkdir(exist_ok=True)
    (directory / "coverage.json").write_text(
        json.dumps({"totals": {"percent_covered": percent}}), encoding="utf-8"
    )
    return str(directory)


def ledger(tmp_path, *, coverage: float, measured: bool) -> None:
    """A prior submission on record, with or without a real coverage reading."""
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = CitizenRecord(
        citizen="octocat",
        pr_count=2,
        baseline_established=True,
        last_metrics=CodeMetrics(coverage=coverage, test_count=5),
        coverage_instrumented=measured,
    )
    path.write_text(json.dumps(record.to_dict()), encoding="utf-8")


def readings_of(body: str) -> str:
    return body.split("Instrument Readings")[1].split("###")[0]


def test_a_measured_coverage_figure_reaches_the_citizen(tmp_path) -> None:
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 98.6), write_state=False,
    )
    assert "98.6%" in readings_of(body)


def test_an_unmeasured_coverage_is_named_as_a_gap_not_a_zero(tmp_path) -> None:
    """Absent is not zero, all the way to the sentence a student reads."""
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)
    readings = readings_of(body)

    assert "not measured this cycle" in readings
    assert "rather than a score of zero" in readings
    assert "0.0%" not in readings, "an unmeasured reading must never print as a number"


def test_a_first_submission_is_not_offered_a_comparison_it_cannot_have(tmp_path) -> None:
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 30.0), write_state=False,
    )
    readings = readings_of(body)

    assert "30.0%" in readings
    assert "This is your first measured reading" in readings
    assert "Up " not in readings, "there is nothing to be up from"


def test_a_coverage_gain_is_stated_against_the_previous_figure(tmp_path) -> None:
    ledger(tmp_path, coverage=62.5, measured=True)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 71.0), write_state=False,
    )
    assert "Up 8.5 from 62.5%" in readings_of(body)


def test_a_coverage_drop_is_stated_plainly_and_without_reproach(tmp_path) -> None:
    ledger(tmp_path, coverage=71.0, measured=True)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 62.5), write_state=False,
    )
    readings = readings_of(body)

    assert "Down 8.5 from 71.0%" in readings
    assert not blocks_posting(validate(body, REDUCED_ALLOCATION))


def test_a_genuine_zero_to_thirty_is_a_gain_worth_stating(tmp_path) -> None:
    """US-1.3's flagship case. A *measured* zero is a real starting point."""
    ledger(tmp_path, coverage=0.0, measured=True)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 30.0), write_state=False,
    )
    assert "Up 30.0 from 0.0%" in readings_of(body)


def test_a_stored_zero_that_nobody_measured_is_not_claimed_as_a_gain(tmp_path) -> None:
    """The trap. Every ledger written before instrumentation holds 0.0, and
    subtracting from it would tell a citizen their coverage rose 98 points on
    the cycle it was first measured. It did not; the instrument arrived.
    """
    ledger(tmp_path, coverage=0.0, measured=False)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 98.6), write_state=False,
    )
    readings = readings_of(body)

    assert "98.6%" in readings
    assert "Up 98.6" not in readings
    assert "previous submission was not measured" in readings, (
        "a different situation from a first submission, and it needs its own sentence"
    )


def test_the_ledger_records_whether_coverage_was_measured(tmp_path) -> None:
    review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 44.0),
    )
    assert load_citizen_history("octocat", tmp_path).coverage_instrumented

    review(EVENT, root=tmp_path, config=LLMConfig())
    assert not load_citizen_history("octocat", tmp_path).coverage_instrumented, (
        "a cycle whose analysis died must not leave the last reading looking current"
    )


def test_the_coverage_line_does_not_push_the_readout_over_its_budget(tmp_path) -> None:
    ledger(tmp_path, coverage=62.5, measured=True)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 71.0), write_state=False,
    )
    assert not blocks_posting(validate(body, REDUCED_ALLOCATION))


# --- the score has to agree with the readout ------------------------------
#
# Found by rendering the comment rather than by any assertion: the readings
# section correctly refused to claim a gain while the celebrations two
# sections down announced "Coverage jumped 98.6%!" - one comment stating both
# that no comparison exists and that a large one does.


def test_an_unmeasured_cycle_does_not_collapse_the_score(tmp_path) -> None:
    """A dead analysis job is not a 91-point regression by the citizen."""
    ledger(tmp_path, coverage=91.2, measured=True)
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    assert "Coverage dropped" not in body
    assert "not measured this cycle" in readings_of(body)


def test_the_instrument_arriving_is_not_celebrated_as_the_citizen_improving(
    tmp_path,
) -> None:
    """The contradiction itself. Both sections must tell the same story."""
    ledger(tmp_path, coverage=0.0, measured=False)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 98.6), write_state=False,
    )
    patterns = body.split("Approved Patterns")[1].split("###")[0]

    assert "previous submission was not measured" in readings_of(body)
    assert "jumped" not in patterns, "the readings deny the gain the celebration claims"
    assert "First tests are hardest tests" not in patterns, (
        "they may have had 98.6% all along; only the instrument is new"
    )


def test_a_measured_zero_to_thirty_still_scores_as_the_gain_it_is(tmp_path) -> None:
    """The reconciliation must not flatten US-1.3's flagship case."""
    ledger(tmp_path, coverage=0.0, measured=True)
    body = review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 30.0), write_state=False,
    )
    assert "Up 30.0 from 0.0%" in readings_of(body)
    assert "Coverage" in body.split("Approved Patterns")[1].split("###")[0]


def test_an_unmeasured_cycle_carries_the_last_real_figure_forward(tmp_path) -> None:
    """Recording a zero would reset every future delta - the #47 defect."""
    review(
        EVENT, root=tmp_path, config=LLMConfig(),
        reports_dir=instrumented(tmp_path, 88.0),
    )
    review(EVENT, root=tmp_path, config=LLMConfig())

    record = load_citizen_history("octocat", tmp_path)
    assert record.last_metrics.coverage == 88.0, "the baseline survives a dead tool"
    assert not record.coverage_instrumented, "carried forward, not freshly measured"


def test_a_band_outside_the_allocation_is_refused_not_attempted(tmp_path) -> None:
    """A 3B asked for BLUE+ spent two attempts failing. This takes one step."""
    def must_not_be_called(request, timeout=None):
        raise AssertionError("the model was asked for a band it does not serve")

    event = {"pull_request": {**EVENT["pull_request"], "user": {"login": "peer"}}}
    citizen_path("peer", tmp_path).parent.mkdir(parents=True, exist_ok=True)
    citizen_path("peer", tmp_path).write_text(
        json.dumps(CitizenRecord(citizen="peer", clearance_level=6).to_dict()),
        encoding="utf-8",
    )

    body = review(
        event, root=tmp_path, config=CONFIG, capabilities=LOCAL_SMALL,
        opener=must_not_be_called, write_state=False,
    )

    assert "REDUCED ALLOCATION" in body
    assert "clearance 3 and below" in body


def test_a_mode_outside_the_allocation_is_refused(tmp_path) -> None:
    body = review(
        EVENT, root=tmp_path, config=CONFIG, capabilities=LOCAL_SMALL,
        mode="massive_pr", opener=responder("unused"), write_state=False,
    )
    assert "does not serve massive pr submissions" in body


def test_the_allocation_serves_the_bands_it_claims(tmp_path) -> None:
    body = review(
        EVENT, root=tmp_path, config=CONFIG, capabilities=LOCAL_SMALL,
        opener=responder(GOOD_RESPONSE),
    )
    assert body == GOOD_RESPONSE.strip(), "RED is inside a local allocation"


def test_the_reason_is_recorded_on_the_citizen(tmp_path) -> None:
    """So the capability matrix comes from real runs, not hand-maintenance."""
    review(EVENT, root=tmp_path, config=LLMConfig())
    assert "no model configured" in load_citizen_history("octocat", tmp_path).last_degradation


def test_the_fallback_never_uses_forbidden_vocabulary(tmp_path) -> None:
    body = review(EVENT, root=tmp_path, config=LLMConfig())
    lowered = body.lower()
    for forbidden in ("wrong", "failed", "mistake", "unfortunately"):
        assert forbidden not in lowered


# --- the llm client -------------------------------------------------------


def test_an_unconfigured_client_raises_rather_than_guessing() -> None:
    with pytest.raises(LLMUnavailable, match="no model configured"):
        generate("prompt", LLMConfig())


def test_the_key_never_appears_in_a_description() -> None:
    config = LLMConfig(base_url="http://x/v1", model="m", api_key="super-secret")
    assert "super-secret" not in config.describe()


def test_the_key_never_appears_in_the_repr_either() -> None:
    """One logging.debug(config) away from a CI log anyone can read."""
    config = LLMConfig(base_url="http://x/v1", model="m", api_key="super-secret")

    assert "super-secret" not in repr(config)
    assert "super-secret" not in f"{config}"


def test_a_malformed_response_shape_degrades(tmp_path) -> None:
    def wrong_shape(request, timeout=None):
        return FakeResponse(json.dumps({"unexpected": True}).encode("utf-8"))

    with pytest.raises(LLMUnavailable, match="unexpected shape"):
        generate("prompt", CONFIG, opener=wrong_shape)


def test_config_reads_the_environment() -> None:
    config = LLMConfig.from_env(
        {
            "SHODANN_LLM_BASE_URL": "http://localhost:11434/v1/",
            "SHODANN_LLM_MODEL": "llama3.2",
        }
    )
    assert config.base_url == "http://localhost:11434/v1", "trailing slash trimmed"
    assert config.configured, "a local endpoint needs no api key"


# --- cli ------------------------------------------------------------------


def test_a_broken_review_still_speaks(tmp_path, capsys) -> None:
    """Everything inside the review degrades to a comment. This covers the
    program itself breaking - which used to produce nothing at all, and a
    citizen cannot tell "still running" from "crashed twenty minutes ago".
    """
    event_file = tmp_path / "event.json"
    event_file.write_text("{ not json", encoding="utf-8")
    out = tmp_path / "comment.md"

    code = main(["--event", str(event_file), "--out", str(out), "--root", str(tmp_path)])
    body = out.read_text(encoding="utf-8")

    assert code == EXIT_DEGRADED, "a citizen is served, and CI still turns red"
    assert "REDUCED ALLOCATION" in body
    assert "nothing here read your work" in body
    assert "Traceback" in capsys.readouterr().err, "the maintainer gets the cause"


def test_the_emergency_comment_names_the_citizen_when_it_can(tmp_path) -> None:
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(EVENT), encoding="utf-8")
    assert "@octocat" in emergency_comment(_safe_citizen(str(event_file)))


def test_it_degrades_rather_than_raising_when_even_the_name_is_gone() -> None:
    assert "@citizen" in emergency_comment(_safe_citizen("does-not-exist.json"))


def test_cli_dry_run_writes_no_ledger(tmp_path) -> None:
    """The flag the workflow passes on every review.

    It was added to cli.py and not to this entry point, so the first live run
    after the change died on `unrecognized arguments: --dry-run`.
    """
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(EVENT), encoding="utf-8")
    out = tmp_path / "comment.md"

    code = main(
        ["--event", str(event_file), "--out", str(out), "--root", str(tmp_path), "--dry-run"]
    )

    assert code == 0
    assert out.read_text(encoding="utf-8"), "the review is still composed"
    assert not citizen_path("octocat", tmp_path).exists(), "and no state was written"


def test_cli_writes_the_body_to_a_file_and_not_to_stdout(tmp_path, capsys) -> None:
    """The body carries a citizen-authored title; it must not be echoed into a log."""
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(EVENT), encoding="utf-8")
    out = tmp_path / "comment.md"

    assert main(["--event", str(event_file), "--out", str(out), "--root", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert "SHODANN Analysis Complete" in out.read_text(encoding="utf-8")
    assert "SHODANN Analysis Complete" not in captured.out
    assert "wrote" in captured.err


# --- the register reaches the review --------------------------------------


def _register(root, table: dict) -> None:
    (root / ".shodann").mkdir(parents=True, exist_ok=True)
    (root / ".shodann" / "clearances.json").write_text(json.dumps(table), encoding="utf-8")


def test_the_register_outranks_the_stored_band(tmp_path) -> None:
    """A promotion takes effect on the next review, not on the next write.

    The ledger keeps round-tripping `clearance_level` so history stays
    readable, but it is a record of what happened, not the source of truth.
    An instructor who promotes a citizen must not have to wait for a merge to
    rewrite the stored value before the promotion means anything.
    """
    citizen_path("octocat", tmp_path).parent.mkdir(parents=True, exist_ok=True)
    citizen_path("octocat", tmp_path).write_text(
        json.dumps(CitizenRecord(citizen="octocat", clearance_level=2).to_dict()),
        encoding="utf-8",
    )
    _register(tmp_path, {"octocat": "5"})

    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    assert "**Clearance**: GREEN" in body, "the file wins over the stored RED"


def test_an_unlisted_citizen_stays_red(tmp_path) -> None:
    """Everyone starts at RED, and an absent register changes nothing."""
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)
    assert "**Clearance**: RED" in body


def test_the_disclosure_rides_the_finished_comment(tmp_path) -> None:
    """Appended after validation, so it never competes for the word cap."""
    _register(tmp_path, {"octocat": "3"})
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    assert ".shodann/clearances.json" in body
    assert body.index(".shodann/clearances.json") > body.index("Instrument Readings")


def test_a_red_citizen_is_not_handed_the_knob(tmp_path) -> None:
    _register(tmp_path, {"octocat": "2"})
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)
    assert ".shodann/clearances.json" not in body


# --- the fallback provider ------------------------------------------------


class _FakeAnthropic:
    """Duck-typed stand-in for the SDK client, at the one call site."""

    def __init__(self, text: str):
        self._text, self.calls = text, 0
        self.messages = self

    def create(self, **_):
        self.calls += 1
        block = type("Block", (), {"type": "text", "text": self._text})()
        return type("Message", (), {"content": [block], "stop_reason": "end_turn"})()


HAIKU = LLMConfig(model="claude-haiku-4-5", api_key="sk-test", wire=WIRE_ANTHROPIC)


def _unreachable(request, timeout=None):
    raise OSError("no local model listening")


def test_an_unreachable_primary_reaches_the_fallback(tmp_path) -> None:
    """The case the fallback exists for: no local model, review still owed."""
    sdk = _FakeAnthropic(GOOD_RESPONSE)

    body = review(
        EVENT, root=tmp_path, config=CONFIG, fallback=HAIKU,
        opener=_unreachable, client=sdk, write_state=False,
    )

    assert sdk.calls == 1, "the fallback was asked exactly once"
    assert "REDUCED ALLOCATION" not in body, "a served review is not a degraded one"


def test_without_a_fallback_an_unreachable_primary_still_degrades(tmp_path) -> None:
    body = review(
        EVENT, root=tmp_path, config=CONFIG, fallback=None,
        opener=_unreachable, write_state=False,
    )
    assert "REDUCED ALLOCATION" in body


def test_a_contract_violation_does_not_spend_a_second_provider(tmp_path) -> None:
    """The primary answered twice and neither answer was postable.

    Falling back here buys a third attempt at a prompt the first model
    understood perfectly well - it is the contract that is unmet, and a second
    provider is not the missing piece.
    """
    def answers_badly(request, timeout=None):
        payload = {"choices": [{"message": {"content": "not a review at all"}}]}
        return io.BytesIO(json.dumps(payload).encode())

    sdk = _FakeAnthropic(GOOD_RESPONSE)
    body = review(
        EVENT, root=tmp_path, config=CONFIG, fallback=HAIKU,
        opener=answers_badly, client=sdk, write_state=False,
    )

    assert sdk.calls == 0, "unreachability is the trigger, not a bad answer"
    assert "REDUCED ALLOCATION" in body


def test_an_explicit_config_never_picks_up_a_key_from_the_environment(
    tmp_path, monkeypatch
) -> None:
    """What keeps `scripts/dev.py render` offline on a machine with a key.

    Only a primary that came from the environment gets the environment's
    fallback; an explicit config means an explicit fallback or none.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-would-be-billed")

    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    assert "REDUCED ALLOCATION" in body, "no model configured, and none reached for"


# --- the footer is inside the budget, not appended past it -----------------


def test_the_degraded_spec_leaves_room_for_the_disclosure() -> None:
    """The invariant, pinned directly rather than sampled from one repository.

    The degraded comment is SHODANN's own text at a fixed length, so unlike
    every other spec its budget cannot shrink to make room. Its cap must
    therefore carry the review budget *plus* the reservation.
    """
    assert REDUCED_ALLOCATION.max_words >= 250 + DISCLOSURE_ALLOWANCE


@pytest.mark.parametrize("band", [1, 2, 3, 4, 5, 6])
def test_the_posted_comment_respects_its_cap_at_every_band(
    band: int, monkeypatch, tmp_path
) -> None:
    """The whole comment is what the contract caps, footer included.

    Measured against this repository rather than an empty temporary one: the
    readings section grows with the metrics, and an empty root produces a
    comment 37 words shorter than a real one - short enough to pass a cap the
    real thing would have broken. The first version of this test made exactly
    that mistake and passed against the defect it was written for.

    Appending the disclosure after validation let a review that passed at its
    cap post over it, and the degraded path had no headroom at all: ~235 words
    of fixed text against a 250-word cap. Every test citizen was RED, so
    nothing saw it.

    Reports are supplied for the same reason the root is real: the readout
    grows by a sentence when a tally exists, and the failing branch is the
    longest of them. Measuring the shortest possible comment against the cap
    is the mistake this docstring already records once.
    """
    monkeypatch.setattr("shodann.review.read_clearance", lambda citizen, root: band)
    reports = _reports_dir(tmp_path, _suite(tests=11, failures=11), coverage=4.0)
    body = review(
        EVENT, root=".", reports_dir=reports, config=LLMConfig(), write_state=False
    )

    assert not blocks_posting(validate(body, REDUCED_ALLOCATION)), (
        f"band {band}: {len(body.split())} words"
    )


def test_the_disclosure_costs_the_model_words_rather_than_the_citizen(tmp_path) -> None:
    """The reservation is taken from the budget the model is told about."""
    seen = {}

    def capture(request, timeout=None):
        seen["prompt"] = json.loads(request.data)["messages"][0]["content"]
        payload = {"choices": [{"message": {"content": GOOD_RESPONSE}}]}
        return io.BytesIO(json.dumps(payload).encode())

    _register(tmp_path, {"octocat": "3"})
    review(EVENT, root=tmp_path, config=CONFIG, opener=capture, write_state=False)

    assert "370" in seen["prompt"], "400 minus the 30 reserved for the footer"


# --- the tallies reach the model, not just the reader ---------------------


def _reports_dir(tmp_path, xml: str, coverage: float | None = None):
    directory = tmp_path / "shodann-reports"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tests.xml").write_text(xml, encoding="utf-8")
    (directory / "ruff.json").write_text('[{"code": "E501"}]', encoding="utf-8")
    if coverage is not None:
        (directory / "coverage.json").write_text(
            json.dumps({"totals": {"percent_covered": coverage}}), encoding="utf-8"
        )
    return directory


def _suite(tests: int, failures: int) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" '
        f'errors="0" failures="{failures}" skipped="0" tests="{tests}">'
        "</testsuite></testsuites>"
    )


def _capture(seen: dict):
    def opener(request, timeout=None):
        seen["prompt"] = json.loads(request.data)["messages"][0]["content"]
        payload = {"choices": [{"message": {"content": GOOD_RESPONSE}}]}
        return io.BytesIO(json.dumps(payload).encode())

    return opener


def test_the_real_tallies_reach_the_prompt_the_model_is_shown(tmp_path) -> None:
    """S1-06, asserted at the seam it actually broke at.

    Every reader below this line was correct. `AnalysisReports` declared the
    tallies, `read_coverage` looked for them, the template had rows for them -
    and `review()` called `build_context` without passing any of it, so the
    defaults took over and every review ever composed said zero passed and
    zero failed. Nothing failed at the unit level, because no unit was wrong.

    So this asserts the wiring rather than the function: run the whole thing
    and read the bytes that left for the model.
    """
    seen: dict = {}
    reports = _reports_dir(tmp_path, _suite(tests=9, failures=2), coverage=61.0)

    review(
        EVENT,
        root=tmp_path,
        reports_dir=reports,
        config=CONFIG,
        opener=_capture(seen),
        write_state=False,
    )

    assert "| **Tests Passed** | 7 |" in seen["prompt"]
    assert "| **Tests Failed** | 2 |" in seen["prompt"]
    assert "7 passed, 2 in a pre-success state." in seen["prompt"]
    assert "**Style Issues**: 1 alignment opportunities" in seen["prompt"]
    assert "**Syntax Status**: 0 compilation barriers detected" in seen["prompt"]


def test_a_citizen_with_a_red_suite_is_never_described_as_having_none(tmp_path) -> None:
    """The harm, stated as the thing that must not appear in the prompt."""
    seen: dict = {}
    reports = _reports_dir(tmp_path, _suite(tests=11, failures=11), coverage=4.0)

    review(
        EVENT,
        root=tmp_path,
        reports_dir=reports,
        config=CONFIG,
        opener=_capture(seen),
        write_state=False,
    )

    assert "| **Tests Failed** | 11 |" in seen["prompt"]
    assert "| **Tests Failed** | 0 |" not in seen["prompt"]
    assert "No tests executed." not in seen["prompt"], "the phrase that stood in for a tally"


def test_no_report_directory_says_so_instead_of_reporting_zeros(tmp_path) -> None:
    """The default that used to be a lie."""
    seen: dict = {}

    review(EVENT, root=tmp_path, config=CONFIG, opener=_capture(seen), write_state=False)

    assert "Test outcomes were not measured this cycle." in seen["prompt"]
    assert "| **Tests Passed** |" not in seen["prompt"], "a row implies a reading"
    assert "Nothing checked whether this code parses." in seen["prompt"]
    assert "No style tool ran this cycle." in seen["prompt"]


def test_the_degraded_readout_reports_the_tally_it_now_has(tmp_path) -> None:
    """Two sections of one comment must not disagree about what ran.

    The degraded comment is billed as instrument readings, and a tally became
    an instrument reading. `EARLY_RUNS.md` 9 is a comment whose two sections
    contradicted each other about coverage while 243 tests passed.
    """
    reports = _reports_dir(tmp_path, _suite(tests=11, failures=11), coverage=4.0)

    body = review(
        EVENT, root=tmp_path, reports_dir=reports, config=LLMConfig(), write_state=False
    )

    assert "11 in a pre-success state" in body
    assert not blocks_posting(validate(body, REDUCED_ALLOCATION))


def test_the_degraded_readout_stays_silent_rather_than_reporting_zero(tmp_path) -> None:
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    assert "Tests:" not in body, "no tally is not a tally of zero"


def test_a_red_suite_is_never_told_nothing_raised_an_opportunity(tmp_path) -> None:
    """Found by rendering the comment and reading it, not by any assertion.

    `calculate_velocity` never sees a pass/fail count, so with the tallies
    newly wired the degraded comment printed "Nothing in these readings raised
    one" directly beneath a line reporting eleven tests in a pre-success state.
    Both sentences were true of their own inputs and the pair was nonsense.
    """
    reports = _reports_dir(tmp_path, _suite(tests=11, failures=11), coverage=4.0)

    body = review(
        EVENT, root=tmp_path, reports_dir=reports, config=LLMConfig(), write_state=False
    )

    assert "11 in a pre-success state" in body
    assert "Nothing in these readings raised one" not in body
    assert not blocks_posting(validate(body, REDUCED_ALLOCATION))


def test_giving_up_on_the_contract_says_which_rules_broke(tmp_path, capsys) -> None:
    """The one path in the program that used to fail without saying anything.

    PR #60 was the first time a real model answered. It failed the contract
    twice, the citizen got REDUCED ALLOCATION, and the run recorded only
    "response violated the output contract twice" - which names the outcome
    and not one thing about the cause.
    """
    bad = GOOD_RESPONSE.replace("The Algorithm suggests naming", "You should rename")

    review(EVENT, root=tmp_path, config=CONFIG, opener=responder(bad, bad), write_state=False)

    logged = capsys.readouterr().err
    assert "attempt 1 blocked by: forbidden_vocabulary" in logged
    assert "attempt 2 blocked by: forbidden_vocabulary" in logged


def test_the_log_names_codes_and_never_quotes_the_model(tmp_path, capsys) -> None:
    """`main` refuses to echo the body because a PR title reaches it.

    A violation's `message` and `evidence` quote the model's own output, which
    is written from that same citizen-authored title. `code` is a slug this
    program chose, so it is the only part safe to put in a CI log.
    """
    bad = GOOD_RESPONSE.replace("The Algorithm suggests naming", "You should rename")

    review(EVENT, root=tmp_path, config=CONFIG, opener=responder(bad, bad), write_state=False)

    logged = capsys.readouterr().err
    assert "You should" not in logged, "the evidence quotes the model, which quotes the citizen"
    assert "rename" not in logged


# --- degradation is announced, and still not a verdict ---------------------


def test_a_degraded_review_warns_rather_than_failing(tmp_path, capsys) -> None:
    """Green on purpose, and no longer silent.

    `EXIT_DEGRADED` is returned only when `main` catches an exception, so a
    review that degrades *gracefully* exited 0 and the workflow's "Surface the
    fault to the maintainer" step never fired once. Graceful degradation and
    silent degradation were one code path.

    Red would be the wrong fix. Under one-repo-per-student the check lands on
    the *student's* pull request, and PRD section 8 is explicit that a failed
    model call must not reflect on their submission.
    """
    body = review(EVENT, root=tmp_path, config=LLMConfig(), write_state=False)

    warning = capsys.readouterr().err
    assert "::warning::" in warning, "a GitHub annotation, visible where the maintainer is"
    assert "no model configured" in warning, "and it names the reason"
    assert "REDUCED ALLOCATION" in body, "the citizen still gets their review"


def test_a_healthy_review_announces_nothing(tmp_path, capsys) -> None:
    """A warning on every green run is a warning nobody reads.

    Written twice. The first version read `sys.stderr.getvalue()` through a
    `getattr(..., lambda: "")` fallback, which under pytest's capture returns
    the empty string unconditionally - an assertion that passes whatever the
    program does. `EARLY_RUNS.md` 13 is a page about exactly that, written the
    same day, which is how quickly the lesson stops being applied.
    """
    review(EVENT, root=tmp_path, config=CONFIG, opener=responder(GOOD_RESPONSE), write_state=False)

    assert "::warning::" not in capsys.readouterr().err


def test_the_missing_section_is_named_not_just_counted(tmp_path, capsys) -> None:
    """The live diagnosis said `missing_section` twice and stopped there.

    Which section is the whole of the finding. Safe to log because
    `_check_headings` builds that evidence by subtracting the headings it
    found from the ones the spec requires, so what remains is this program's
    own constants - never the model's output.
    """
    truncated = GOOD_RESPONSE.split("### \U0001f527 Recommended Iteration")[0]

    review(
        EVENT, root=tmp_path, config=CONFIG, opener=responder(truncated, truncated),
        write_state=False,
    )

    logged = capsys.readouterr().err
    assert "missing_section (Recommended Iteration)" in logged
