"""One review, end to end: facts in, a comment body out.

This is rung 1 - the walking skeleton. It runs as a single job rather than the
five-job pipeline the design describes, because five jobs on separate runners
need every tool report to cross a job boundary through ``$GITHUB_OUTPUT``, and
any flake8 or pytest output containing a bare ``EOF`` line breaks the
delimiter. One job sidesteps that entirely until there is a reason not to.

**Nothing here reads a PR title or body into a shell.** Untrusted text arrives
as a parsed JSON event payload and leaves as a file written by Python. The
workflow never interpolates it into a ``run:`` block, which is the defect the
draft workflow in ``design_docs/shodann-core.yml`` carries at line 131.

The degraded path is the interesting one. If no model is configured, or the
model is unreachable, or its output cannot be made to satisfy the contract in
one retry, a student still receives a comment - assembled from the tool facts
alone, in SHODANN's voice, and validated like any other.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import replace
from pathlib import Path

from .analysis import AnalysisReports
from .capability import FULL, Capabilities, refusal_reason
from .clearance import DISCLOSURE_ALLOWANCE, clearance_disclosure
from .groundedness import check_groundedness
from .llm import LLMConfig, LLMUnavailable, fallback_from_env, generate
from .prompts import build_context, render_prompt
from .state import (
    CitizenRecord,
    clearance_name,
    load_citizen_history,
    read_clearance,
    save_citizen_history,
)
from .validator import (
    BLOCKING,
    SPECS,
    ResponseSpec,
    blocks_posting,
    for_clearance,
    format_retry_instruction,
    unwrap_fenced_response,
    validate,
)
from .velocity import CodeMetrics, VelocityResult, calculate_velocity

__all__ = [
    "EXIT_DEGRADED",
    "collect_metrics",
    "emergency_comment",
    "main",
    "pr_facts",
    "reconcile_coverage",
    "reduced_allocation_comment",
    "review",
]

EXIT_DEGRADED = 3
"""The review was written but something broke producing it.

Distinct from 0 so CI can post the comment and still turn red: a citizen
is served either way, and a maintainer is not told everything is fine.
"""

EXCLUDED_DIRS = frozenset(
    {
        ".venv",
        "venv",
        ".git",
        "node_modules",
        "site-packages",
        # `pip install .` leaves a copy of every module under build/, and the
        # workflow installs before it reviews. Counting both halves doubled
        # the first citizen's baseline on the very first live run - and an
        # inflated baseline makes every later submission look like a
        # regression, which is the one failure this system cannot tolerate.
        "build",
        "dist",
    }
)


def pr_facts(event: dict) -> dict:
    """Pull the submission facts out of a GitHub pull_request event payload."""
    pull = event.get("pull_request") or {}
    user = pull.get("user") or {}
    return {
        "citizen": user.get("login") or "unknown-citizen",
        "number": pull.get("number") or 0,
        "title": pull.get("title") or "(untitled)",
        "files_changed": pull.get("changed_files") or 0,
        "lines_added": pull.get("additions") or 0,
        "lines_removed": pull.get("deletions") or 0,
        "commits": pull.get("commits") or 1,
    }


def collect_metrics(
    root: Path | str = ".", reports: AnalysisReports | None = None
) -> CodeMetrics:
    """Count what can be counted, and fold in whatever was measured elsewhere.

    Reading source is cheap, needs no toolchain, and cannot execute a
    citizen's code. Coverage and lint counts can only come from *running*
    things, which happens in a separate unprivileged job - see
    `shodann.analysis`. This function never runs anything.

    Without reports, coverage stays 0.0 and is reported as *not instrumented*
    rather than as a measured zero.
    """
    reports = reports or AnalysisReports()
    loc = tests = functions = docstrings = 0
    for path in sorted(Path(root).rglob("*.py")):
        if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        loc += len(body.splitlines())
        tests += body.count("def test_")
        functions += body.count("def ")
        docstrings += body.count('"""') // 2

    return CodeMetrics(
        coverage=reports.coverage or 0.0,
        test_count=tests,
        # C901 violations, from the report - not the `def ` count this field
        # used to hold. The two were the same number for every reading ever
        # taken, which is why `pyproject.toml` could claim the ruff pin
        # protected a complexity baseline that nothing computed.
        #
        # A measured 0 here is a real and good answer: no function exceeds the
        # branch threshold. An absent report also reads 0, exactly as
        # `lint_issues` beside it does - tolerable only because nothing keyed
        # on this can fabricate a claim from a zero. The score no longer reads
        # it, and `_complexity_note` fires on a positive delta, so silence is
        # what an unmeasured cycle produces.
        complexity=reports.complexity or 0,
        loc=loc,
        functions=functions,
        docstrings=docstrings,
        lint_issues=reports.lint_issues or 0,
        # Declared since the port and never once assigned, so every ledger ever
        # written recorded `syntax_errors: 0` for a repository nothing had
        # checked. Same `or 0` as the two fields above, and tolerable for the
        # same reason: no score term reads it, and the prompt takes its
        # syntax figure from `reports`, where absent is still absent.
        syntax_errors=reports.syntax_errors or 0,
    )


