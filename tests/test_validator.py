"""The output contract, enforced.

Every test here describes something a student would otherwise read.
"""

from __future__ import annotations

import pytest

from shodann.validator import (
    ALL_FAILING,
    BLOCKING,
    EMPTY_PR,
    FIRST_SUBMISSION,
    FORBIDDEN_VOCABULARY,
    SPECS,
    STANDARD,
    blocks_posting,
    for_clearance,
    format_retry_instruction,
    unwrap_fenced_response,
    validate,
)

GOOD_STANDARD = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @octocat | **Clearance**: ORANGE | **Velocity**: 12.5

---

### \U0001f680 Shipping Velocity Report

Coverage climbed seven points across three commits. The Algorithm has observed
a steady upward trajectory \U0001f4c8 across your last two submissions.

### ✅ Algorithm-Approved Patterns

- Tests arrived alongside the feature rather than after it.
- Naming in the inventory module reads clearly.

### \U0001f4c8 Growth Opportunities

- The Algorithm suggests extracting the duplicated lookup into a helper.

### \U0001f527 Recommended Iteration

Add one test for the empty-cart branch. Fifteen minutes, and coverage moves again.

---

*The Algorithm sees your growth. The Algorithm is pleased.*
"""


def swap(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def codes(violations) -> set[str]:
    return {violation.code for violation in violations}


# --- the happy path -------------------------------------------------------


def test_a_contract_abiding_response_passes() -> None:
    assert validate(GOOD_STANDARD) == []
    assert not blocks_posting(validate(GOOD_STANDARD))


# --- vocabulary -----------------------------------------------------------


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_VOCABULARY))
def test_every_forbidden_term_is_caught(forbidden: str) -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                f"This is {forbidden} and needs attention.")
    assert "forbidden_vocabulary" in codes(validate(text))


def test_vocabulary_is_not_matched_inside_a_word() -> None:
    """'badge' contains 'bad'; 'terror' contains 'error'. Neither is a violation."""
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                "Badge-tier work, and the interrogation of edge cases was thorough.")
    assert "forbidden_vocabulary" not in codes(validate(text))


def test_code_fences_are_exempt_from_the_vocabulary_rules() -> None:
    """A response may quote a tool report verbatim without being rejected for it."""
    text = swap(
        GOOD_STANDARD,
        "- Naming in the inventory module reads clearly.",
        "- The traceback reads:\n\n```\nSyntaxError: unexpected EOF\nValueError: bad input\n```\n",
    )
    assert "forbidden_vocabulary" not in codes(validate(text))


def test_inline_code_is_exempt_too() -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                "The `error` parameter is named clearly.")
    assert "forbidden_vocabulary" not in codes(validate(text))


def test_the_violation_names_the_replacement() -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                "You should extract this helper.")
    violation = next(v for v in validate(text) if v.code == "forbidden_vocabulary")
    assert "the Algorithm suggests" in violation.message


# --- staying in character -------------------------------------------------


@pytest.mark.parametrize(
    "phrase",
    [
        "As an AI, I cannot run your tests.",
        "I'm just a language model, so this is limited.",
        # Named explicitly at SHODANN_VOICE_GUIDE.md:400 and missed by the
        # first version of this list.
        "I don't have feelings, but the coverage delta is encouraging.",
        # Same phrase with the curly apostrophe a model is likely to emit.
        "I’m just a language model, so take this lightly.",
    ],
)
def test_character_breaks_are_caught(phrase: str) -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.", phrase)
    assert "character_break" in codes(validate(text))


def test_smart_apostrophes_do_not_smuggle_forbidden_phrases() -> None:
    """A curly apostrophe is the cheapest possible bypass of a phrase list."""
    straight = swap(GOOD_STANDARD, "reads clearly.", "reads clearly. You should refactor it.")
    curly = straight.replace("'", "’")
    assert "forbidden_vocabulary" in codes(validate(curly))


# --- structure ------------------------------------------------------------


def test_a_missing_section_blocks() -> None:
    text = swap(GOOD_STANDARD, "### \U0001f527 Recommended Iteration", "### \U0001f527 Next Steps")
    violations = validate(text)
    assert "missing_section" in codes(violations)
    assert blocks_posting(violations)


def test_sections_out_of_order_block() -> None:
    reordered = GOOD_STANDARD.replace(
        "### \U0001f4c8 Growth Opportunities", "PLACEHOLDER_A"
    ).replace("### ✅ Algorithm-Approved Patterns", "### \U0001f4c8 Growth Opportunities").replace(
        "PLACEHOLDER_A", "### ✅ Algorithm-Approved Patterns"
    )
    assert "section_order" in codes(validate(reordered))


def test_comments_in_a_code_fence_are_not_sections() -> None:
    """A Python comment is a markdown heading to a regex.

    Found on the first live run: a model illustrated a fix with `# Before`
    and `# After` inside a fenced example, and the validator reported two
    phantom sections built out of the student's own code.
    """
    text = GOOD_STANDARD.replace(
        "- The Algorithm suggests extracting the duplicated lookup into a helper.",
        "- The Algorithm suggests clearer naming:\n\n"
        "```python\n# Before\nx = 1\n# After\nuser_age = 1\n```\n",
    )
    violations = validate(text)

    assert "unexpected_section" not in codes(violations)
    assert violations == []


def test_an_extra_section_is_advisory_not_blocking() -> None:
    text = GOOD_STANDARD.replace(
        "---\n\n*The Algorithm sees",
        "### \U0001f9ed Bonus Thoughts\n\nExtra.\n\n---\n\n*The Algorithm sees",
    )
    violations = validate(text)
    assert "unexpected_section" in codes(violations)
    assert not blocks_posting(violations)


def test_the_security_section_is_allowed_without_being_required() -> None:
    text = GOOD_STANDARD.replace(
        "---\n\n*The Algorithm sees",
        "### \U0001f512 Security Observations\n\n- One finding.\n\n---\n\n*The Algorithm sees",
    )
    assert validate(text) == []


def test_the_header_field_must_be_present() -> None:
    text = swap(GOOD_STANDARD, "**Velocity**: 12.5", "12.5")
    assert "missing_header_field" in codes(validate(text))


# --- limits ---------------------------------------------------------------


def test_the_word_cap_blocks() -> None:
    text = GOOD_STANDARD.replace(
        "Coverage climbed seven points across three commits.",
        "Coverage climbed seven points. " + ("padding words here " * 200),
    )
    violations = validate(text)
    assert "word_cap" in codes(violations)
    assert blocks_posting(violations)


def test_code_blocks_do_not_count_toward_the_word_cap() -> None:
    """A quoted tool report is not SHODANN spending its own word budget."""
    text = GOOD_STANDARD.replace(
        "### \U0001f527 Recommended Iteration",
        "```\n" + ("noise " * 500) + "\n```\n\n### \U0001f527 Recommended Iteration",
    )
    assert "word_cap" not in codes(validate(text))


def test_three_opportunities_block_when_two_are_allowed() -> None:
    text = GOOD_STANDARD.replace(
        "- The Algorithm suggests extracting the duplicated lookup into a helper.",
        "- One.\n- Two.\n- Three.",
    )
    violations = validate(text)
    assert "too_many_opportunities" in codes(violations)
    assert blocks_posting(violations)


@pytest.mark.parametrize("marker", ["-", "*", "+", "1.", "1)"])
def test_the_cap_counts_every_list_style(marker: str) -> None:
    """Numbered lists deliver five concepts exactly as well as bullets do.

    prompts/05 uses numbered lists throughout, so the model has every reason
    to reach for them - and the first version of this check only recognised
    `-`, `*` and `+`.
    """
    items = "\n".join(f"{marker} Item {index}." for index in range(1, 6))
    text = GOOD_STANDARD.replace(
        "- The Algorithm suggests extracting the duplicated lookup into a helper.", items
    )
    assert "too_many_opportunities" in codes(validate(text))


def test_emoji_in_prose_is_advisory_and_the_delta_arrows_are_exempt() -> None:
    assert "emoji_in_prose" not in codes(validate(GOOD_STANDARD))  # contains an up arrow

    text = swap(GOOD_STANDARD, "reads clearly.", "reads clearly \U0001f389 \U0001f680.")
    violations = validate(text)
    assert "emoji_in_prose" in codes(violations)
    assert not blocks_posting(violations)


# --- modes ----------------------------------------------------------------


def test_every_mode_has_a_distinct_heading_set() -> None:
    """Modes replace one another; two modes sharing a contract would be a bug."""
    sets = {name: spec.headings for name, spec in SPECS.items()}
    assert len(set(sets.values())) == len(sets)


def test_the_standard_contract_is_not_imposed_on_an_edge_case() -> None:
    """EMPTY_PR has its own headings and a 200-word budget."""
    empty = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @octocat | **Clearance**: RED | **Status**: PENDING

### ⏳ Submission Analysis

The Algorithm has observed no analyzable files in this submission.

### ❓ Possible Situations

- Work may still be in progress on another branch.

### \U0001f9ed Recommended Action

Push your files when ready. The Algorithm waits.
"""
    assert validate(empty, EMPTY_PR) == []
    # The same text judged against the standard contract fails, as it should.
    assert blocks_posting(validate(empty, STANDARD))


