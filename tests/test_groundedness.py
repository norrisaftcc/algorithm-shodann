"""The check the validator structurally cannot make.

Every case here is drawn from a real local-model run recorded in
design_docs/EARLY_RUNS.md.
"""

from __future__ import annotations

import pytest

from shodann.groundedness import BLOCKING_THRESHOLD, check_groundedness, ungrounded_tokens
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
