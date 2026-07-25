"""The behavioural contract.

These assertions outlive any particular set of weights. The customer expects
the curve to move as real submissions arrive; what may not move is what the
system promises a citizen.
"""

from __future__ import annotations

import math

import pytest

from shodann.config import DEFAULT_CONFIG, ORACLE_CONFIG
from shodann.velocity import (
    FIRST_TESTS_PHRASE,
    CodeMetrics,
    MetricDeltas,
    calculate_velocity,
    composite_score,
)


def metrics(**overrides) -> CodeMetrics:
    return CodeMetrics(**overrides)


# --- iteration is always positive -----------------------------------------


@pytest.mark.parametrize("iterations", [1, 2, 3, 7, 12, 40])
def test_iteration_term_never_subtracts(iterations: int) -> None:
    """More commits must never cost a citizen score. Never suggest fewer commits."""
    deltas = MetricDeltas()
    assert composite_score(deltas, iterations) >= composite_score(deltas, 1)


def test_more_iterations_score_at_least_as_well() -> None:
    deltas = MetricDeltas(coverage=-5.0, test_count=-2)
    scores = [composite_score(deltas, n) for n in range(1, 10)]
    assert scores == sorted(scores)


# --- the two guards -------------------------------------------------------


def test_added_lint_issues_do_not_produce_nan() -> None:
    """A first submission with lint issues has a negative lint delta; sqrt would be NaN."""
    result = calculate_velocity(metrics(coverage=10.0, lint_issues=12), None, 1)
    assert not math.isnan(result.score)
    assert result.deltas.lint_issues == -12


def test_added_lint_issues_are_not_penalised() -> None:
    worse = MetricDeltas(lint_issues=-9)
    unchanged = MetricDeltas(lint_issues=0)
    assert composite_score(worse, 1) == composite_score(unchanged, 1)


def test_reducing_complexity_is_never_a_penalty() -> None:
    simplified = MetricDeltas(complexity=-14)
    unchanged = MetricDeltas(complexity=0)
    assert composite_score(simplified, 1) == composite_score(unchanged, 1)


def test_complexity_without_tests_still_credits_something() -> None:
    with_tests = composite_score(MetricDeltas(complexity=10, test_count=1), 1)
    without_tests = composite_score(MetricDeltas(complexity=10, test_count=0), 1)
    assert 0 < without_tests < with_tests


# --- delta direction ------------------------------------------------------


def test_lint_delta_is_inverted_and_the_rest_are_not() -> None:
    previous = metrics(coverage=40.0, test_count=5, lint_issues=10, docstrings=2)
    current = metrics(coverage=55.0, test_count=8, lint_issues=3, docstrings=4)
    deltas = MetricDeltas.between(current, previous)

    assert deltas.coverage == pytest.approx(15.0)
    assert deltas.test_count == 3
    assert deltas.docstrings == 2
    assert deltas.lint_issues == 7, "fewer lint issues must read as a positive delta"


# --- PRD US-1.3: first tests are hardest tests ----------------------------


def test_first_coverage_gain_outscores_an_equal_later_gain() -> None:
    """0 -> 30 must beat 50 -> 80. The retired engine scored them identically."""
    base = dict(test_count=4, complexity=10, loc=200, functions=8, docstrings=3, lint_issues=2)
    first = calculate_velocity(
        metrics(coverage=30.0, **base), metrics(coverage=0.0, **base), 1
    )
    later = calculate_velocity(
        metrics(coverage=80.0, **base), metrics(coverage=50.0, **base), 1
    )
    assert first.score > later.score


def test_the_retired_engine_really_did_score_them_the_same() -> None:
    """Documents the defect this curve fixes, so nobody 'restores' the old behaviour."""
    base = dict(test_count=4, complexity=10, loc=200, functions=8, docstrings=3, lint_issues=2)
    first = calculate_velocity(
        metrics(coverage=30.0, **base), metrics(coverage=0.0, **base), 1, config=ORACLE_CONFIG
    )
    later = calculate_velocity(
        metrics(coverage=80.0, **base), metrics(coverage=50.0, **base), 1, config=ORACLE_CONFIG
    )
    assert first.score == later.score == pytest.approx(60.50)


def test_first_test_emits_the_required_phrase() -> None:
    result = calculate_velocity(metrics(coverage=12.0, test_count=1), None, 1)
    assert any(FIRST_TESTS_PHRASE in line for line in result.celebrations)


def test_the_phrase_is_not_repeated_to_veterans() -> None:
    veteran = calculate_velocity(
        metrics(coverage=70.0, test_count=20), metrics(coverage=65.0, test_count=18), 2
    )
    assert not any(FIRST_TESTS_PHRASE in line for line in veteran.celebrations)


# --- output contract ------------------------------------------------------


def test_celebrations_are_never_empty() -> None:
    """Even a submission that improved nothing gets something true and kind said about it."""
    flat = calculate_velocity(metrics(), metrics(), 0)
    assert flat.celebrations


def test_opportunities_never_exceed_the_cap() -> None:
    """All three opportunity branches fire at once; the contract allows two."""
    previous = metrics(coverage=0.0, complexity=1, functions=9, docstrings=0)
    current = metrics(coverage=0.0, complexity=20, functions=9, docstrings=0, test_count=0)
    result = calculate_velocity(current, previous, 1)
    assert len(result.opportunities) <= DEFAULT_CONFIG.max_opportunities


def test_no_branch_is_punitive() -> None:
    """A citizen who went backwards is still told they are building a foundation."""
    result = calculate_velocity(
        metrics(coverage=20.0, test_count=1, lint_issues=30),
        metrics(coverage=80.0, test_count=15, lint_issues=0),
        1,
    )
    assert result.score < 0
    assert "Refactoring phase detected" in result.assessment
    for forbidden in ("wrong", "failed", "mistake", "bad"):
        assert forbidden not in result.assessment.lower()


# --- first submission -----------------------------------------------------


def test_first_submission_is_measured_against_zero() -> None:
    result = calculate_velocity(metrics(coverage=42.0, test_count=3), None, 1)
    assert result.is_first_submission
    assert result.deltas.coverage == pytest.approx(42.0)


def test_rounding_matches_javascript_on_exact_halves() -> None:
    """Math.round sends halves toward +infinity; Python's round() is banker's rounding.

    Uses values that are exact in binary, because a decimal literal like 2.345
    is not stored as an exact half and would demonstrate nothing. 0.125 * 100
    is exactly 12.5, so it is a real half and shows the direction.
    """
    from shodann.velocity import _round_half_up

    assert _round_half_up(0.125) == 0.13, "a positive half rounds up"
    assert _round_half_up(-0.125) == -0.12, "a negative half rounds toward zero, not away"
    assert round(0.125, 2) == 0.12, "which is exactly what Python's round() would get wrong"
    assert _round_half_up(0.375) == 0.38
    assert _round_half_up(-33.554) == -33.55