def reconcile_coverage(
    metrics: CodeMetrics, record: CitizenRecord, reports: AnalysisReports
) -> tuple[CodeMetrics, CodeMetrics | None]:
    """Hold coverage still unless both sides of the comparison were measured.

    A delta is a claim about the past. ``collect_metrics`` has to hand the
    engine a float, so an absent reading arrives as 0.0 - and the engine, which
    cannot tell that zero from a real one, then reports a 98-point gain to a
    citizen whose coverage did not move (the instrument arrived) or a 91-point
    collapse to one whose analysis job merely died. Both are punitive branches
    caused by infrastructure, which the behavioural contract forbids.

    So when either side is unmeasured, both sides are set to whichever figure
    is real. The delta is zero, the celebrations stay quiet, and the score
    stops swinging on whether a tool ran. A *measured* zero is untouched: 0 to
    30 is US-1.3's flagship case and must keep scoring as the gain it is.

    Returned rather than mutated, because the current metrics are also what
    gets written to the ledger - and a cycle with no reading should carry the
    last real figure forward rather than recording a zero that resets every
    future delta.
    """
    previous = record.last_metrics
    if reports.coverage_instrumented and (previous is None or record.coverage_instrumented):
        return metrics, previous
    if previous is None:
        # No history and no reading: the baseline is already zero on both
        # sides, so nothing can be inferred and nothing needs holding.
        return replace(metrics, coverage=0.0), previous

    anchor = metrics.coverage if reports.coverage_instrumented else previous.coverage
    return replace(metrics, coverage=anchor), replace(previous, coverage=anchor)


def _coverage_reading(reports: AnalysisReports, record: CitizenRecord, first: bool) -> str:
    """One sentence of coverage, or one sentence saying there is none.

    Coverage is the heaviest term in the velocity score and the one number a
    citizen is most likely to be chasing. Leaving it out of the degraded
    readout meant the review most citizens actually receive was silent about
    the measurement it was most driven by.

    A delta is only claimed when the previous figure was itself measured. A
    stored zero from a cycle that never ran coverage is not a reading, and
    subtracting from it would announce a gain the citizen did not make - the
    same class of error as telling a first submission it compares to its
    predecessor.
    """
    if not reports.coverage_instrumented:
        return (
            "Coverage: not measured this cycle. The coverage tool reported nothing, "
            "which is a gap in the readings rather than a score of zero."
        )

    current = f"Coverage: {reports.coverage}% of lines run by your tests."
    previous = record.last_metrics.coverage if record.last_metrics else None
    if first or previous is None:
        # A genuine first submission. US-1.3 treats this as a gain from zero
        # and the celebrations say so, so the readout must not undercut them
        # by implying the number means nothing yet.
        return f"{current} This is your first measured reading."
    if not record.coverage_instrumented:
        # Not the same situation, and it needs its own sentence: there *is* a
        # previous submission, it simply was never measured. Claiming a gain
        # against it would credit the citizen for the instrument arriving.
        return (
            f"{current} Your previous submission was not measured, "
            "so this one starts the comparison."
        )

    delta = round(reports.coverage - previous, 1)
    if delta > 0:
        return f"{current} \U0001f4c8 Up {delta} from {previous}%."
    if delta < 0:
        return f"{current} \U0001f4c9 Down {abs(delta)} from {previous}%."
    return f"{current} Unchanged from {previous}%."


