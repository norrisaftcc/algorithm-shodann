"""Growth velocity: the rate of improvement, not the absolute position.

The person who goes from terrible to okay beats the person who stays good.
This module is the ported successor to ``design_docs/growth-velocity.js`` and
is the only authoritative statement of the scoring maths - prose descriptions
elsewhere in the repo are all partial.

Two guards in :func:`composite_score` are load-bearing and easy to lose:

* a complexity delta contributes only when it is positive, so simplifying code
  is never a penalty
* a lint delta contributes only when it is positive, so ``sqrt`` is never
  handed a negative number - which is the common case, since a first
  submission with any lint issues has a negative lint delta
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .config import DEFAULT_CONFIG, VelocityConfig

__all__ = [
    "CodeMetrics",
    "MetricDeltas",
    "VelocityResult",
    "analyze_growth",
    "calculate_velocity",
    "composite_score",
    "describe",
]

FIRST_TESTS_PHRASE = "First tests are hardest tests"
"""Required verbatim by PRD US-1.3 whenever a citizen writes their first test."""


@dataclass(frozen=True)
class CodeMetrics:
    """One submission's hard-analysis facts. Produced by tools, never by a model."""

    coverage: float = 0.0
    test_count: int = 0
    complexity: int = 0
    loc: int = 0
    functions: int = 0
    docstrings: int = 0
    lint_issues: int = 0
    syntax_errors: int = 0

    @classmethod
    def baseline(cls) -> CodeMetrics:
        """The zeroed metrics a citizen is measured against on their first submission."""
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> CodeMetrics:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class MetricDeltas:
    """Change since the previous submission - the dy/dx the whole system measures.

    Every field is ``current - previous`` except :attr:`lint_issues`, which is
    inverted so that positive always means improvement.
    """

    coverage: float = 0.0
    test_count: int = 0
    complexity: int = 0
    loc: int = 0
    functions: int = 0
    docstrings: int = 0
    lint_issues: int = 0

    @classmethod
    def between(cls, current: CodeMetrics, previous: CodeMetrics) -> MetricDeltas:
        return cls(
            coverage=current.coverage - previous.coverage,
            test_count=current.test_count - previous.test_count,
            complexity=current.complexity - previous.complexity,
            loc=current.loc - previous.loc,
            functions=current.functions - previous.functions,
            docstrings=current.docstrings - previous.docstrings,
            lint_issues=previous.lint_issues - current.lint_issues,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class VelocityResult:
    score: float
    deltas: MetricDeltas
    assessment: str
    celebrations: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    iterations: int = 1
    is_first_submission: bool = False

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "deltas": self.deltas.to_dict(),
            "assessment": self.assessment,
            "celebrations": list(self.celebrations),
            "opportunities": list(self.opportunities),
            "iterations": self.iterations,
            "is_first_submission": self.is_first_submission,
        }


def _round_half_up(value: float, places: int = 2) -> float:
    """Round halves toward positive infinity, matching JavaScript's ``Math.round``.

    Python's built-in :func:`round` is banker's rounding (2.5 -> 2) and would
    disagree on exact halves, which is precisely where a transcription bug
    hides. Note this is *not* "away from zero": ``Math.round(-0.5)`` is ``-0``,
    so a single ``floor(x + 0.5)`` covers both signs.
    """
    scale = 10**places
    return math.floor(value * scale + 0.5) / scale


def _coverage_multiplier(previous_coverage: float, config: VelocityConfig) -> float:
    """Weight coverage gained from a low base more heavily (PRD US-1.3).

    Returns 1.0 when the bonus is disabled, which is how ORACLE_CONFIG
    reproduces the original flat curve.
    """
    if config.first_test_bonus <= 0:
        return 1.0
    headroom = 1.0 - (min(max(previous_coverage, 0.0), 100.0) / 100.0)
    return 1.0 + config.first_test_bonus * headroom


