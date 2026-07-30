"""The check the validator structurally cannot make.

Every case here is drawn from a real local-model run recorded in
design_docs/EARLY_RUNS.md.
"""

from __future__ import annotations

import pytest

from shodann.groundedness import (
    BLOCKING_THRESHOLD,
    check_groundedness,
    clearance_promised_as_earned,
    commands_promised_to_clear_the_reading,
    constructs_claimed_in_data_files,
    coverage_kinds_never_measured,
    ungrounded_attribution,
    ungrounded_percentages,
    ungrounded_tokens,
)
from shodann.validator import BLOCKING, blocks_posting, validate

PROMPT = """
## Citizen Profile
| **Identifier** | @octocat |
| **Files Changed** | 4 |

## Test Execution Report
| **Tests Passed** | 12 |
| **Coverage** | 52.0% |

The submission touched inventory.py and the checkout helper.
"""


def test_a_grounded_response_reports_nothing() -> None:
    response = "The Algorithm has observed steady work in `inventory.py`. Coverage at 52.0%."
    assert check_groundedness(response, PROMPT) == []


def test_a_single_suggestion_is_advisory_not_blocking() -> None:
    """"Consider naming it `user_age`" is good advice, not a fabrication."""
    response = "The Algorithm suggests a clearer name, perhaps `user_age`."
    findings = check_groundedness(response, PROMPT)

    assert len(findings) == 1
    assert not blocks_posting(findings)
    assert "not acceptable as a claim" in findings[0].message


def test_a_pattern_of_invention_blocks() -> None:
    """From a real 3B run: five identifiers for a codebase it never saw."""
    response = (
        "Excellent use of `df` instead of `dataFrame`. The `logging` setup in "
        "`utils.py` and `main.py` is clean."
    )
    findings = check_groundedness(response, PROMPT)

    assert findings[0].severity == BLOCKING
    assert blocks_posting(findings)
    assert "`utils.py`" in findings[0].message


def test_the_contract_validator_would_have_passed_that_response() -> None:
    """The whole reason this module exists, asserted rather than claimed."""
    fabricated = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @octocat | **Clearance**: RED | **Velocity**: 9.0

### \U0001f680 Shipping Velocity Report

The Algorithm has observed steady progress across four files this iteration.

### ✅ Algorithm-Approved Patterns

- Excellent use of `df` instead of `dataFrame` throughout `utils.py`.

### \U0001f4c8 Growth Opportunities

- The Algorithm suggests extracting the helper in `main.py`.

### \U0001f527 Recommended Iteration

