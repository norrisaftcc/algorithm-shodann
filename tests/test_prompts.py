"""Prompt assembly: extraction, strict binding, and the syntax we cannot render."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from jinja2 import Environment, StrictUndefined, meta
from jinja2.exceptions import UndefinedError

from shodann.prompts import (
    BASE_TEMPLATE,
    EMOJI,
    UnsupportedTemplateSyntax,
    build_context,
    extract_template,
    find_pseudo_syntax,
    render_prompt,
    render_template_text,
)
from shodann.state import CitizenRecord
from shodann.velocity import CodeMetrics, calculate_velocity

PROMPTS = Path(__file__).parent.parent / "prompts"


def sample_context() -> dict:
    record = CitizenRecord(citizen="octocat", clearance_level=3, pr_count=4, iteration_streak=2)
    record.last_metrics = CodeMetrics(coverage=45.0, test_count=6, complexity=11)
    result = calculate_velocity(
        CodeMetrics(coverage=52.0, test_count=9, complexity=14),
        record.last_metrics,
        3,
    )
    return build_context(
        result,
        record,
        pr_title="Add inventory tests",
        files_changed=4,
        lines_added=120,
        lines_removed=18,
        current_week="6",
    )


# --- extraction -----------------------------------------------------------


def test_extraction_excludes_the_documentation() -> None:
    """The file's own variable table mentions every placeholder as prose."""
    body = extract_template(PROMPTS / BASE_TEMPLATE)

    assert "LAYER 0: SHODANN IDENTITY" in body
    assert "Variable Injection Reference" not in body
    assert "Implementation Notes" not in body
    assert "`github.event.pull_request.user.login`" not in body


def test_extraction_drops_the_outer_fence_but_keeps_inner_ones() -> None:
    """Inner fences delimit tool reports and are part of the prompt."""
    body = extract_template(PROMPTS / BASE_TEMPLATE)

    assert not body.lstrip().startswith("```")
    assert "```\n{{ SYNTAX_REPORT }}\n```" in body


def test_missing_markers_is_an_error_not_a_guess(tmp_path) -> None:
    unmarked = tmp_path / "unmarked.md"
    unmarked.write_text("# Docs\n\nSome prose with {{ CITIZEN_USERNAME }}.\n", encoding="utf-8")

    with pytest.raises(UnsupportedTemplateSyntax, match="TEMPLATE:BEGIN"):
        extract_template(unmarked)


# --- rendering ------------------------------------------------------------


def test_base_template_renders_with_nothing_left_unresolved() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "{{" not in rendered
    assert "}}" not in rendered
    assert "[ROBOT EMOJI]" not in rendered
    assert "EMOJI]" not in rendered


def test_build_context_supplies_every_variable_the_template_declares() -> None:
    """Enumerate the template's variables rather than trusting a hand-written list."""
    source = extract_template(PROMPTS / BASE_TEMPLATE)
    # noqa: S701 - parse-only, and markdown for an LLM is never HTML for a browser
    environment = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701
    declared = meta.find_undeclared_variables(environment.parse(source))

    missing = declared - set(sample_context())
    assert not missing, f"build_context does not supply: {sorted(missing)}"


def test_bracketed_emoji_names_become_emoji() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "\U0001f916" in rendered, "robot, for the analysis header"
    assert "\U0001f680" in rendered, "rocket, for the velocity report"
    assert "\U0001f512" in rendered, "lock, for security observations"


def test_author_annotations_do_not_reach_the_model() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "<!--" not in rendered
    assert "Injected as:" not in rendered


def test_annotations_can_be_kept_for_inspection() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS, strip_comments=False)
    assert "<!--" in rendered


def test_a_forgotten_variable_raises_instead_of_leaking(tmp_path) -> None:
    """A literal {{ FOO }} in a student's feedback is the failure this prevents."""
    with pytest.raises(UndefinedError):
        render_template_text("Citizen: {{ CITIZEN_USERNAME }} at {{ NOT_PROVIDED }}", {
            "CITIZEN_USERNAME": "octocat"
        })