def _test_reading(reports: AnalysisReports) -> str:
    """One sentence of outcomes, or none at all.

    The degraded comment is the review most citizens actually receive, and it
    is billed as instrument readings. A tally is now an instrument reading, so
    leaving it out would put this section a measurement behind the prompt -
    and two sections of one comment disagreeing about what ran is the exact
    defect `EARLY_RUNS.md` 9 records.

    Silent when unmeasured, rather than saying so. Coverage earns its "not
    measured this cycle" sentence because a citizen chases the number and will
    wonder where it went; nobody is chasing a tally, and spending words to
    announce the absence of something never promised is the mode padding
    itself. No claim is still the point - the citizen is told nothing rather
    than told a zero.
    """
    if not reports.tests_instrumented:
        return ""
    if reports.tests_failed:
        return (
            f"Tests: {reports.tests_passed} passed, {reports.tests_failed} "
            "in a pre-success state - each one is a specific, findable next step."
        )
    return f"Tests: {reports.tests_passed} passed, none in a pre-success state."


def reduced_allocation_comment(
    facts: dict,
    result: VelocityResult,
    record: CitizenRecord,
    reason: str,
    reports: AnalysisReports | None = None,
) -> str:
    """The readings, and almost nothing else.

    PRD section 8 commits to graceful degradation: a student always receives
    *some* feedback. This is that floor, and it is a *visibly different*
    review rather than a quieter one wearing a footnote.

    **Short on purpose, and much shorter than it was.** This used to run four
    headed sections and ~235 words to say "no model answered, here are the
    numbers" - long enough to read as a review, which is the one thing it is
    not. Its own length was the lie: a citizen skimming it could not tell it
    apart from a review that had been thought about. Length is how a reader
    judges effort, so a mode that spent 235 words announcing that no effort was
    made was arguing with itself.

    Two things survive the cut, and both were paid for:

    * **The disclaimer**, compressed to one clause. Without it the status reads
      as a verdict on the submission rather than on the Algorithm.
    * **One next step.** Citizen Zero, reading the old comment cold: "a review
      that leaves you with nothing to do has failed." An empty ending is not
      neutral, it is a dead end - and that is truer, not less true, in a
      comment this short.

    Gone: the velocity score, the rate-of-change explanation, and the
    celebration list. A number nobody interpreted invites interpretation, and
    the explanation existed only to defuse the number. Celebrations are the
    part that most needs a reader; `calculate_velocity` writes them from
    deltas alone, and three cheerful bullets under a banner saying nothing was
    analysed is the tonal mismatch this mode exists to avoid.
    """
    reports = reports or AnalysisReports()
    first = result.is_first_submission or record.pr_count <= 1
    lines = [
        line
        for line in (_coverage_reading(reports, record, first), _test_reading(reports))
        if line
    ]
    # The score stays, in four words instead of thirty. Citizen Zero read a
    # bare velocity number as a grade, and the old comment spent a 30-word
    # paragraph explaining that it is a rate. The explanation was right and
    # the length was the mode's whole problem, so the protection is kept and
    # the paragraph is not.
    facts_line = (
        f"Submission {record.pr_count} - {result.iterations} commit(s), "
        f"{facts['files_changed']} file(s). Velocity {result.score} (a rate, not a grade)."
    )
    readings_block = "\n\n".join([facts_line, *lines])

    # The tally gets first refusal. `calculate_velocity` never sees a pass/fail
    # count, so once the tallies were wired this line printed "Nothing in these
    # readings raised one" directly beneath a line reporting eleven tests in a
    # pre-success state - two parts of one comment disagreeing about the same
    # submission, which is `EARLY_RUNS.md` 9 exactly. Caught by rendering it
    # and reading it, as that entry was.
    if reports.tests_failed:
        next_step = (
            "**Next:** take the first test in a pre-success state and make it pass. "
            "One is a smaller job than eleven."
        )
    elif result.opportunities:
        next_step = f"**Next:** {result.opportunities[0]}"
    else:
        next_step = (
            "**Next:** run your tests locally before your next push, so you see a "
            "pre-success state before The Algorithm does."
        )

    return f"""## \U0001f916 SHODANN Analysis Complete

**Citizen**: @{facts["citizen"]} | \
**Clearance**: {clearance_name(record.clearance_level)} | \
**Status**: MINIMAL RESPONSE

Readings only, not interpreted ({reason}) - the Algorithm is running lean, \
which is a fact about the Algorithm and not about your work.

{readings_block}

{next_step}
"""


