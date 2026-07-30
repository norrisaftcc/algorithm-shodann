"""Assemble the prompt sent to the model.

The files in ``prompts/`` are documents *about* prompts: the prompt itself sits
inside a fenced block, and the same file carries a variable-reference table
that mentions every placeholder as documentation. Rendering a whole file would
happily substitute the documentation too, so the renderable region is delimited
explicitly:

    <!-- TEMPLATE:BEGIN -->
    ...the actual prompt...
    <!-- TEMPLATE:END -->

Templates use ``{{ UPPER_SNAKE }}`` with inner spaces, which is already valid
Jinja, so variable substitution needed no rewriting. What did need handling:

* **Missing variables must be loud.** ``StrictUndefined`` turns a forgotten
  binding into an exception at render time rather than a literal ``{{ FOO }}``
  arriving in a student's feedback.
* **Bracketed emoji names.** The templates write ``[ROCKET EMOJI]`` where the
  output contract requires an actual emoji. Left alone, the model copies the
  bracket text into the comment.
* **Author annotations.** HTML comments inside the template are notes to
  whoever maintains it, not instructions for the model. They are stripped.
* **Pseudo-control-flow.** Templates 02, 04 and 05 contain ``{{ IF X }}`` and
  ``{{ FOR EACH x IN y }}``, which are not Jinja and raise a syntax error that
  says nothing useful. Those are detected up front and reported by file and
  line, with the conversion that would fix them.
"""

from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from .analysis import AnalysisReports
from .clearance import clearance_instructions, iteration_guidance
from .state import CitizenRecord, clearance_name
from .validator import STANDARD, ResponseSpec, for_clearance
from .velocity import CodeMetrics, VelocityResult

__all__ = [
    "BASE_TEMPLATE",
    "PROMPTS_DIR",
    "UnsupportedTemplateSyntax",
    "build_context",
    "describe_history",
    "describe_style_rules",
    "extract_template",
    "find_pseudo_syntax",
    "render_prompt",
    "render_template_text",
]

PROMPTS_DIR = Path("prompts")
BASE_TEMPLATE = "01_base_shodann_prompt.md"

TEMPLATE_BEGIN = "<!-- TEMPLATE:BEGIN -->"
TEMPLATE_END = "<!-- TEMPLATE:END -->"

EMOJI = {
    # Standard response contract
    "ROBOT EMOJI": "\U0001f916",
    "ROCKET EMOJI": "\U0001f680",
    "CHECK EMOJI": "✅",
    "CHART EMOJI": "\U0001f4c8",
    "WRENCH EMOJI": "\U0001f527",
    "LOCK EMOJI": "\U0001f512",
    "UPWARD CHART EMOJI": "\U0001f4c8",
    "DOWNWARD CHART EMOJI": "\U0001f4c9",
    # RAGE STATE (prompts/02)
    "SIREN EMOJI": "\U0001f6a8",
    "WARNING EMOJI": "⚠️",
    "SHIELD EMOJI": "\U0001f6e1️",
    "EYES EMOJI": "\U0001f440",
    "DICE EMOJI": "\U0001f3b2",
    "TARGET EMOJI": "\U0001f3af",
    "CLIPBOARD EMOJI": "\U0001f4cb",
    # First submission (prompts/04)
    "SPARKLE EMOJI": "✨",
    "STAR EMOJI": "⭐",
    "COMPASS EMOJI": "\U0001f9ed",
    "TEST TUBE EMOJI": "\U0001f9ea",
    "X EMOJI": "❌",
    # Edge case handlers (prompts/05)
    "HOURGLASS EMOJI": "⏳",
    "QUESTION EMOJI": "❓",
    "WHALE EMOJI": "\U0001f433",
    "LIGHTBULB EMOJI": "\U0001f4a1",
    "CONSTRUCTION EMOJI": "\U0001f6a7",
    "MAGNIFYING GLASS EMOJI": "\U0001f50d",
    "DOCUMENT EMOJI": "\U0001f4c4",
    "INFO EMOJI": "ℹ️",
}
"""Bracketed names the templates use where the output contract wants an emoji.

An unmapped name passes through untouched and lands in a student's section
heading as literal bracket text. `test_prompts.py` asserts every bracketed name
across the whole library has an entry here, including templates that are not
rendered yet - the failure only appears the day one of them is wired up, which
is exactly when nobody is looking for it.
"""

