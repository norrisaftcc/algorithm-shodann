"""Prompt assembly: extraction, strict binding, and the syntax we cannot render."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from jinja2 import Environment, StrictUndefined, meta
from jinja2.exceptions import UndefinedError

from shodann.analysis import AnalysisReports
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


MEASURED = AnalysisReports(
    coverage=52.0,
    lint_issues=18,
    complexity=2,
    syntax_errors=0,
    tests_passed=9,
    tests_failed=0,
)
"""A cycle where every tool ran. The realistic case, and no longer the default.

`build_context` used to default coverage to instrumented and every other
reading to a hardcoded zero, so a context built with no reports at all looked
like a fully measured green run. That default was the defect; an omitted
`reports` now means nothing was measured, which is what an omitted report
directory actually means.
"""


def sample_context(reports: AnalysisReports | None = MEASURED) -> dict:
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
        reports=reports,
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
        reports=AnalysisReports(lint_issues=4, complexity=0, syntax_errors=0),
    )
    rendered = render_prompt(context, prompts_dir=PROMPTS)
    coverage_rows = [line for line in rendered.splitlines() if "**Coverage**" in line]

    assert not coverage_rows, "a row with Previous and Current columns implies a progression"
    assert "Coverage was not measured this cycle." in rendered
    assert "Do not report, infer, or celebrate" in rendered

    # The complexity row must survive the branch it shares a table with. Named
    # by its unit since a model read a bare "0" as "not measured" - see
    # test_a_measured_zero_is_not_reported_as_an_absent_reading.
    assert "**Functions over the branch threshold**" in rendered

    # The prime directive's "0% to 30%" is illustrative prose, not a reading,
    # and must survive untouched.
    assert "0% to 30% test" in rendered


def test_instrumented_coverage_still_reports_normally() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "**Line coverage**" in rendered, (
        "the unit is part of the label - see the branch-coverage test"
    )
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


# --- the tallies, measured and not ----------------------------------------


def test_measured_tallies_render_as_the_numbers_they_are() -> None:
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "| **Tests Passed** | 9 |" in rendered
    assert "| **Tests Failed** | 0 |" in rendered
    assert "9 passed, none in a pre-success state." in rendered
    assert "**Style Issues**: 18 alignment opportunities" in rendered
    assert "**Syntax Status**: 0 compilation barriers detected" in rendered


def test_the_fenced_report_never_contradicts_the_table_beside_it() -> None:
    """The two used to disagree on every review ever composed.

    "No tests executed." was printed in the fence while the table asserted a
    measured 0 passed and 0 failed - a placeholder string beside a confident
    reading, in the same nine lines, for a repository with 245 passing tests.
    """
    reports = AnalysisReports(lint_issues=3, complexity=0, syntax_errors=0,
                              tests_passed=0, tests_failed=11)
    rendered = render_prompt(sample_context(reports), prompts_dir=PROMPTS)

    assert "0 passed, 11 in a pre-success state." in rendered
    assert "| **Tests Failed** | 11 |" in rendered
    assert "No tests executed." not in rendered


def test_unmeasured_tallies_drop_the_rows_and_forbid_the_claim() -> None:
    """The coverage treatment, applied to the reading beside it.

    A row with a Previous and a Current column implies a progression whatever
    you put in it, and a row reading 0 implies a measurement. Neither is
    available when no runner reported, so neither row is printed.
    """
    rendered = render_prompt(sample_context(AnalysisReports()), prompts_dir=PROMPTS)

    assert "| **Tests Passed** |" not in rendered
    assert "| **Tests Failed** |" not in rendered
    assert "Test outcomes were not measured this cycle." in rendered
    assert "do not tell this citizen that" in rendered
    assert "Not measured this cycle." in rendered


def test_an_unmeasured_syntax_status_is_not_a_clean_bill_of_health() -> None:
    rendered = render_prompt(sample_context(AnalysisReports()), prompts_dir=PROMPTS)

    assert "compilation barriers detected" not in rendered
    assert "Nothing checked whether this code parses." in rendered


def test_an_unmeasured_style_count_is_not_a_count_of_zero() -> None:
    rendered = render_prompt(sample_context(AnalysisReports()), prompts_dir=PROMPTS)

    assert "alignment opportunities" not in rendered
    assert "No style tool ran this cycle." in rendered


def test_coverage_still_reports_when_only_the_tests_went_unmeasured() -> None:
    """The two readings are independent, and one gap must not swallow the other."""
    rendered = render_prompt(sample_context(AnalysisReports(coverage=52.0)), prompts_dir=PROMPTS)

    assert "**Line coverage**" in rendered
    assert "Coverage was not measured" not in rendered
    assert "Test outcomes were not measured this cycle." in rendered


# --- the prompt refuses the lesson the metric exists to refuse -------------


def test_the_prompt_states_what_the_score_is_made_of() -> None:
    """The first synthesised review attributed velocity to volume.

    "your velocity score of 119.03 reflects the substantial work across 16
    files and 1,302 lines added" - and `loc` is not a term in the composite at
    all. That sentence teaches a citizen to write more lines, which is the
    single behaviour `PRD.md` section 7 forbids the system from rewarding.

    The groundedness probe cannot catch it: every number really was in the
    prompt, and the claim contains no novel backticked identifier. Its own
    docstring says so - a mislabelled figure is outside what it can see. The
    prompt is the only place this can be prevented.
    """
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "Lines added and files changed are not in it" in rendered
    assert "teaches a citizen to write more lines" in rendered


def test_the_reserved_first_tests_phrase_is_not_offered_to_the_model() -> None:
    """The engine guards this and the model is not bound by the engine.

    `test_the_phrase_is_not_repeated_to_veterans` stops `calculate_velocity`
    saying it to someone with 245 tests. The first synthesised review said it
    anyway, to a citizen with 363 - the phrase is a specific pedagogical
    signal for a specific moment, and spending it elsewhere is what makes it
    stop meaning anything.
    """
    from shodann.velocity import FIRST_TESTS_PHRASE

    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)
    # Wrapped prose, so the instruction spans a line break.
    instruction = " ".join(rendered.split("Algorithm-Approved Patterns")[1].split())

    assert f'Do not write "{FIRST_TESTS_PHRASE}"' in instruction


def test_the_prompt_forbids_connecting_two_instruments() -> None:
    """Two live reviews invented a mechanism between unrelated measurements.

    "gets you back to 98%+ coverage territory" from a style cleanup, and
    "complexity may have increased faster than test coverage" when the
    measured complexity delta was 0. Neither is a hallucinated *number* - both
    are hallucinated *causation*, which is the harder thing and the one that
    sends a citizen to do work that cannot succeed.
    """
    rendered = " ".join(render_prompt(sample_context(), prompts_dir=PROMPTS).split())

    assert "separate instruments, and you may not connect them" in rendered
    assert "If a delta reads 0, nothing moved" in rendered
    assert "no targets, no predictions" in rendered


def test_the_model_is_told_it_has_not_seen_the_code() -> None:
    """The rule that was missing entirely, and the review that needed it.

    SHODANN's third review of PR #61 recommended "examining whether your new
    functions in METRICS.md have narrative explanations". METRICS.md is a
    generated markdown leaderboard with no functions - and the model had less
    than that sentence implies to work from, because this template supplies
    `FILES_CHANGED` as a *count* and no file list at all. The only place the
    name can have come from is `PR_TITLE`. A filename in a title became a file
    with contents, then a file whose functions could be reviewed.

    Nothing anywhere told the model it had not read the submission. The
    groundedness block forbade inventing figures and causes and said nothing
    about inventing *contents*, so this was not a rule being broken - it was a
    rule that did not exist.

    Asserted because the prose half of this fix had no guard when it was
    written: deleting the paragraph left 418 tests green, which is EARLY_RUNS 13
    exactly. `groundedness.constructs_claimed_in_data_files` covers the subset
    that is mechanically checkable; this covers the instruction that covers the
    rest.
    """
    rendered = " ".join(render_prompt(sample_context(), prompts_dir=PROMPTS).split())

    assert "You have not seen this submission's code" in rendered
    assert "no file list, no source, no diff" in rendered
    assert "Do not describe the contents of a file" in rendered


def test_the_streak_is_labelled_with_the_unit_it_actually_counts() -> None:
    """SHODANN said "your iteration streak of 18 commits" and was quoting us.

    `save_citizen_history` increments `iteration_streak` once per recorded
    submission - consecutive *submissions*, never commits. The prompt labelled
    it "commits", the model repeated the label faithfully, and the citizen was
    told a number about their commit history that was really about their
    submission history.

    Worth its own test because of how nearly it was filed against the model.
    A mislabelled figure looks identical to a fabricated one from the outside,
    and the difference is entirely in whose text the label came from.

    The label broke a second time, in the other half of the phrase, and by the
    same mechanism. S1-23 made the increment unconditional - a refactoring PR
    scoring below zero extends the streak, because no branch of this engine is
    punitive - while the template still read "with positive velocity". This
    test asserted that string and passed, so the suite was pinning the stale
    wording in place: the fix for EARLY_RUNS 16 recreated EARLY_RUNS 16. Both
    directions are asserted now, because a label is only checkable against the
    rule it claims to describe.
    """
    rendered = render_prompt(sample_context(), prompts_dir=PROMPTS)

    assert "Iteration Streak** | 2 commits" not in rendered
    assert "positive velocity" not in rendered, (
        "S1-23: the streak counts every submission, including one that scored below zero"
    )
    assert "whatever each scored" in rendered, "the sign-independence has to survive"


def test_the_two_submission_counters_do_not_contradict_each_other() -> None:
    """SHODANN reviewed PR #61 and said both of these, one paragraph apart:

        "The Algorithm observes sustained momentum across your 20th submission"
        "This is your 19th consecutive submission recorded."

    Both were faithful to the prompt, which is what makes it ours. `review()`
    increments `pr_count` before assembling the context, so `PR_COUNT` arrives
    as the current submission's number while `PREV_STREAK` arrives as the
    stored, un-incremented streak - and S1-23 had just made the two counters
    count the same events, so template 01 was handing the model two aliases one
    apart with the post-increment one labelled "Previous Submissions".

    Neither value changed. Both rows now say which of the two they are, because
    the numbers were right and only the labels were lying.
    """
    rendered = " ".join(render_prompt(sample_context(), prompts_dir=PROMPTS).split())

    assert "Previous Submissions" not in rendered, (
        "a post-increment count is not a count of previous submissions"
    )
    assert "Submission Number" in rendered
    assert not re.search(r"Iteration Streak\*\* \| \d", rendered), (
        "the streak row must carry no number of its own - see the docstring"
    )
    # And no arithmetic either. The first version of this fix replaced the
    # duplicate figure with "This is Submission Number minus one, not a second
    # figure to report" - which handed the model a calculation and a prohibition
    # in one sentence. It did the calculation: the next review opened with
    # "19 consecutive submissions" beside "20 submissions, 20 counted", the same
    # contradiction restored from a subtraction rather than from a second row.
    # An instruction not to report a number is not a way to avoid supplying one.
    assert "minus one" not in rendered, "do not hand the model the subtraction"
    assert "whatever each scored" in rendered, "the sign-independence still has to survive"


def test_a_measured_zero_is_not_reported_as_an_absent_reading() -> None:
    """The absent-vs-zero rule, running in the other direction.

    Every guard for this so far has protected against an *absent* reading being
    reported as a zero. SHODANN's fourth review of PR #61 did the reverse, and
    nothing was watching that side:

        "Zero complexity metrics recorded. As scope expands, the next level
        involves understanding *where* complexity lives"

    The reading was 0 and it was measured - a ruff `C901` count of zero means no
    function exceeded the branch threshold, which is a good result and the best
    available one. The citizen was told their complexity had not been captured
    and sent to go and find it.

    The row was labelled `**Complexity**` and carried a bare integer, and the
    unit had changed under it in #58 from a count of `def ` to a count of
    threshold violations. "Complexity: 0" invites exactly one reading from
    anything that has not been told the unit. The row now names what it counts,
    and the prompt states that a visible number is never a missing one - a
    reading that was not taken has no row at all, which is the mechanism the
    coverage, syntax, tests and style branches already use.
    """
    context = sample_context(
        AnalysisReports(
            coverage=97.6, lint_issues=20, complexity=0, syntax_errors=0,
            tests_passed=419, tests_failed=0,
        )
    )
    rendered = render_prompt(context, prompts_dir=PROMPTS)

    assert "**Functions over the branch threshold**" in rendered, "a bare 'Complexity' has no unit"
    assert "is a measurement and a good one" in rendered
    assert "never describe a number you can see as missing" in rendered


def test_no_streak_figure_reaches_the_model_from_anywhere() -> None:
    """The whole prompt, not one row - which is why the first two fixes failed.

    `iteration_streak` equals `pr_count` for every ledger this system writes
    (S1-42), so any prompt carrying both hands the model two numbers for one
    quantity, one apart. Three consecutive reviews reported both:

        round 2  "your 20th submission" / "your 19th consecutive submission"
        round 4  "Submission 20 lands"  / "This is your 19th consecutive submission"
        round 7  "Across 20 submissions" / "across 19 consecutive submissions"

    Round 2's fix relabelled the rows. Round 4's replaced the figure with "This
    is Submission Number minus one", which handed over a subtraction instead of a
    number, and the model did the subtraction. Round 7's contradiction survived
    both because the *same figure* was still arriving through
    `HISTORY_NARRATIVE`, which `describe_history` composed separately - one
    answer in two places, found only by grepping the assembled prompt for the
    number rather than the row.

    Asserted over the rendered whole for that reason. A row-scoped assertion is
    what let this run three times.
    """
    context = sample_context()
    rendered = render_prompt(context, prompts_dir=PROMPTS)
    streak = context["PREV_STREAK"]

    assert streak, "the fixture must carry a non-zero streak or this proves nothing"
    assert f"streak: {streak}" not in rendered.lower()
    assert "minus one" not in rendered, "nor a way to derive it"
    # The trend is a genuinely separate reading and must survive.
    assert "Velocity trend:" in rendered


def test_the_style_rules_reach_the_model_instead_of_being_guessed() -> None:
    """S1-45, at the layer where the guessing happened.

    Handed "23 style diagnostics" and nothing else, the model supplied the rest
    in five of ten reviews: categories it invented, a fixable count it invented,
    and a command that shows the citizen nothing. The rules were in `ruff.json`
    the whole time.
    """
    reports = AnalysisReports(
        coverage=52.0, lint_issues=23, complexity=0, syntax_errors=0,
        tests_passed=436, tests_failed=0,
        style_breakdown=[("RUF100", 8), ("ISC004", 5), ("C408", 4)], style_fixable=22,
    )
    rendered = render_prompt(sample_context(reports), prompts_dir=PROMPTS)

    assert "`RUF100` x8" in rendered
    assert "22 of them are fixable" in rendered
    assert "Name only these rules" in rendered, "four rules are not the whole count"
    assert "own lint configuration ignored" in rendered, (
        "the citizen's own ruff check reports a different number and must not be promised one"
    )


def test_an_unrecorded_breakdown_refuses_rather_than_inviting_one() -> None:
    """Absent is not zero here either, and the failure mode is specific: an
    empty breakdown beside a real count is exactly the gap the model filled."""
    reports = AnalysisReports(
        coverage=52.0, lint_issues=23, complexity=0, syntax_errors=0,
        tests_passed=436, tests_failed=0,
    )
    rendered = render_prompt(sample_context(reports), prompts_dir=PROMPTS)

    assert "rules behind this count were not recorded" in rendered
    assert "Do not name, guess or illustrate a rule" in rendered
    assert "23 alignment opportunities" in rendered, "the count itself is still reported"