class _AlreadyResolved(Exception):
    """The review was settled before a model was needed."""


def _safe_citizen(event_path: str) -> str:
    """The citizen's name, if the payload can still be read. Never raises."""
    try:
        with Path(event_path).open(encoding="utf-8") as handle:
            return pr_facts(json.load(handle))["citizen"]
    except Exception:  # noqa: BLE001 - this runs *because* something already broke
        return "citizen"


def emergency_comment(citizen: str) -> str:
    """What a citizen gets when the review itself could not be assembled.

    No metrics, because whatever produced them is what failed. It wears the
    same MINIMAL RESPONSE status, because that mode means exactly this: the
    readings are absent and the Algorithm is saying so rather than going
    quiet. Silence is the one response a citizen cannot interpret.

    Shortened alongside the mode it shares a status with, and for a sharper
    version of the same reason. This ran four headed sections to report that
    *nothing had been read at all* - the further a comment is from having
    anything to say, the less it may spend saying it.
    """
    return f"""## \U0001f916 SHODANN Analysis Complete

**Citizen**: @{citizen} | **Clearance**: PENDING | **Status**: MINIMAL RESPONSE

An internal fault stopped the analysis before it read anything, so there are \
no readings this cycle. Nothing here reflects on your work, because nothing \
here saw your work. The fault is logged for the instructor.

**Next:** carry on. The Algorithm will resume observation once repaired.
"""


def _spec_for(record: CitizenRecord, mode: str) -> ResponseSpec:
    return for_clearance(SPECS[mode], record.clearance_level)


def _inspect(response: str, prompt: str, spec: ResponseSpec) -> list:
    """Contract violations and groundedness findings, together.

    The two checks are deliberately separate modules and deliberately applied
    together: one knows the shape a response must take, the other knows what
    the model was actually shown. A response can satisfy either alone and
    still be unfit to post.
    """
    return validate(response, spec) + check_groundedness(response, prompt)


def _synthesise(
    prompt: str, spec: ResponseSpec, config: LLMConfig, opener=None, client=None
) -> str:
    """Generate, validate, retry once naming the violations, then give up.

    Giving up is not failure - it hands control back to the caller, which has
    a comment ready that does not need a model at all.
    """
    transport = {}
    if opener is not None:
        transport["opener"] = opener
    if client is not None:
        transport["client"] = client

    response = unwrap_fenced_response(generate(prompt, config, **transport))
    findings = _inspect(response, prompt, spec)
    if not blocks_posting(findings):
        return response

    retry = f"{prompt}\n\n{format_retry_instruction(findings)}"
    second = unwrap_fenced_response(generate(retry, config, **transport))
    final = _inspect(second, prompt, spec)
    if blocks_posting(final):
        _log_violations(findings, final)
        raise _ContractViolation("response violated the output contract twice")
    return second


def _log_violations(first: list, second: list) -> None:
    """Say which rules were broken, on the one path that used to say nothing.

    `_synthesise` computed these findings twice, spent them on the retry
    instruction, and dropped both sets. So the first time a real model
    answered - PR #60, `claude-haiku-4-5` - the degraded comment said
    "response violated the output contract twice" and the run held no record
    of *which* contract, which is the one fact needed to do anything about it.

    Codes, plus the evidence of the few codes whose evidence this program
    wrote itself. `Violation.message` and `.evidence` generally quote the
    model's output, which is written from a citizen-authored PR title, so the
    rule that keeps `main` from echoing the body applies to them for the same
    reason - see `_SPEC_DERIVED` for the exception and why it is safe.
    """
    for label, findings in (("attempt 1", first), ("attempt 2", second)):
        blocking = [finding for finding in findings if finding.severity == BLOCKING]
        detail = sorted(
            {
                f"{finding.code} ({finding.evidence})"
                if finding.code in _SPEC_DERIVED and finding.evidence
                else finding.code
                for finding in blocking
            }
        )
        sys.stderr.write(f"SHODANN {label} blocked by: {', '.join(detail) or 'nothing'}\n")