def test_rendered_prompt_carries_the_facts_it_was_given() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "@octocat" in rendered
    assert "ORANGE" in rendered
    assert "Add inventory tests" in rendered
    assert "52.0%" in rendered
    assert "+7.0%" in rendered, "the delta carries its own sign and unit"


def test_uninstrumented_coverage_says_so_rather_than_reporting_zero() -> None:
    """A zero handed to a model is a measurement, and it will be read as one.

    Given `0.0` and told to celebrate deltas, both a 3B and an 8B model
    congratulated a citizen on "a coverage delta of 0.0% to 0.0%". That is the
    prompt's defect, not the model's, and no larger model fixes it.
    """
    record = CitizenRecord(citizen="octocat", clearance_level=2, pr_count=2)
    result = calculate_velocity(CodeMetrics(test_count=9), None, 2)
    context = build_context(
        result,
        record,
        pr_title="Wire the analysis job",
        files_changed=2,
        lines_added=40,
        lines_removed=3,
        coverage_instrumented=False,
    )
    rendered = render_prompt(context, prompts_dir=PROMPTS)
    coverage_rows = [line for line in rendered.splitlines() if "**Coverage**" in line]

    assert not coverage_rows, "a row with Previous and Current columns implies a progression"
    assert "Coverage was not measured this cycle." in rendered
    assert "Do not report, infer, or celebrate" in rendered

    # The complexity row must survive the branch it shares a table with.
    assert "**Complexity**" in rendered

    # The prime directive's "0% to 30%" is illustrative prose, not a reading,
    # and must survive untouched.
    assert "0% to 30% test" in rendered


def test_instrumented_coverage_still_reports_normally() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "**Coverage**" in rendered
    assert "Coverage was not measured" not in rendered


# --- the syntax we cannot render -----------------------------------------


def test_pseudo_control_flow_is_found_with_line_numbers() -> None:
    found = find_pseudo_syntax("a\n{{ IF X }}\nb\n{{ ENDIF }}\n")
    assert [number for number, _ in found] == [2, 4]


@pytest.mark.parametrize("token", ["{{ EXAMPLE }}", "{{ EXAMPLES }}", "{{ END EXAMPLES }}"])
def test_authoring_placeholders_are_detected_including_the_plural(token: str) -> None:
    """`{{ EXAMPLES }}` is valid Jinja - a bare lookup - so it parses and then fails
    at render time looking like an ordinary missing binding. It has to be caught here.
    """
    assert find_pseudo_syntax(token), f"{token} slipped past the detector"


def test_every_bracketed_emoji_name_has_a_mapping() -> None:
    """Covers templates that are not rendered yet.

    An unmapped name does not raise - it passes through into a student's
    section heading as literal bracket text. The day someone wires up 02 is
    exactly the day nobody is checking for this.
    """
    pattern = re.compile(r"\[([A-Z][A-Z ]*EMOJI)\]")
    unmapped: dict[str, set[str]] = {}
    for path in sorted(PROMPTS.glob("*.md")):
        names = set(pattern.findall(path.read_text(encoding="utf-8")))
        missing = names - set(EMOJI)
        if missing:
            unmapped[path.name] = missing

    assert not unmapped, f"bracketed emoji names with no mapping: {unmapped}"


@pytest.mark.parametrize(
    "template",
    ["02_rage_state_addon.md", "04_first_submission_prompt.md", "05_edge_case_handlers.md"],
)
def test_templates_with_control_flow_fail_with_a_useful_message(template: str) -> None:
    """These are out of scope for rung 1; the error must say why, not raise a Jinja trace."""
    path = PROMPTS / template
    if "TEMPLATE:BEGIN" not in path.read_text(encoding="utf-8"):
        pytest.skip(f"{template} has no template markers yet")

    with pytest.raises(UnsupportedTemplateSyntax, match="control flow"):
        render_prompt(sample_context(), template=template, prompts_dir=PROMPTS)


def test_the_error_names_the_conversion() -> None:
    with pytest.raises(UnsupportedTemplateSyntax) as caught:
        render_template_text("{{ IF FILES_CHANGED == 0 }}x{{ ENDIF }}", {})

    message = str(caught.value)
    assert "{% if" in message
    assert "line 1" in message