def _growth_delta(deltas: MetricDeltas, config: VelocityConfig) -> int:
    """Which delta the "complexity growth" term actually means.

    It means "how much code did you take on", and it always did - until C901
    was measured, `complexity` and `functions` were the same `def ` count set
    from one variable, so the term's label and its input never had to agree.
    Now they do. `functions` is the honest one.

    Reading `complexity` instead would be worse than a mislabel: a positive
    delta in a C901 count means the citizen *added a function over the branch
    threshold*, and this term would pay them for it.

    Worth surfacing rather than quietly settling - unbounded growth in how
    much code you took on is a signal, but probably not a good one. It is the
    lines-of-code metric with a smaller coefficient, and the one-sided guard
    around it is all that stops it penalising a citizen who deletes code. It
    survives because PRD section 8 forbids removing a signal mid-cohort, not
    because it earned its place. Revisit between cohorts.
    """
    return deltas.functions if config.complexity_growth_reads_functions else deltas.complexity


def composite_score(
    deltas: MetricDeltas,
    iterations: int,
    *,
    previous_coverage: float = 0.0,
    config: VelocityConfig = DEFAULT_CONFIG,
) -> float:
    """Combine the deltas into a single velocity score.

    Never returns NaN, and never lets the iteration term subtract.
    """
    weights = config.weights
    score = 0.0

    score += deltas.coverage * weights.coverage_delta * _coverage_multiplier(
        previous_coverage, config
    )
    score += deltas.test_count * weights.test_growth

    # Iteration bonus. Always non-negative: we celebrate attempts, and the
    # system must never make a citizen regret committing.
    if iterations > 0:
        score += math.log2(iterations + 1) * weights.iteration_count * iterations

    # Only ever adds. Growing alongside tests is healthy; growing without
    # tests earns a smaller credit, never a penalty.
    growth = _growth_delta(deltas, config)
    if growth > 0:
        factor = 1.0 if deltas.test_count > 0 else config.untested_complexity_factor
        score += growth * weights.complexity_growth * factor

    score += deltas.docstrings * weights.documentation_delta

    # Guard: a negative lint delta means issues were added. sqrt() of that is
    # NaN, which would poison the entire score.
    if deltas.lint_issues > 0:
        score += math.sqrt(deltas.lint_issues) * weights.lint_improvement

    return score


def describe(score: float, config: VelocityConfig = DEFAULT_CONFIG) -> str:
    """Assessment line for the score. Even a negative score gets a growth frame."""
    thresholds = config.thresholds
    if score >= thresholds.exceptional:
        return "\U0001f680 EXCEPTIONAL GROWTH DETECTED - The Algorithm is deeply pleased"
    if score >= thresholds.positive:
        return "\U0001f4c8 Positive trajectory - Shipping velocity optimal"
    if score >= thresholds.baseline:
        return "\U0001f4ca Baseline established - Ready for growth acceleration"
    return "\U0001f504 Refactoring phase detected - Foundation building in progress"


Note = tuple[list[str], list[str]]
"""(celebrations, opportunities) contributed by one observation."""


def _iterations_note(iterations: int, config: VelocityConfig) -> Note:
    if iterations >= config.iterations.exceptional:
        return ([
            f"{iterations} iterations this PR! Exceptional commitment to incremental development."
        ], [])
    if iterations >= config.iterations.celebrated:
        return ([f"{iterations} commits shows healthy iteration patterns."], [])
    if iterations > 0:
        return ([f"Iteration count: {iterations}. Every commit is progress."], [])
    return ([], [])


def _first_test_note(current: CodeMetrics, previous: CodeMetrics, config: VelocityConfig) -> Note:
    """PRD US-1.3's required phrase.

    Travels with the curve that earns it, so ORACLE_CONFIG reproduces the
    pre-US-1.3 engine exactly, celebrations included.
    """
    if config.first_test_bonus <= 0:
        return ([], [])
    wrote_first_test = previous.test_count == 0 and current.test_count > 0
    covered_for_first_time = previous.coverage <= 0 and current.coverage > 0
    if wrote_first_test or covered_for_first_time:
        return ([f"{FIRST_TESTS_PHRASE}. The Algorithm weights this one heavily."], [])
    return ([], [])