_SPEC_DERIVED = frozenset({"missing_section"})
"""Codes whose `evidence` came from the spec, not from the response.

`_check_headings` builds a `missing_section`'s evidence by subtracting the
headings it *found* from the headings the `ResponseSpec` *requires*, so what
survives is a list of this program's own constants - the names it never saw.
It cannot carry model output, and it is the one detail worth having: the first
live diagnosis read `missing_section` twice and could not say which section,
which is half a finding.

Nothing else belongs here without the same argument made explicitly.
`section_order` looks similar and is not: its message reports the order it
*found*, which is the model's.
"""


def _announce_degradation(reason: str | None) -> None:
    """A warning annotation, and the job stays green.

    Takes the falsy case rather than making the caller branch on it. `review`
    tripped our own `C901` at 11 branches when this was an `if` at the call
    site - the first time the complexity gate wired up two commits ago has
    fired on this project's own code, which is a better argument for the
    metric than anything in the PRD.

    Every degraded review before this one exited 0, so the workflow's
    "Surface the fault to the maintainer" step - gated on the compose step's
    outcome - had never fired, and `EXIT_DEGRADED`'s own docstring promised a
    red run that only a *crash* could produce. Graceful degradation and silent
    degradation were the same code path.

    Green on purpose, rather than fixed by returning `EXIT_DEGRADED`. Under
    one-repo-per-student the check appears on the *student's* pull request,
    and a failed model call is precisely what PRD section 8 says must not
    reflect on their submission - a red X for our outage teaches the wrong
    thing more effectively than the comment teaches the right one. A warning
    is visible in the run and in the Actions tab, where the maintainer is,
    and invisible as a verdict, where the student is.

    The reason is one of this program's own strings, never the model's output
    and never the citizen's - see `_log_violations`.
    """
    if not reason:
        return
    sys.stderr.write(f"::warning::SHODANN degraded - {reason}. A comment was still posted.\n")


class _ContractViolation(LLMUnavailable):
    """The model answered, twice, and neither answer was postable.

    A subclass so the fallback can tell it apart from a model it could not
    reach. Falling back here would buy a third attempt at a prompt the first
    model understood perfectly well - it is the *contract* that is not being
    met, and a second provider is not the missing piece. Reaching for one
    would spend a second bill to reach the same comment.
    """


def _synthesise_chain(
    prompt: str,
    spec: ResponseSpec,
    config: LLMConfig,
    fallback: LLMConfig | None,
    opener=None,
    client=None,
) -> str:
    """The configured model, then the fallback if it produced nothing usable.

    The trigger is every `LLMUnavailable` except `_ContractViolation` - which
    is broader than "unreachable", and deliberately so. `generate` raises the
    same exception for a connection failure, unparseable JSON, an unexpected
    response shape, a refusal, and an empty body; a provider that answers with
    garbage is no more available than one that does not answer, and a second
    one is worth trying in all of those cases.

    The one exclusion is the case where a second provider cannot help: the
    primary returned a well-formed response, twice, and both failed *our*
    contract rather than its own. See `_ContractViolation`.
    """
    try:
        return _synthesise(prompt, spec, config, opener=opener, client=client)
    except _ContractViolation:
        raise
    except LLMUnavailable:
        if fallback is None or not fallback.configured:
            raise
    return _synthesise(prompt, spec, fallback, opener=opener, client=client)


