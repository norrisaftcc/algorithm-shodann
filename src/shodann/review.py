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
from pathlib import Path

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

__all__ = ["collect_metrics", "facts_only_comment", "main", "pr_facts", "review"]

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


def collect_metrics(root: Path | str = ".") -> CodeMetrics:
    """Count what can be counted without running anything.

    Rung 1 deliberately runs no analysis tools. Reading source is cheap, needs
    no toolchain, and cannot execute a student's code - which matters more
    than the extra signal a test run would add. Coverage stays zero until the
    hard-analysis job exists, so velocity here is carried by test growth,
    documentation and iteration count.
    """
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
        coverage=0.0,
        test_count=tests,
        complexity=functions,
        loc=loc,
        functions=functions,
        docstrings=docstrings,
    )


def facts_only_comment(
    facts: dict, result: VelocityResult, record: CitizenRecord, reason: str
) -> str:
    """The comment a citizen gets when no model could be reached.

    PRD section 8 commits to graceful degradation: a student always receives
    *some* feedback. This is that floor, and it honours the same output
    contract as a generated response - it is quieter, not lesser.
    """
    celebrations = "\n".join(f"- {line}" for line in result.celebrations[:3])
    opportunities = "\n".join(f"- {line}" for line in result.opportunities) or (
        "- The Algorithm has no growth opportunities to raise this iteration."
    )
    next_step = (
        "Keep the iteration cadence. The Algorithm will have more to say once "
        "the analysis tools are online."
    )

    return f"""## \U0001f916 SHODANN Analysis Complete

**Citizen**: @{facts["citizen"]} | **Clearance**: {clearance_name(record.clearance_level)} | \
**Velocity**: {result.score}

---

### \U0001f680 Shipping Velocity Report

{result.assessment}. Submission {record.pr_count} across {result.iterations} \
commit(s), touching {facts["files_changed"]} file(s).

### ✅ Algorithm-Approved Patterns

{celebrations}

### \U0001f4c8 Growth Opportunities

{opportunities}

### \U0001f527 Recommended Iteration

{next_step}

---

*The Algorithm sees your growth. The Algorithm is pleased.*

<sub>Generated without model synthesis ({reason}).</sub>
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
    config: LLMConfig | None = None,
    mode: str = "standard",
    opener=None,
    write_state: bool = True,
) -> str:
    """Produce the comment body for one pull request."""
    facts = pr_facts(event)
    config = config or LLMConfig.from_env()

    record = load_citizen_history(facts["citizen"], root)
    metrics = collect_metrics(root)
    result = calculate_velocity(metrics, record.last_metrics, facts["commits"])

    if write_state:
        record = save_citizen_history(facts["citizen"], metrics, result, root)
    else:
        record.pr_count += 1

    spec = _spec_for(record, mode)

    try:
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
            # Rung 1 runs no coverage tool, so the reading is absent rather
            # than zero. Saying so is the difference between a model reporting
            # a gap and a model celebrating one.
            coverage_instrumented=False,
        )
        # Note the asymmetry: `root` is the citizen's repository, but the
        # prompt library is SHODANN's own and is read relative to the working
        # directory. Rung 1 reviews this repository, so they coincide. They
        # will not once SHODANN reviews someone else's repo, and at that point
        # the templates need to ship as package data.
        prompt = render_prompt(context)
        return _synthesise(prompt, spec, config, opener=opener)
    except LLMUnavailable as unavailable:
        return facts_only_comment(facts, result, record, str(unavailable))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shodann-review")
    parser.add_argument("--event", required=True, help="path to the GitHub event payload")
    parser.add_argument("--out", required=True, help="where to write the comment body")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", default="standard", choices=sorted(SPECS))
    args = parser.parse_args(argv)

    with Path(args.event).open(encoding="utf-8") as handle:
        event = json.load(handle)

    body = review(event, root=args.root, mode=args.mode)
    Path(args.out).write_text(body, encoding="utf-8")

    # Never echo the body: it contains citizen-authored text via the PR title.
    sys.stderr.write(f"SHODANN wrote {len(body.split())} words to {args.out}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