_EMOJI_PATTERN = re.compile(r"\[([A-Z ]+EMOJI)\]")
_HTML_COMMENT = re.compile(r"[ \t]*<!--.*?-->[ \t]*\n?", re.DOTALL)

# {{ IF x }}, {{ ELSE }}, {{ ENDIF }}, {{ END IF }}, {{ FOR EACH x IN y }},
# {{ END FOR }}, {{ EXAMPLE }}, {{ EXAMPLES }}, {{ END EXAMPLES }} - none of it
# is Jinja. The plural matters: `EXAMPLE\b` does not match `{{ EXAMPLES }}`,
# and an undetected authoring placeholder is worse than an undetected keyword -
# it parses as a perfectly valid variable lookup and only fails at render time,
# looking like an ordinary missing binding rather than syntax that was never
# meant to be data.
_PSEUDO_SYNTAX = re.compile(r"\{\{\s*(IF|ELSE|ENDIF|END\s+\w+|FOR\s+EACH|EXAMPLES?)\b[^}]*\}\}")


class UnsupportedTemplateSyntax(ValueError):
    """A template carries control flow the renderer cannot interpret."""


def find_pseudo_syntax(text: str) -> list[tuple[int, str]]:
    """Locate ad-hoc control flow, as ``(line number, matched text)`` pairs."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        found.extend((number, match.group(0)) for match in _PSEUDO_SYNTAX.finditer(line))
    return found


def extract_template(path: Path | str) -> str:
    """Pull the renderable region out of a prompt document.

    Raises if the markers are missing rather than guessing, because guessing
    would silently send a variable-reference table to the model.
    """
    text = Path(path).read_text(encoding="utf-8")

    if TEMPLATE_BEGIN not in text or TEMPLATE_END not in text:
        raise UnsupportedTemplateSyntax(
            f"{path}: no {TEMPLATE_BEGIN} / {TEMPLATE_END} markers. "
            "Wrap the prompt body in them so the renderer knows what is template "
            "and what is documentation."
        )

    body = text.split(TEMPLATE_BEGIN, 1)[1].split(TEMPLATE_END, 1)[0]

    # The markers sit outside the fence that makes the prompt readable on
    # GitHub; the fence itself is not part of the prompt.
    lines = body.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip() + "\n"


def _resolve_emoji(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return EMOJI.get(match.group(1), match.group(0))

    return _EMOJI_PATTERN.sub(replace, text)


def render_template_text(
    template_text: str,
    context: dict,
    *,
    source: str = "<string>",
    strip_comments: bool = True,
) -> str:
    """Render already-extracted template text.

    Split out from :func:`render_prompt` so prompt assembly can be unit tested
    without touching the filesystem.
    """
    pseudo = find_pseudo_syntax(template_text)
    if pseudo:
        detail = ", ".join(f"line {number}: {text}" for number, text in pseudo[:5])
        raise UnsupportedTemplateSyntax(
            f"{source}: contains control flow the renderer cannot interpret ({detail}). "
            "Convert it to Jinja - {{ IF X }} becomes {% if X %}, "
            "{{ FOR EACH x IN y }} becomes {% for x in y %} - or render a template "
            "that does not use it."
        )

    environment = Environment(
        undefined=StrictUndefined,
        autoescape=False,  # noqa: S701 - markdown for an LLM, never HTML for a browser
        keep_trailing_newline=True,
    )
    rendered = environment.from_string(template_text).render(**context)

    if strip_comments:
        rendered = _HTML_COMMENT.sub("", rendered)
    return _resolve_emoji(rendered)


def build_context(
    result: VelocityResult,
    record: CitizenRecord,
    *,
    pr_title: str,
    files_changed: int,
    lines_added: int,
    lines_removed: int,
    current_week: str = "",
    reports: AnalysisReports | None = None,
    spec: ResponseSpec | None = None,
    security_section: str = "",
    rage_section: str = "",
    mode_statement: str = "NORMAL (Growth Celebration)",
) -> dict:
    """Map domain objects onto the template's variables.

    Every placeholder in the base template gets a value here - a missing one
    would raise at render time, which is the point, but it should never get
    that far in production.

    An absent reading sends the literal words ``not instrumented`` in place of
    every figure it would have produced. A zero handed to a model is a
    measurement, and it will be read as one: both a 3B and an 8B model, given
    `0.0` and told to celebrate deltas, congratulated a citizen on "a coverage
    delta of 0.0% to 0.0%". That is the prompt's defect, not the model's, and
    no larger model fixes it.

    **One `reports` object, not six numbers.** This function used to take
    `tests_passed`, `tests_failed`, `style_issue_count` and three report
    strings as separate parameters, each defaulting to a zero or to "No tests
    executed." `review()` passed none of them, so every review ever composed
    told the model that zero tests passed, zero failed and nothing was checked
    for syntax - while the velocity score beside it read the real coverage and
    the real lint count off an object already in scope at the call site.

    The parameters are gone rather than filled in. Six arguments a caller must
    remember is a defect waiting to recur; one object cannot be half-passed.
    And the default is now *honest*: no reports means nothing was measured,
    which is what the template will say, instead of a confident row of zeros.
    """
    reports = reports or AnalysisReports()
    previous = record.last_metrics or CodeMetrics.baseline()
    current = result.deltas

    # The format rules the prompt states are derived from the spec the
    # validator enforces. Anything else is two sources of truth pretending to
    # be one: the template used to instruct "Recommended Iteration" while the
    # validator demanded "Observations" at BLUE+, so every review at that band
    # was rejected, retried, rejected and dropped to the fallback.
    spec = spec or for_clearance(STANDARD, record.clearance_level)
    iteration_heading = spec.headings[-1] if spec.headings else "Recommended Iteration"
    iteration_limit = (
        "Provide exactly 1 recommended next iteration"
        if iteration_heading == "Recommended Iteration"
        else f"Provide at most 1 item under {iteration_heading}, or omit the section"
    )

    # When coverage is absent the rows are dropped entirely rather than filled
    # with a phrase. Filling them was tried: an 8B model dutifully narrated
    # "improving their test coverage from not instrumented to not
    # instrumented", because a table row with a Previous and a Current column
    # implies a progression whatever you put in it. A row that is not there
    # cannot be narrated.
    previous_coverage = f"{round(previous.coverage, 1)}%"
    current_coverage = f"{round(previous.coverage + current.coverage, 1)}%"
    coverage_delta = f"{round(current.coverage, 1):+}%"

    return {
        "MODE_STATEMENT": mode_statement,
        "CITIZEN_USERNAME": record.citizen,
        "CLEARANCE_NAME": clearance_name(record.clearance_level),
        "CLEARANCE_NUMBER": record.clearance_level,
        "CURRENT_WEEK": current_week,
        # Arrives *post*-increment: `review()` does `record.pr_count += 1` before
        # calling here, so this is the number of the submission being reviewed,
        # not a count of the ones before it. `PREV_STREAK` on the next line is
        # the opposite - stored, un-incremented, genuinely prior.
        #
        # Harmless until S1-23 made the two counters count the same events, at
        # which point the prompt was handing the model two aliases one apart and
        # template 01 labelled the post-increment one "Previous Submissions".
        # SHODANN reviewed PR #61 and reported both faithfully: "your 20th
        # submission" and "This is your 19th consecutive submission recorded",
        # in one paragraph. The model was right twice and the comment still
        # contradicted itself, which is a labelling defect and not a model one.
        # Renaming the row rather than changing either value: 20 really is the
        # submission number, 19 really is the prior streak, and both are true
        # once each says which it is.
        "PR_COUNT": record.pr_count,
        "COVERAGE_INSTRUMENTED": reports.coverage_instrumented,
        "PREV_COVERAGE": previous_coverage,
        # Retained as a context key with no template consumer, deliberately.
        # No template renders it any more (S1-42: it is `PR_COUNT - 1` for
        # every ledger this system writes, and three reviews reported both
        # numbers as two facts). Kept so `build_context`'s output stays a
        # superset of what any template might ask for, rather than removed
        # and re-derived by whoever next wants a streak - the value is
        # correct, it is only unfit to hand a model beside `PR_COUNT`.
        "PREV_STREAK": record.iteration_streak,
        "PR_TITLE": pr_title,
        "FILES_CHANGED": files_changed,
        "LINES_ADDED": lines_added,
        "LINES_REMOVED": lines_removed,
        "ITERATION_COUNT": result.iterations,
        "HISTORY_NARRATIVE": describe_history(record, result),
        "SYNTAX_REPORT": _syntax_report(reports),
        "SYNTAX_MEASURED": reports.syntax_errors is not None,
        "SYNTAX_ERRORS": reports.syntax_errors,
        "STYLE_RULES": describe_style_rules(reports),
        "STYLE_REPORT": _style_report(reports),
        "STYLE_MEASURED": reports.lint_issues is not None,
        "STYLE_ISSUE_COUNT": reports.lint_issues,
        "TEST_REPORT": _test_report(reports),
        "TESTS_INSTRUMENTED": reports.tests_instrumented,
        "TESTS_PASSED": reports.tests_passed,
        "TESTS_FAILED": reports.tests_failed,
        "CURRENT_COVERAGE": current_coverage,
        "PREV_COMPLEXITY": previous.complexity,
        "CURRENT_COMPLEXITY": previous.complexity + current.complexity,
        "COMPLEXITY_DELTA": current.complexity,
        "COVERAGE_DELTA": coverage_delta,
        "VELOCITY_SCORE": result.score,
        "VELOCITY_ASSESSMENT": result.assessment,
        "SECURITY_SECTION": security_section,
        "CLEARANCE_INSTRUCTIONS": clearance_instructions(record.clearance_level),
        "RAGE_SECTION_IF_ACTIVE": rage_section,
        "ITERATION_HEADING": iteration_heading,
        # design_docs/CLEARANCE_REGISTER.md specifies a magnifier for the
        # peer-register section; a wrench is for someone being handed a task.
        "ITERATION_MARK": (
            "[MAGNIFYING GLASS EMOJI]"
            if iteration_heading == "Observations"
            else "[WRENCH EMOJI]"
        ),
        "ITERATION_GUIDANCE": iteration_guidance(spec, record.clearance_level),
        "ITERATION_LIMIT": iteration_limit,
        "WORD_CAP": spec.max_words,
        "MAX_OPPORTUNITIES": spec.max_opportunities,
    }


_NOT_MEASURED = "Not measured this cycle."
"""What every report says when its tool did not run.