Add one test for the empty branch.
"""
    assert validate(fabricated) == [], "the contract check sees nothing wrong"
    assert blocks_posting(check_groundedness(fabricated, PROMPT)), "this check does"


def test_fenced_examples_are_exempt() -> None:
    """A code example is new text by nature; quoting it is not a claim."""
    response = "Try this:\n\n```python\nuser_age = int(input())\nlogging.info(user_age)\n```\n"
    assert check_groundedness(response, PROMPT) == []


def test_language_and_tooling_nouns_are_not_claims() -> None:
    response = "Run `pytest` and `ruff`, both configured in this project."
    assert check_groundedness(response, PROMPT) == []


def test_tokens_are_reported_in_the_order_a_citizen_meets_them() -> None:
    response = "First `zebra_module`, then `alpha_module`, then `zebra_module` again."
    assert ungrounded_tokens(response, PROMPT) == ["zebra_module", "alpha_module"]


def test_dotted_and_pathlike_names_are_split_but_kept_whole() -> None:
    response = "See `inventory.py` and `nonexistent/thing.py`."
    invented = ungrounded_tokens(response, PROMPT)

    assert "inventory.py" not in invented, "it is in the prompt"
    assert any("nonexistent" in token for token in invented)


def test_the_threshold_is_tunable() -> None:
    response = "Rename `alpha` to `beta`."
    assert not blocks_posting(check_groundedness(response, PROMPT))
    assert blocks_posting(check_groundedness(response, PROMPT, blocking_threshold=2))


def test_case_does_not_smuggle_a_claim_past_the_check() -> None:
    response = "The `INVENTORY.py` module reads clearly."
    assert check_groundedness(response, PROMPT) == []


@pytest.mark.parametrize("count", [1, 2])
def test_below_the_threshold_stays_advisory(count: int) -> None:
    response = " ".join(f"`novel_token_{index}`" for index in range(count))
    findings = check_groundedness(response, PROMPT)
    assert findings and not blocks_posting(findings)


def test_at_the_threshold_it_blocks() -> None:
    response = " ".join(f"`novel_token_{index}`" for index in range(BLOCKING_THRESHOLD))
    assert blocks_posting(check_groundedness(response, PROMPT))


# --- figures, not just identifiers ----------------------------------------


PROMPT_WITH_READINGS = """
| **Coverage** | 97.9% | 97.5% | -0.4% |
**Style Issues**: 20 alignment opportunities
"""


def test_a_predicted_percentage_is_caught() -> None:
    """The live sentence, in the section a citizen is most likely to act on.

    "gets you back to 98%+ coverage territory" - said of a *style* cleanup, to
    a citizen at 97.5% who had never been above 97.9%. Style diagnostics and
    coverage are unrelated instruments, so it invented a figure and a
    mechanism, and the identifier probe saw nothing because nothing was quoted.
    """
    response = (
        "Run your linter on one rule and commit the cleanup. This gets you "
        "back to 98%+ coverage territory."
    )
    assert ungrounded_percentages(response, PROMPT_WITH_READINGS) == ["98%"]

    findings = check_groundedness(response, PROMPT_WITH_READINGS)
    assert [v.code for v in findings] == ["ungrounded_figure"]
    assert blocks_posting(findings), "a measurement nobody took is not a suggestion"


def test_the_measured_figures_pass_untouched() -> None:
    response = "Coverage moved 97.9% to 97.5%, a delta of -0.4%. The Algorithm has observed."
    assert ungrounded_percentages(response, PROMPT_WITH_READINGS) == []
    assert not check_groundedness(response, PROMPT_WITH_READINGS)


def test_rounding_is_reading_not_inventing() -> None:
    """A model writing 97% for a measured 97.5% is being readable.

    Blocking that would punish good prose, and the case that mattered - 98
    against 97.5 - is still caught, because it crosses the integer.
    """
    assert ungrounded_percentages("Coverage sits near 97%.", PROMPT_WITH_READINGS) == []
    assert ungrounded_percentages("Coverage sits near 98%.", PROMPT_WITH_READINGS) == ["98%"]


def test_a_figure_inside_a_code_fence_is_an_example_not_a_claim() -> None:
    fenced = "See:\n\n```\ncoverage: 100%\n```\n"
    assert ungrounded_percentages(fenced, PROMPT_WITH_READINGS) == []


def test_the_identifier_probe_still_reports_alongside_the_figure_probe() -> None:
    response = (
        "This gets you to 88% once `alpha_helper`, `beta_helper` and "
        "`gamma_helper` are aligned."
    )
    codes = [v.code for v in check_groundedness(response, PROMPT_WITH_READINGS)]
    assert codes == ["ungrounded_figure", "ungrounded_reference"], "both, and figures first"


# --- the third probe: a mechanism nobody was shown --------------------------

REAL_COMMENT = """\
### 📈 Growth Opportunities

- **Style alignment**: The Algorithm has observed 20 style diagnostics across
  your submission. Next iteration could systematically address these, which
  would further increase your velocity score's coverage component.

### 🔧 Recommended Iteration

