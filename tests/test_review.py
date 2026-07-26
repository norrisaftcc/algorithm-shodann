"""One review, end to end - especially the paths that run when things go wrong."""

from __future__ import annotations

import io
import json

import pytest

from shodann.capability import LOCAL_SMALL
from shodann.llm import LLMConfig, LLMUnavailable, generate
from shodann.review import collect_metrics, main, pr_facts, review
from shodann.state import CitizenRecord, citizen_path, load_citizen_history
from shodann.validator import REDUCED_ALLOCATION, STANDARD, blocks_posting, validate

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
