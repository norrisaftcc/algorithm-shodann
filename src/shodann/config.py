"""Tunable knobs for the velocity engine.

Weights, thresholds and curve shape are expected to move as real submissions
arrive. What may not move is the behavioural contract they implement:

* the iteration term can never subtract
* no branch is punitive
* improvement outranks position

Two configurations ship. ``DEFAULT_CONFIG`` is what runs in production.
``ORACLE_CONFIG`` disables the first-test bonus so the engine reproduces the
original ``design_docs/growth-velocity.js`` numbers exactly, which is how the
snapshot tests catch transcription errors.
"""

from dataclasses import dataclass, field

__all__ = [
    "DEFAULT_CONFIG",
    "ORACLE_CONFIG",
    "IterationMilestones",
    "Thresholds",
    "VelocityConfig",
    "Weights",
]


@dataclass(frozen=True)
class Weights:
    """Multipliers applied to each metric delta."""

    coverage_delta: float = 2.0
    test_growth: float = 1.5
    iteration_count: float = 0.5
    complexity_growth: float = 0.3
    documentation_delta: float = 0.8
    lint_improvement: float = 0.5


@dataclass(frozen=True)
class Thresholds:
    """Score boundaries that select the assessment message."""

    exceptional: float = 10.0
    positive: float = 3.0
    baseline: float = 0.0


@dataclass(frozen=True)
class IterationMilestones:
    """Commit counts that earn a celebration."""

    celebrated: int = 3
    exceptional: int = 7


@dataclass(frozen=True)
class VelocityConfig:
    weights: Weights = field(default_factory=Weights)
    thresholds: Thresholds = field(default_factory=Thresholds)
    iterations: IterationMilestones = field(default_factory=IterationMilestones)

    first_test_bonus: float = 1.0
    """Strength of the PRD US-1.3 curve.

    Coverage gained from a low base is worth more than the same gain from a
    high base, because the first test is harder than the tenth. The multiplier
    is ``1 + first_test_bonus * (1 - previous_coverage / 100)``: at 1.0 a gain
    starting from zero coverage counts double, and a gain starting from full
    coverage counts once. Set to 0.0 for the flat curve the JS engine used.
    """

    untested_complexity_factor: float = 0.3
    """Applied to ``weights.complexity_growth`` when complexity grew but tests did not.

    Growing complexity without tests is a smaller credit, never a penalty.
    """

    complexity_growth_reads_functions: bool = True
    """Take the growth term from ``functions`` rather than ``complexity``.

    A deliberate divergence from the oracle, expressed here rather than in the
    engine so ``ORACLE_CONFIG`` still reproduces the retired JavaScript exactly
    - the same mechanism ``first_test_bonus`` uses.

    The oracle read ``complexity``. In production the two fields have always
    held the same number, a count of ``def ``, because ``collect_metrics`` set
    them from one variable. Now that ``complexity`` carries a real C901
    reading, the term has to say which of the two it always meant: "how much
    code did you take on", which is ``functions``. Pointing it at C901 instead
    would credit a citizen for adding a function over the branch threshold.

    Only the synthetic oracle fixtures ever set the two fields apart, so
    flipping this changes no real citizen's score by any amount.
    """

    max_opportunities: int = 2
    """Hard cap from the output contract. The engine truncates; job 4 must not have to."""

    velocity_history_length: int = 10


DEFAULT_CONFIG = VelocityConfig()

ORACLE_CONFIG = VelocityConfig(
    first_test_bonus=0.0,
    complexity_growth_reads_functions=False,
)
"""Reproduces design_docs/growth-velocity.js. Test-only - never ship this."""
