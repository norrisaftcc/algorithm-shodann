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

from .state import CitizenRecord, clearance_name
from .velocity import CodeMetrics, VelocityResult

__all__ = [
    "BASE_TEMPLATE",
    "PROMPTS_DIR",
    "UnsupportedTemplateSyntax",
    "build_context",
    "describe_history",
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
    "ROBOT EMOJI": "\U0001f916",
    "ROCKET EMOJI": "\U0001f680",
    "CHECK EMOJI": "✅",
    "CHART EMOJI": "\U0001f4c8",
    "WRENCH EMOJI": "\U0001f527",
    "LOCK EMOJI": "\U0001f512",
    "UPWARD CHART EMOJI": "\U0001f4c8",
    "DOWNWARD CHART EMOJI": "\U0001f4c9",
}

_EMOJI_PATTERN = re.compile(r"\[([A-Z ]+EMOJI)\]")
_HTML_COMMENT = re.compile(r"[ \t]*<!--.*?-->[ \t]*\n?", re.DOTALL)

# {{ IF x }}, {{ ELSE }}, {{ ENDIF }}, {{ END IF }}, {{ FOR EACH x IN y }},
# {{ END FOR }}, {{ EXAMPLE }}, {{ END EXAMPLES }} - none of it is Jinja.
_PSEUDO_SYNTAX = re.compile(r"\{\{\s*(IF|ELSE|ENDIF|END\s+\w+|FOR\s+EACH|EXAMPLE)\b[^}]*\}\}")


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
    syntax_report: str = "No syntax analysis performed.",
    style_report: str = "No style analysis performed.",
    test_report: str = "No tests executed.",
    tests_passed: int = 0,
    tests_failed: int = 0,
    style_issue_count: int = 0,
    clearance_instructions: str = "",
    security_section: str = "",
    rage_section: str = "",
    mode_statement: str = "NORMAL (Growth Celebration)",
) -> dict:
    """Map domain objects onto the template's variables.

    Every placeholder in the base template gets a value here - a missing one
    would raise at render time, which is the point, but it should never get
    that far in production.
    """
    previous = record.last_metrics or CodeMetrics.baseline()
    current = result.deltas

    return {
        "MODE_STATEMENT": mode_statement,
        "CITIZEN_USERNAME": record.citizen,
        "CLEARANCE_NAME": clearance_name(record.clearance_level),
        "CLEARANCE_NUMBER": record.clearance_level,
        "CURRENT_WEEK": current_week,
        "PR_COUNT": record.pr_count,
        "PREV_COVERAGE": round(previous.coverage, 1),
        "PREV_STREAK": record.iteration_streak,
        "PR_TITLE": pr_title,
        "FILES_CHANGED": files_changed,
        "LINES_ADDED": lines_added,
        "LINES_REMOVED": lines_removed,
        "ITERATION_COUNT": result.iterations,
        "HISTORY_NARRATIVE": describe_history(record, result),
        "SYNTAX_REPORT": syntax_report,
        "SYNTAX_ERRORS": 0,
        "STYLE_REPORT": style_report,
        "STYLE_ISSUE_COUNT": style_issue_count,
        "TEST_REPORT": test_report,
        "TESTS_PASSED": tests_passed,
        "TESTS_FAILED": tests_failed,
        "CURRENT_COVERAGE": round(previous.coverage + current.coverage, 1),
        "PREV_COMPLEXITY": previous.complexity,
        "CURRENT_COMPLEXITY": previous.complexity + current.complexity,
        "COMPLEXITY_DELTA": current.complexity,
        "COVERAGE_DELTA": round(current.coverage, 1),
        "VELOCITY_SCORE": result.score,
        "VELOCITY_ASSESSMENT": result.assessment,
        "SECURITY_SECTION": security_section,
        "CLEARANCE_INSTRUCTIONS": clearance_instructions,
        "RAGE_SECTION_IF_ACTIVE": rage_section,
    }


def describe_history(record: CitizenRecord, result: VelocityResult) -> str:
    """One or two sentences of context for the model. Facts only, no framing."""
    if result.is_first_submission or record.pr_count <= 1:
        return (
            "This is the citizen's first submission. No previous metrics exist, "
            "so every delta is measured against a zero baseline."
        )
    return (
        f"Submission number {record.pr_count}. Velocity trend: "
        f"{record.velocity_trend.upper()}. Iteration streak: {record.iteration_streak}."
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