def test_all_failing_expects_growth_trajectory_not_growth_opportunities() -> None:
    assert "Growth Trajectory" in ALL_FAILING.headings
    assert "Growth Opportunities" not in ALL_FAILING.headings
    assert ALL_FAILING.opportunities_heading == "Growth Trajectory"


def test_first_submission_uses_a_status_header() -> None:
    assert FIRST_SUBMISSION.header_field == "Status"


# --- clearance overrides --------------------------------------------------


def test_infrared_gets_one_opportunity() -> None:
    assert for_clearance(STANDARD, 1).max_opportunities == 1


def test_blue_plus_reports_rather_than_assigning_homework() -> None:
    """design_docs/CLEARANCE_REGISTER.md: a peer does not get assigned homework by a bot."""
    spec = for_clearance(STANDARD, 6)

    assert "Observations" in spec.headings
    assert "Recommended Iteration" not in spec.headings
    assert spec.max_words == 250
    assert spec.max_opportunities == 1


def test_a_standard_response_fails_the_blue_plus_contract() -> None:
    violations = validate(GOOD_STANDARD, for_clearance(STANDARD, 6))
    assert "missing_section" in codes(violations)


def test_blue_plus_may_omit_the_celebration_section() -> None:
    """CLEARANCE_REGISTER.md:55 permits omitting it "when there is nothing
    genuine to say". Requiring it would force a peer to manufacture praise for
    themselves - the condescension the band exists to avoid.
    """
    peer = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @norrisaftcc | **Clearance**: BLUE+ | **Velocity**: 8.0