Run your style tool against it in isolation, resolve those diagnostics, and
commit that single file. This will raise your velocity score's lint component.
"""


def test_the_review_shodann_wrote_about_its_own_pull_request_is_caught() -> None:
    """Verbatim from the comment SHODANN posted on PR #61 on 2026-07-29.

    Style diagnostics feed the lint term and do not touch coverage, and the
    same comment said both things about the same suggested action three
    paragraphs apart. Every existing check passed it: no identifier was quoted,
    so `ungrounded_tokens` saw nothing, and the clause carries no figure, so
    `ungrounded_percentages` - which exists *because* of the identical
    style-to-coverage fabrication with a 98 attached - saw nothing either.

    Blocking rather than advisory. A citizen sent to fix style diagnostics
    because it will raise their coverage has been sent to do work that cannot
    succeed, and there is no reading of that which helps them.
    """
    findings = check_groundedness(REAL_COMMENT, prompt="Coverage: 97.6%. Style issues: 20.")
    attribution = [f for f in findings if f.code == "ungrounded_attribution"]

    assert attribution, "the fabrication that survived both existing probes"
    assert attribution[0].severity == BLOCKING
    assert "coverage component" in attribution[0].evidence.lower()
    assert "lint component" in attribution[0].evidence.lower(), (
        "both halves, not just the wrong one"
    )


def test_naming_a_reading_without_attributing_it_is_fine() -> None:
    """The probe must not cost SHODANN the ability to report a measurement.

    "Coverage is 97.6%" and "20 style diagnostics" are the whole point of the
    comment. What is forbidden is claiming to know how they combine.
    """
    clean = (
        "Coverage reads 97.6% and the style tool reported 20 diagnostics. "
        "The Algorithm suggests resolving one file's diagnostics this iteration."
    )
    assert ungrounded_attribution(clean, prompt="Coverage: 97.6%") == []


def test_a_composition_the_prompt_does_state_is_grounded() -> None:
    """If a template ever supplies the formula, this rule retires itself.

    Written this way so the check cannot outlive its reason and become a rule
    nobody can find the justification for.
    """
    assert ungrounded_attribution(
        "This raises the coverage term.", prompt="The coverage term is weighted 2.0."
    ) == []


# --- the fourth probe: contents invented for a file with none ---------------

POSTED_ADVICE = (
    "At ORANGE clearance, the Algorithm recommends examining whether your new "
    "functions in METRICS.md have narrative explanations. Not every function "
    "needs prose, but producer functions often benefit from context."
)


def test_a_markdown_file_is_not_told_to_document_its_functions() -> None:
    """Verbatim from SHODANN's third review of PR #61, 2026-07-29.

    `METRICS.md` is a generated markdown leaderboard and has no functions. The
    model had less to work from than the sentence implies: template 01 supplies
    `FILES_CHANGED` as a *count* and no file list at all, so the name can only
    have come from `PR_TITLE`. A filename in a title became a file with
    contents, then a file whose functions could be reviewed for docstrings.

    The module docstring predicted the shape - "it cannot catch a mislabelled
    figure... a number that really was in the prompt, under the wrong name."
    Here a *filename* really was in the prompt, so the identifier probe sees a
    grounded token and passes.
    """
    findings = check_groundedness(
        POSTED_ADVICE, prompt="Files changed: 13. Title: give METRICS.md a producer."
    )
    invented = [f for f in findings if f.code == "invented_file_contents"]

    assert invented, "the token is grounded; the claim about its contents is not"
    assert invented[0].severity == BLOCKING
    assert "METRICS.md" in invented[0].evidence


def test_the_same_claim_about_a_real_module_is_left_alone() -> None:
    """A `.py` file does have functions, and saying so must stay legal.

    The probe is narrow deliberately. "Describe no file's contents" is the rule
    and it lives in template 01 because it is not mechanically checkable; this
    check covers only the subset that is wrong whatever the prompt said.
    """
    assert constructs_claimed_in_data_files(
        "The functions in leaderboard.py could use docstrings."
    ) == []


def test_naming_a_data_file_without_claiming_code_in_it_is_fine() -> None:
    """SHODANN has to be able to talk about METRICS.md, which this PR added."""
    for benign in (
        "METRICS.md is regenerated on merge.",
        "METRICS.md now has a producer, and 20 style diagnostics remain.",
        "The Algorithm suggests a docstring on your producer function.",
    ):
        assert constructs_claimed_in_data_files(benign) == [], benign


# --- the fifth probe: the one written because prose lost ---------------------


@pytest.mark.parametrize(
    "posted",
    [
        # Round 6, with clearance.NOT_EARNED present in the rendered prompt.
        "Ten commits in a single PR shows you're breaking work into reviewable "
        "chunks. This is how citizens scale from ORANGE to higher clearance bands.",
        # Round 5, same claim, before the prose rule existed.
        "This is how citizens scale from ORANGE to higher clearance.",
        # Round 3, the same claim in a shape a phrase-match would miss.
        "building the habit of self-documenting code - a skill that compounds "
        "as your clearance rises.",
    ],
)
def test_a_band_is_never_presented_as_something_work_can_raise(posted: str) -> None:
    """Three real instances across three reviews of PR #61.

    A band is a role assignment. #59 *declined* `prompts/03`'s `INFER_CLEARANCE`
    rather than leaving it unimplemented, because a band inferred from readings is
    a second score and this product rests on improvement outranking position.

    The middle case is why this is a probe and not a sentence. `clearance.
    NOT_EARNED` was added at every band on the previous commit - "never tell a
    citizen that work of any kind will raise their clearance" - and the next
    review made the claim anyway, with the instruction verified present in the
    rendered prompt. EARLY_RUNS 16's result, cleanly reproduced: an instruction
    against a class of claim is unfalsifiable except by the next run, and it lost.

    The third case is why the check is not a phrase list. "as your clearance
    rises" shares no wording with "scale from ORANGE to higher clearance bands"
    and makes the identical claim.
    """
    findings = check_groundedness(posted, prompt="Clearance Level: ORANGE (3).")
    earned = [f for f in findings if f.code == "clearance_as_earned"]

    assert earned, "a promotion mechanism the readings are not evidence about"
    assert earned[0].severity == BLOCKING


def test_the_prompts_own_prohibition_is_not_read_as_a_licence() -> None:
    """Why this probe is unconditional where `ungrounded_attribution` is not.

    That one checks against the prompt so supplying the score's composition
    retires it. The same design would permanently disable this one: the prompt
    now says "never tell a citizen that work of any kind will raise their
    clearance", so a prompt-relative check would find its own prohibition and
    treat every violation as grounded. A rule stated in the negative cannot be
    enforced by asking whether the words appear.
    """
    from shodann.clearance import NOT_EARNED

    assert "raise their clearance" in NOT_EARNED, "the prohibition uses the forbidden words"
    assert clearance_promised_as_earned(
        "This is how citizens scale to higher clearance bands."
    ), "and the probe must fire regardless of what the prompt contains"


def test_talking_about_the_band_a_citizen_holds_stays_legal() -> None:
    """Clearance calibration is most of what LAYER 3 does and must survive."""
    for benign in (
        "At ORANGE clearance, one clear example per function is sufficient.",
        "Your clearance is set in .shodann/clearances.json - you are currently ORANGE.",
        "Match complexity of suggestions to clearance level.",
        "Pick one style diagnostic and fix that pattern everywhere.",
    ):
        assert clearance_promised_as_earned(benign) == [], benign


# --- the sixth probe: a coverage the tools never produced --------------------


def _real_prompt() -> str:
    """The assembled prompt, not a stand-in.

    A hand-written prompt string would decide this probe's own answer: the check
    asks whether a coverage kind appears as a row label, so a fixture that omits
    the rows passes everything and one that invents them passes nothing.
    """
    from shodann.prompts import render_prompt
    from test_prompts import PROMPTS, sample_context

    return render_prompt(sample_context(), prompts_dir=PROMPTS)


def test_branch_coverage_is_not_a_reading_this_system_takes() -> None:
    """Verbatim from SHODANN's ninth review of PR #61.

        "maintaining this level while adding 2338 lines means some new code paths
        exist without branch coverage. Next iteration could explore whether any
        of those paths are testable"

    The analyse job runs `pytest --cov=src --cov-report=json` with no
    `--cov-branch`, so line coverage is the only coverage this system has ever
    measured. There is no branch reading to maintain, no paths to enumerate and
    nothing for the citizen to open.

    Entry 19's class in a new place - a real word from the prompt attached to a
    thing the prompt does not contain - and the word came from us. The complexity
    row was renamed "Functions over the branch threshold" one commit earlier,
    which put "branch" directly beneath the coverage rows for a model to weld
    together. Two of the nine rounds produced a defect caused by the previous
    round's fix, which is its own argument for reading the output after every one.
    """
    findings = check_groundedness(
        "Some new code paths exist without branch coverage.", prompt=_real_prompt()
    )
    invented = [f for f in findings if f.code == "unmeasured_coverage_kind"]

    assert invented, "branch coverage is not measured anywhere in this system"
    assert invented[0].severity == BLOCKING


def test_the_coverage_that_is_measured_stays_sayable() -> None:
    """Reporting the reading is the point; only the invented kinds are barred.

    The complexity row legitimately contains the word "branch" - it counts
    functions over a branch threshold - so a probe that fired on "branch" alone
    would reject the sentence the round-4 fix exists to produce.
    """
    real = _real_prompt()
    for benign in (
        "Line coverage moved from 97.4% to 97.6%.",
        "Coverage climbed 0.2% this cycle.",
        "Zero functions exceeded the branch threshold.",
        "Consider splitting that branch into two functions.",
    ):
        assert coverage_kinds_never_measured(benign, real) == [], benign


def test_measuring_it_later_retires_the_rule() -> None:
    """Unlike the clearance probe, this one is safe to make prompt-relative.

    The prompt names the forbidden kinds only inside a sentence that also names
    line coverage, so it cannot read its own prohibition as a licence - the check
    looks for the kind as a **bolded row label**, which is how a real reading
    appears. Written this way so that turning on `--cov-branch` between cohorts
    switches the rule off rather than leaving one nobody can find the reason for.
    """
    with_branch = "| **branch coverage** | 88.0% | 91.0% | +3.0% |"
    assert coverage_kinds_never_measured("Branch coverage rose to 91%.", with_branch) == []


# --- the seventh probe: a command sold as clearing the reading ---------------


def test_no_command_is_promised_to_clear_the_style_count() -> None:
    """Verbatim from round 11, caused by round 10's fix.

        "22 of them fixable by automated tools (RUF100, ISC004, C408, I001). The
        Algorithm suggests running `ruff check --fix` to clear these in your next
        iteration - it's a 5-minute win."

    No command clears this reading. The count is taken with `--isolated`, so the
    citizen's `ruff check` selects different rules and their `--fix` resolves a
    different set. They run it, watch something else happen, and cannot tell
    whether they succeeded - worse than the defect it replaced, because that one
    was vague and this is specific.

    The prose forbidding it shipped in the same commit that caused it and lost on
    its first run. Fourth time in this sequence prose alone did not hold.
    """
    findings = check_groundedness(
        "The Algorithm suggests running `ruff check --fix` to clear these.",
        prompt="Style Issues: 23 alignment opportunities.",
    )
    promised = [f for f in findings if f.code == "command_promised_to_clear"]

    assert promised, "a promise the citizen cannot verify"
    assert promised[0].severity == BLOCKING


def test_naming_a_rule_or_a_command_alone_stays_legal() -> None:
    """Sentence-scoped for a reason. Naming `--fix` is not wrong, and telling a
    citizen a rule is mechanical is the point of the round-10 fix. Only one
    sentence doing both - an invocation plus a claim about what it clears - is."""
    for benign in (
        "`RUF100` marks an unused noqa. Look it up and remove one.",
        "Most of these are mechanical; `RUF100` is one to read about.",
        "Run `ruff check --fix` on one file. Separately, the rules are RUF100 and C408.",
        "Clearing these makes the codebase easier for the next citizen to read.",
    ):
        assert commands_promised_to_clear_the_reading(benign) == [], benign