def review(
    event: dict,
    *,
    root: Path | str = ".",
    reports_dir: Path | str | None = None,
    config: LLMConfig | None = None,
    fallback: LLMConfig | None = None,
    capabilities: Capabilities = FULL,
    mode: str = "standard",
    opener=None,
    client=None,
    write_state: bool = True,
) -> str:
    """Produce the comment body for one pull request."""
    facts = pr_facts(event)
    if config is None:
        config = LLMConfig.from_env()
        # Only reach for the environment's fallback when the primary came
        # from there too. An explicit config means an explicit fallback or
        # none - which is what keeps `scripts/render_review.py` offline even
        # on a machine with a key exported.
        if fallback is None:
            fallback = fallback_from_env()

    reports = (
        AnalysisReports.from_directory(reports_dir)
        if reports_dir is not None
        else AnalysisReports()
    )
    record = load_citizen_history(facts["citizen"], root)
    # The file wins over the ledger. The ledger keeps round-tripping the band
    # so history stays readable, but the instructor's file is the source: a
    # promotion has to take effect on the next review, not whenever the stored
    # value happens to be rewritten.
    band = read_clearance(facts["citizen"], root)
    if band is not None:
        record.clearance_level = band
    metrics, previous = reconcile_coverage(
        collect_metrics(root, reports), record, reports
    )
    result = calculate_velocity(metrics, previous, facts["commits"])

    # The submission number this is about to become. State is written at the
    # end rather than here, because what gets recorded includes whether the
    # review degraded - which is not known yet.
    record.pr_count += 1
    spec = _spec_for(record, mode)

    # Reserve the footer's words before the model is told its budget, so the
    # posted comment - review plus footer - stays inside the cap the contract
    # states. Appending after validation would let a review that passed at 400
    # words post at 447, which is the cap applied to the wrong thing.
    disclosure = clearance_disclosure(record.clearance_level)
    if disclosure:
        spec = spec.with_(max_words=spec.max_words - DISCLOSURE_ALLOWANCE)

    # Refuse outside the envelope rather than attempting and discovering. A 3B
    # model asked for the BLUE+ peer register spent two attempts failing; this
    # reaches the same outcome in one step, with a reason worth recording.
    degradation: str | None = refusal_reason(
        capabilities, band=record.clearance_level, mode=mode
    )
    body = ""
    if degradation:
        # Refused before a prompt is even assembled: no tokens, no latency,
        # and a reason a citizen can read.
        body = reduced_allocation_comment(facts, result, record, degradation, reports)

    try:
        if degradation:
            raise _AlreadyResolved
        context = build_context(
            result,
            record,
            pr_title=facts["title"],
            files_changed=facts["files_changed"],
            lines_added=facts["lines_added"],
            lines_removed=facts["lines_removed"],
            # The same spec the response will be judged against, so the
            # instructions and the checks cannot disagree.
            spec=spec,
            # The whole object, not the one attribute this line used to read.
            # Every reading it carries is a fact the model is about to speak
            # about; an absent one is not a zero, and saying so is the
            # difference between a model reporting a gap and a model
            # celebrating one.
            reports=reports,
        )
        # Note the asymmetry: `root` is the citizen's repository, but the
        # prompt library is SHODANN's own and is read relative to the working
        # directory. Rung 1 reviews this repository, so they coincide. They
        # will not once SHODANN reviews someone else's repo, and at that point
        # the templates need to ship as package data.
        prompt = render_prompt(context)
        body = _synthesise_chain(prompt, spec, config, fallback, opener=opener, client=client)
    except _AlreadyResolved:
        pass
    except LLMUnavailable as unavailable:
        degradation = str(unavailable)
        body = reduced_allocation_comment(facts, result, record, degradation, reports)

    body += disclosure

    _announce_degradation(degradation)

    if write_state:
        save_citizen_history(
            facts["citizen"],
            metrics,
            result,
            root,
            degradation=degradation,
            coverage_instrumented=reports.coverage_instrumented,
        )
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shodann-review")
    parser.add_argument("--event", required=True, help="path to the GitHub event payload")
    parser.add_argument("--out", required=True, help="where to write the comment body")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--reports",
        help="directory holding coverage.json and ruff.json from the analysis job",
    )
    parser.add_argument("--mode", default="standard", choices=sorted(SPECS))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="compose the review without writing the citizen ledger",
    )
    args = parser.parse_args(argv)

    try:
        with Path(args.event).open(encoding="utf-8") as handle:
            event = json.load(handle)
        body = review(
            event,
            root=args.root,
            reports_dir=args.reports,
            mode=args.mode,
            write_state=not args.dry_run,
        )
        exit_code = 0
    except Exception:  # noqa: BLE001 - the last thing between a defect and silence
        # Everything inside the review degrades to a comment. A defect in the
        # program itself used to produce nothing at all, and a citizen cannot
        # tell "still running" from "crashed twenty minutes ago". They get the
        # notice; the maintainer gets the traceback and a red run.
        traceback.print_exc()
        body = emergency_comment(_safe_citizen(args.event))
        exit_code = EXIT_DEGRADED

    Path(args.out).write_text(body, encoding="utf-8")

    # Never echo the body: it contains citizen-authored text via the PR title.
    sys.stderr.write(f"SHODANN wrote {len(body.split())} words to {args.out}\n")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