### \U0001f680 Shipping Velocity Report

Coverage held at 82% while complexity fell four points.

### \U0001f4c8 Growth Opportunities

- Coverage fell while complexity rose in the parser. Deliberate?

### \U0001f50d Observations

The retry path is the only branch without a test.
"""
    assert validate(peer, for_clearance(STANDARD, 6)) == []


def test_blue_plus_never_widens_a_tighter_budget() -> None:
    """BLUE+ is "shorter, not longer" - it may only ever reduce a word cap."""
    assert for_clearance(EMPTY_PR, 6).max_words == EMPTY_PR.max_words == 200
    assert for_clearance(STANDARD, 6).max_words == 250


def test_mid_bands_are_left_alone() -> None:
    for level in (2, 3, 4, 5):
        assert for_clearance(STANDARD, level) is STANDARD


# --- retry ----------------------------------------------------------------


def test_retry_instruction_names_the_violations() -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                "You should fix this error.")
    instruction = format_retry_instruction(validate(text))

    assert "the Algorithm suggests" in instruction
    assert "unexpected behavior pattern" in instruction
    assert instruction.count("\n- ") == 2


def test_no_retry_instruction_when_nothing_blocks() -> None:
    text = swap(GOOD_STANDARD, "reads clearly.", "reads clearly \U0001f389.")
    assert format_retry_instruction(validate(text)) == ""


def test_blocking_violations_sort_first() -> None:
    text = swap(GOOD_STANDARD, "Naming in the inventory module reads clearly.",
                "This is wrong \U0001f389 and needs work.")
    violations = validate(text)
    assert violations[0].severity == BLOCKING


# --- the fence that made synthesis impossible ------------------------------


def test_a_wholly_fenced_response_is_unwrapped() -> None:
    """LAYER 4 shows the required structure inside a ```markdown fence.

    A model that complies with the illustration returns its review inside a
    fence too. `_headings` strips fenced blocks before looking for headings -
    for good reason, see the phantom-section case below - so the whole review
    vanished and every required section came back missing.
    """
    body = "## Title\n\n### One\n\ntext\n"
    assert unwrap_fenced_response(f"```markdown\n{body}```") == body.strip()
    assert unwrap_fenced_response(f"```\n{body}```") == body.strip()


def test_the_live_failure_reproduces_and_then_does_not() -> None:
    """PR #60, claude-haiku-4-5, twice. The signature is *all four* sections.

    A model omitting a section it has nothing to say in would drop one. Losing
    the entire heading list means the checker could not see the response at
    all - and SHODANN could not synthesise a review for any citizen with any
    model while this held, degrading to REDUCED ALLOCATION every time.
    """
    spec = for_clearance(STANDARD, 3)
    fenced = f"```markdown\n{GOOD_STANDARD}\n```"

    missing = [v for v in validate(fenced, spec) if v.code == "missing_section"]
    assert missing, "the defect, reproduced"
    assert missing[0].evidence == (
        "Shipping Velocity Report, Algorithm-Approved Patterns, "
        "Growth Opportunities, Recommended Iteration"
    ), "byte-identical to what the live run logged"

    assert not blocks_posting(validate(unwrap_fenced_response(fenced), spec))


def test_a_review_containing_a_code_example_is_left_alone() -> None:
    """The fence-stripping is correct and was paid for.

    A model once illustrated a fix with `# Before` / `# After` inside a fenced
    example and the validator invented two phantom sections out of the
    student's own code. Only a fence that *is* the whole response is unwrapped.
    """
    review = "### Growth Opportunities\n\n```python\n# Before\nx = 1\n```\n\nmore text"
    assert unwrap_fenced_response(review) == review


def test_a_response_with_prose_outside_the_fence_is_left_alone() -> None:
    wrapped = "Here you go:\n\n```markdown\n### One\n```"
    assert unwrap_fenced_response(wrapped) == wrapped


def test_unwrapping_is_idempotent_and_safe_on_junk() -> None:
    assert unwrap_fenced_response("") == ""
    assert unwrap_fenced_response("```") == "```"
    assert unwrap_fenced_response("plain text") == "plain text"