One phrase for all three, because the failure it replaces was three different
sentences - "No tests executed.", "No syntax analysis performed.", "No style
analysis performed." - each of which reads as a *finding* about the code rather
than a gap in the instruments. "No tests executed" describes a citizen who
wrote none. It was printed to a model beside a table claiming a measured zero,
on every review, for a repository with 245 passing tests.
"""


def _test_report(reports: AnalysisReports) -> str:
    if not reports.tests_instrumented:
        return _NOT_MEASURED
    if reports.tests_failed:
        return f"{reports.tests_passed} passed, {reports.tests_failed} in a pre-success state."
    return f"{reports.tests_passed} passed, none in a pre-success state."


def _style_report(reports: AnalysisReports) -> str:
    if reports.lint_issues is None:
        return _NOT_MEASURED
    if reports.complexity:
        return (
            f"{reports.lint_issues} style diagnostics, "
            f"{reports.complexity} of them functions above the branch threshold."
        )
    return f"{reports.lint_issues} style diagnostics."


def _syntax_report(reports: AnalysisReports) -> str:
    if reports.syntax_errors is None:
        return _NOT_MEASURED
    if reports.syntax_errors:
        return f"{reports.syntax_errors} files could not be parsed."
    return "Every file parsed."


def describe_style_rules(reports: AnalysisReports) -> str:
    """The rules behind the style count, or a refusal to characterise it.

    S1-45. The count alone made the model guess what was in it - categories, then
    a fixable count, then a command that shows the citizen nothing. Naming the
    rules is what makes the number reproducible: a citizen handed `RUF100` can
    look it up or select it, where a citizen handed "23" and their own clean
    `ruff check` has nothing to act on.

    The absent case is a refusal rather than an empty list, for the same reason
    every other reading here has one. "No breakdown available" invites the model
    to supply one.
    """
    if reports.style_breakdown is None:
        return (
            "The rules behind this count were not recorded. Do not name, guess or "
            "illustrate a rule or category, and do not say which kind of issue these are."
        )
    if not reports.style_breakdown:
        return "No diagnostics, so no rules to report."

    rules = ", ".join(f"`{code}` x{count}" for code, count in reports.style_breakdown)
    # Qualitative, never a count. `style_fixable` is a real reading and it is
    # deliberately not rendered: it sits two lines from the total, the two are
    # within one of each other, and a model handed two adjacent figures for
    # related quantities welds them - which is exactly what happened, and is
    # EARLY_RUNS 18's class with different numbers in it.
    fixable = (
        " Most of these are mechanical rather than judgement calls."
        if reports.style_fixable
        else ""
    )
    return (
        f"Most frequent rules: {rules}.{fixable} Name only these rules; there may "
        "be others in the count and you have not been shown them. **State no "
        "second count.** There is one number here, the total above; how many are "
        "auto-fixable is not yours to state and no arithmetic on the total is "
        "either.\n\n"
        "**No command clears this reading.** It is taken with the citizen's own "
        "lint configuration ignored, so their `ruff check` selects different "
        "rules and their `--fix` resolves a different set. Name a rule so they "
        "can look it up; never name a command and say it will clear, fix or "
        "resolve these diagnostics, and never estimate how long that would take."
    )


def describe_history(record: CitizenRecord, result: VelocityResult) -> str:
    """One or two sentences of context for the model. Facts only, no framing.

    No streak figure, and it took three commits to get here. `iteration_streak`
    equals `pr_count` for every ledger this system writes (S1-42), so handing
    both over gives the model two numbers for one quantity one apart - and it
    reliably reports both. The DATA-table row lost its number, then lost the
    subtraction that replaced it, and the contradiction survived anyway because
    the *same figure* was still arriving here. One answer in two places, which is
    the failure this file's own comments keep naming.

    The trend stays: `velocity_trend` is a genuinely separate reading, computed by
    `compute_trend` over the newest three history entries, and nothing else in
    the prompt carries it.
    """
    if result.is_first_submission or record.pr_count <= 1:
        return (
            "This is the citizen's first submission. No previous metrics exist, "
            "so every delta is measured against a zero baseline."
        )
    return (
        f"Submission number {record.pr_count}. "
        f"Velocity trend: {record.velocity_trend.upper()}."
    )


def render_prompt(
    context: dict,
    *,
    template: str = BASE_TEMPLATE,
    prompts_dir: Path | str = PROMPTS_DIR,
    strip_comments: bool = True,
) -> str:
    """Render one prompt document against ``context``.

    Rung 1 renders the base template only. Mode selection, clearance
    calibration, RAGE STATE and the edge-case handlers each replace or extend
    this and are not wired up yet.
    """
    path = Path(prompts_dir) / template
    return render_template_text(
        extract_template(path),
        context,
        source=str(path),
        strip_comments=strip_comments,
    )
