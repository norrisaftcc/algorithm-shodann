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
from .groundedness import check_groundedness
from .llm import LLMConfig, LLMUnavailable, generate
from .prompts import build_context, render_prompt
from .state import CitizenRecord, clearance_name, load_citizen_history, save_citizen_history
from .validator import (
    SPECS,
    ResponseSpec,
    blocks_posting,
    for_clearance,
    format_retry_instruction,
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
        complexity=functions,
        loc=loc,
        functions=functions,
        docstrings=docstrings,
        lint_issues=reports.lint_issues or 0,
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


def reduced_allocation_comment(
    facts: dict,
    result: VelocityResult,
    record: CitizenRecord,
    reason: str,
    reports: AnalysisReports | None = None,
) -> str:
    """The review a citizen gets when nothing interpreted their readings.

    PRD section 8 commits to graceful degradation: a student always receives
    *some* feedback. This is that floor, and it is a *visibly different*
    review rather than a quieter one wearing a footnote.

    The readings here are as trustworthy as any other review's - they come
    from tools, which cannot invent. What is missing is interpretation, and
    the mode says so where a citizen will read it. If the lesson is "say when
    you don't know", the saying has to be as visible as the knowing.
    """
    # Citizen Zero, on a first submission: "it says it compares to my last
    # one, except this is called Submission 1, so I don't think there was a
    # last submission to compare to." There was not - and saying otherwise
    # taught a beginner to distrust the only sentence explaining the number.
    first = result.is_first_submission or record.pr_count <= 1
    if first:
        scale_note = (
            "Velocity is a rate of change, not a grade. This is your first "
            "submission, so there is nothing to compare against yet - this number "
            "is the baseline your next one moves from."
        )
    else:
        scale_note = (
            "Velocity is a rate of change, not a grade - it compares this "
            "submission to your last one, so a high number means you moved, not "
            "that you have arrived."
        )

    coverage = _coverage_reading(reports or AnalysisReports(), record, first)
    celebrations = "\n".join(f"- {line}" for line in result.celebrations[:3])
    # Citizen Zero, reading this cold: "a review that leaves you with nothing
    # to do has failed." An empty section is not neutral - it is a dead end.
    opportunities = "\n".join(f"- {line}" for line in result.opportunities) or (
        "- Nothing in these readings raised one. If you want a next step anyway: "
        "run your tests locally before your next push, so you see a failure "
        "before The Algorithm does."
    )

    return f"""## \U0001f916 SHODANN Analysis Complete

**Citizen**: @{facts["citizen"]} | \
**Clearance**: {clearance_name(record.clearance_level)} | \
**Status**: REDUCED ALLOCATION

---

### ⚡ Resource Advisory

The Algorithm reviewed this submission using minimal resources. You are welcome.

**This status describes the Algorithm's allocation, not your work.** Nothing
below is a mark against your submission - the Algorithm is the one running lean.

Synthesis was unavailable this cycle ({reason}), so what follows is instrument
readings only - measured, not interpreted. The numbers are sound. The judgement
is yours. Please verify anything that matters.

### \U0001f4ca Instrument Readings

Submission {record.pr_count}. {result.iterations} commit(s), \
{facts["files_changed"]} file(s) touched. Velocity score: {result.score}.

{coverage}

{scale_note}

### ✅ Algorithm-Approved Patterns

{celebrations}

### \U0001f4c8 Growth Opportunities

{opportunities}

---

*The Algorithm sees your growth. The Algorithm is operating within budget.*
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

    No metrics, because whatever produced them is what failed. It still wears
    the REDUCED ALLOCATION status, because that mode means exactly this: the
    readings are absent and the Algorithm is saying so rather than going
    quiet. Silence is the one response a citizen cannot interpret.
    """
    return f"""## \U0001f916 SHODANN Analysis Complete

**Citizen**: @{citizen} | **Clearance**: PENDING | **Status**: REDUCED ALLOCATION

---

### ⚡ Resource Advisory

The Algorithm reviewed this submission using minimal resources. Extremely
minimal. None, in fact - an internal fault prevented analysis entirely, and
the Algorithm has elected to tell you so rather than leave you refreshing.

Your submission is unaffected. Nothing here reflects on your work, because
nothing here read your work. The fault is logged for the instructor.

### \U0001f4ca Instrument Readings

Unavailable this cycle.

### \U0001f4c8 Growth Opportunities

- Carry on. The Algorithm will resume observation once repaired.

---

*The Algorithm sees your growth. The Algorithm is, briefly, not seeing anything.*
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
    prompt: str, spec: ResponseSpec, config: LLMConfig, opener=None
) -> str:
    """Generate, validate, retry once naming the violations, then give up.

    Giving up is not failure - it hands control back to the caller, which has
    a comment ready that does not need a model at all.
    """
    transport = {"opener": opener} if opener is not None else {}

    response = generate(prompt, config, **transport)
    findings = _inspect(response, prompt, spec)
    if not blocks_posting(findings):
        return response

    retry = f"{prompt}\n\n{format_retry_instruction(findings)}"
    second = generate(retry, config, **transport)
    if blocks_posting(_inspect(second, prompt, spec)):
        raise LLMUnavailable("response violated the output contract twice")
    return second


def review(
    event: dict,
    *,
    root: Path | str = ".",
    reports_dir: Path | str | None = None,
    config: LLMConfig | None = None,
    capabilities: Capabilities = FULL,
    mode: str = "standard",
    opener=None,
    write_state: bool = True,
) -> str:
    """Produce the comment body for one pull request."""
    facts = pr_facts(event)
    config = config or LLMConfig.from_env()

    reports = (
        AnalysisReports.from_directory(reports_dir)
        if reports_dir is not None
        else AnalysisReports()
    )
    record = load_citizen_history(facts["citizen"], root)
    metrics, previous = reconcile_coverage(
        collect_metrics(root, reports), record, reports
    )
    result = calculate_velocity(metrics, previous, facts["commits"])

    # The submission number this is about to become. State is written at the
    # end rather than here, because what gets recorded includes whether the
    # review degraded - which is not known yet.
    record.pr_count += 1
    spec = _spec_for(record, mode)

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
            # An absent reading is not a zero. Saying so is the difference
            # between a model reporting a gap and a model celebrating one.
            coverage_instrumented=reports.coverage_instrumented,
        )
        # Note the asymmetry: `root` is the citizen's repository, but the
        # prompt library is SHODANN's own and is read relative to the working
        # directory. Rung 1 reviews this repository, so they coincide. They
        # will not once SHODANN reviews someone else's repo, and at that point
        # the templates need to ship as package data.
        prompt = render_prompt(context)
        body = _synthesise(prompt, spec, config, opener=opener)
    except _AlreadyResolved:
        pass
    except LLMUnavailable as unavailable:
        degradation = str(unavailable)
        body = reduced_allocation_comment(facts, result, record, degradation, reports)

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