def _coverage_note(deltas: MetricDeltas, current: CodeMetrics) -> Note:
    """Celebrate coverage movement; suggest a first test when there are none.

    The suggestion keys on ``test_count``, not on ``coverage == 0``. A zero
    coverage reading means one of two very different things - nobody has
    written a test, or nobody has measured - and the predecessor could not
    tell them apart. Until the hard-analysis job exists nothing measures
    coverage at all, so keying on coverage told a citizen with 110 test
    functions to write their first one, on every single review.
    """
    if deltas.coverage > 10:
        return ([f"Coverage jumped {deltas.coverage:.1f}%! Significant testing investment."], [])
    if deltas.coverage > 0:
        return ([f"Coverage improved by {deltas.coverage:.1f}%. Tests validate your growth."], [])
    if current.test_count == 0:
        return ([], [
            "First test = first step to confidence. Consider adding one test this iteration."
        ])
    return ([], [])


def _tests_note(deltas: MetricDeltas) -> Note:
    if deltas.test_count > 0:
        return ([f"{deltas.test_count} new test(s) added. The Algorithm approves."], [])
    return ([], [])


def _documentation_note(deltas: MetricDeltas, current: CodeMetrics) -> Note:
    if deltas.docstrings > 0:
        return (["Documentation improved. Future-you will be grateful."], [])
    if current.docstrings == 0 and current.functions > 3:
        return ([], ["Consider adding docstrings to your main functions."])
    return ([], [])


def _lint_note(deltas: MetricDeltas) -> Note:
    if deltas.lint_issues > 3:
        return ([f"{deltas.lint_issues} fewer lint issues. Code clarity increasing."], [])
    return ([], [])


def _complexity_note(deltas: MetricDeltas, config: VelocityConfig) -> Note:
    """Keyed on the same delta the score term is, for the same reason.

    These sentences say "you took on more code", which is what a `def ` count
    measures. Said about a C901 count they would congratulate a citizen for
    writing a function with more branches than the threshold allows.
    """
    growth = _growth_delta(deltas, config)
    if growth > 0 and deltas.test_count > 0:
        return (["Complexity growth backed by tests. Sustainable expansion."], [])
    if growth > 5 and deltas.test_count == 0:
        return ([], [
            "Complexity grew significantly. Consider adding tests to validate new logic."
        ])
    return ([], [])


def analyze_growth(
    deltas: MetricDeltas,
    current: CodeMetrics,
    previous: CodeMetrics,
    iterations: int,
    *,
    config: VelocityConfig = DEFAULT_CONFIG,
) -> Note:
    """Pick out what to celebrate and what to suggest.

    Order matters: it is the order a citizen reads them in. Celebrations are
    never empty. Opportunities are capped at ``config.max_opportunities``,
    enforced here rather than left to the prompt layer to remember.
    """
    notes = [
        _iterations_note(iterations, config),
        _first_test_note(current, previous, config),
        _coverage_note(deltas, current),
        _tests_note(deltas),
        _documentation_note(deltas, current),
        _lint_note(deltas),
        _complexity_note(deltas, config),
    ]

    celebrations = [line for note in notes for line in note[0]]
    opportunities = [line for note in notes for line in note[1]]

    if not celebrations:
        celebrations.append("Code submitted. That's the hardest step. Keep shipping.")

    return celebrations, opportunities[: config.max_opportunities]


def calculate_velocity(
    current: CodeMetrics | dict,
    previous: CodeMetrics | dict | None = None,
    iterations: int = 1,
    *,
    config: VelocityConfig = DEFAULT_CONFIG,
) -> VelocityResult:
    """Score one submission against the citizen's previous state.

    ``previous`` may be ``None`` for a first submission, in which case the
    citizen is measured against zeroed metrics - so their first coverage delta
    equals their absolute coverage.
    """
    if isinstance(current, dict):
        current = CodeMetrics.from_dict(current)
    if isinstance(previous, dict):
        previous = CodeMetrics.from_dict(previous)

    is_first = previous is None
    baseline = previous if previous is not None else CodeMetrics.baseline()

    deltas = MetricDeltas.between(current, baseline)
    raw = composite_score(
        deltas, iterations, previous_coverage=baseline.coverage, config=config
    )
    celebrations, opportunities = analyze_growth(
        deltas, current, baseline, iterations, config=config
    )

    return VelocityResult(
        score=_round_half_up(raw),
        deltas=deltas,
        assessment=describe(raw, config),
        celebrations=celebrations,
        opportunities=opportunities,
        iterations=iterations,
        is_first_submission=is_first,
    )

