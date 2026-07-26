"""The citizen ledger.

One JSON file per citizen at ``.shodann/citizens/{citizen}.json``, living in
the repository being reviewed. That file is the authoritative record; the
course-level ``METRICS.md`` is a derived mirror, and if the two disagree the
citizen's own file wins.

Schema decided 2026-07-25 (see PRD section 8): snake_case throughout, numbers
unquoted, a ``kind`` discriminator so agent citizens can share the registry,
and a ``display`` block so appearing on the leaderboard under one's own name
is a choice rather than an assumption.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .config import DEFAULT_CONFIG, VelocityConfig
from .velocity import CodeMetrics, VelocityResult

__all__ = [
    "CITIZENS_DIR",
    "CitizenRecord",
    "Display",
    "citizen_path",
    "load_citizen_history",
    "save_citizen_history",
]

CITIZENS_DIR = Path(".shodann/citizens")

TREND_NEW = "new"
TREND_ASCENDING = "ascending"
TREND_DESCENDING = "descending"
TREND_STABLE = "stable"

KIND_HUMAN = "human"
KIND_AGENT = "agent"

CLEARANCE_NAMES = {
    1: "INFRARED",
    2: "RED",
    3: "ORANGE",
    4: "YELLOW",
    5: "GREEN",
    6: "BLUE+",
}
"""Clearance ladder. Anything above 6 is BLUE+; see design_docs/CLEARANCE_REGISTER.md."""


def clearance_name(level: int) -> str:
    """Name for a clearance level, saturating at BLUE+ rather than failing."""
    return CLEARANCE_NAMES.get(max(1, min(level, 6)), "RED")

VISIBILITY_NAMED = "named"
VISIBILITY_ANONYMOUS = "anonymous"


def _utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Display:
    """Leaderboard participation. Opt-in by name, never by default."""

    visibility: str = VISIBILITY_NAMED
    handle: str | None = None

    def label(self, citizen: str) -> str:
        """What the leaderboard is allowed to print for this citizen."""
        if self.visibility == VISIBILITY_ANONYMOUS:
            return self.handle or "Citizen-Anonymous"
        return f"@{citizen}"


@dataclass
class CitizenRecord:
    citizen: str
    kind: str = KIND_HUMAN
    display: Display = field(default_factory=Display)
    clearance_level: int = 2
    first_submission: str | None = None
    last_updated: str | None = None
    baseline_established: bool = False
    pr_count: int = 0
    iteration_streak: int = 0
    rage_state_encounters: int = 0
    last_metrics: CodeMetrics | None = None
    last_velocity: float = 0.0
    velocity_trend: str = TREND_NEW
    velocity_history: list[dict] = field(default_factory=list)
    last_degradation: str | None = None
    """Why the most recent review went out uninterpreted, or None."""
    coverage_instrumented: bool = False
    """Whether ``last_metrics.coverage`` was measured or is a stand-in zero.

    ``CodeMetrics.coverage`` cannot hold this: it is a float feeding an
    arithmetic engine, and 0.0 there means both *no lines covered* and *nobody
    looked*. Those two need to stay apart in the ledger, because the next
    review subtracts from this number and would otherwise announce a 98-point
    gain to a citizen whose coverage did not move - it was simply measured for
    the first time. Defaults False, so ledgers written before coverage
    instrumentation existed are correctly read as unmeasured.
    """

    # -- serialisation -----------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> CitizenRecord:
        display = data.get("display") or {}
        metrics = data.get("last_metrics")
        return cls(
            citizen=data["citizen"],
            kind=data.get("kind", KIND_HUMAN),
            display=Display(
                visibility=display.get("visibility", VISIBILITY_NAMED),
                handle=display.get("handle"),
            ),
            clearance_level=data.get("clearance_level", 2),
            first_submission=data.get("first_submission"),
            last_updated=data.get("last_updated"),
            baseline_established=data.get("baseline_established", False),
            pr_count=data.get("pr_count", 0),
            iteration_streak=data.get("iteration_streak", 0),
            rage_state_encounters=data.get("rage_state_encounters", 0),
            last_metrics=CodeMetrics.from_dict(metrics) if metrics else None,
            last_velocity=data.get("last_velocity", 0.0),
            velocity_trend=data.get("velocity_trend", TREND_NEW),
            velocity_history=list(data.get("velocity_history", [])),
            last_degradation=data.get("last_degradation"),
            coverage_instrumented=bool(data.get("coverage_instrumented", False)),
        )

    def to_dict(self) -> dict:
        return {
            "citizen": self.citizen,
            "kind": self.kind,
            "display": asdict(self.display),
            "clearance_level": self.clearance_level,
            "first_submission": self.first_submission,
            "last_updated": self.last_updated,
            "baseline_established": self.baseline_established,
            "pr_count": self.pr_count,
            "iteration_streak": self.iteration_streak,
            "rage_state_encounters": self.rage_state_encounters,
            "last_metrics": self.last_metrics.to_dict() if self.last_metrics else None,
            "last_velocity": self.last_velocity,
            "velocity_trend": self.velocity_trend,
            "velocity_history": list(self.velocity_history),
            "last_degradation": self.last_degradation,
            "coverage_instrumented": self.coverage_instrumented,
        }


def citizen_path(citizen: str, root: Path | str = ".") -> Path:
    """Locate a citizen file beneath ``root``.

    ``root`` is explicit because the JS engine resolved its paths against the
    process working directory, which silently wrote state to whatever folder
    the workflow happened to be standing in.
    """
    return Path(root) / CITIZENS_DIR / f"{citizen}.json"


def load_citizen_history(citizen: str, root: Path | str = ".") -> CitizenRecord:
    """Read a citizen's ledger, or return a fresh record if they are new.

    A malformed file is treated as a new citizen rather than an exception:
    PRD section 8 requires state corruption to degrade to a default, not to
    deny a student their feedback.
    """
    path = citizen_path(citizen, root)
    try:
        with path.open(encoding="utf-8") as handle:
            return CitizenRecord.from_dict(json.load(handle))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return CitizenRecord(citizen=citizen)


def compute_trend(history: list[dict]) -> str:
    """Direction over the most recent three scores.

    Returns one of the four values PRD US-3.2 requires. Emoji belong to the
    renderer, not to the ledger.
    """
    if len(history) < 2:
        return TREND_NEW
    recent = [entry["score"] for entry in history[:3]]
    average = sum(recent) / len(recent)
    latest = recent[0]
    if latest > average:
        return TREND_ASCENDING
    if latest < average * 0.8:
        return TREND_DESCENDING
    return TREND_STABLE


def save_citizen_history(
    citizen: str,
    metrics: CodeMetrics,
    result: VelocityResult,
    root: Path | str = ".",
    *,
    config: VelocityConfig = DEFAULT_CONFIG,
    now: str | None = None,
    degradation: str | None = None,
    coverage_instrumented: bool = False,
) -> CitizenRecord:
    """Fold one submission into the citizen's ledger and write it atomically.

    The predecessor wrote ``streak`` and read ``iterationStreak``, so streaks
    silently reset to zero on every run. One name, written and read.
    """
    timestamp = now or _utcnow()
    record = load_citizen_history(citizen, root)

    record.pr_count += 1
    record.last_metrics = metrics
    # Recorded beside the metrics it qualifies. A run whose analysis job died
    # must not leave last cycle's measured reading looking current.
    record.coverage_instrumented = coverage_instrumented
    record.last_velocity = result.score
    record.last_updated = timestamp
    record.baseline_established = True
    # Recorded whether or not it happened, so a cleared degradation does
    # not leave last cycle's reason looking current.
    record.last_degradation = degradation
    if record.first_submission is None:
        record.first_submission = timestamp

    # Streak counts consecutive submissions that kept moving forward.
    record.iteration_streak = record.iteration_streak + 1 if result.score > 0 else 0

    record.velocity_history = [
        {"score": result.score, "date": timestamp},
        *record.velocity_history,
    ][: config.velocity_history_length]
    record.velocity_trend = compute_trend(record.velocity_history)

    path = citizen_path(citizen, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, json.dumps(record.to_dict(), indent=2) + "\n")
    return record


def _atomic_write(path: Path, payload: str) -> None:
    """Write via a temporary file and replace, so a killed job cannot truncate a ledger."""
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    try:
        with handle:
            handle.write(payload)
        os.replace(handle.name, path)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise
