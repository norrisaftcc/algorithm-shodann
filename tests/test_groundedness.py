"""The check the validator structurally cannot make.

Every case here is drawn from a real local-model run recorded in
design_docs/EARLY_RUNS.md.
"""

from __future__ import annotations

import pytest

from shodann.groundedness import (
    BLOCKING_THRESHOLD,
    check_groundedness,
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
