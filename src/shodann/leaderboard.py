"""The METRICS.md leaderboard: a derived mirror, never a source of truth.

Two rules distinguish this from the predecessor, both from decisions recorded
in PRD section 8:

* **every citizen appears.** The JS engine sliced to the top 20, which
  contradicts US-3.2 and quietly deletes exactly the citizens whose growth the
  system exists to notice.
* **naming is opt-in.** Student repositories are public, so a citizen who has
  not chosen to appear by name is rendered under their handle.
"""

from __future__ import annotations

import json
from pathlib import Path

from .state import (
    CITIZENS_DIR,
    KIND_AGENT,
    KIND_HUMAN,
    TREND_ASCENDING,
    TREND_DESCENDING,
    TREND_NEW,
    TREND_STABLE,
    CitizenRecord,
)

__all__ = [
    "AGENT_VIEW_MIN_CLEARANCE",
    "ClearanceRequired",
    "generate_leaderboard",
    "load_all_citizens",
    "may_view",
]


def _board_name(kind: str | None) -> str:
    if kind == KIND_AGENT:
        return "Agent Fleet"
    return "All Citizens" if kind is None else str(kind).title()

TREND_GLYPHS = {
    TREND_ASCENDING: "\U0001f4c8",
    TREND_DESCENDING: "\U0001f4c9",
    TREND_STABLE: "➡️",
    TREND_NEW: "\U0001f195",
}

HEADER = "# \U0001f4ca SHODANN Growth Velocity Leaderboard"
PHILOSOPHY = (
    "This leaderboard measures **improvement**, not absolute skill.\n\n"
    "- **Velocity**: composite of coverage improvement, iteration count and complexity growth\n"
    "- **Trend**: direction across the last three submissions\n"
    "- **Submissions**: total PRs, because consistency matters\n"
    "- **Coverage**: current coverage, shown as context and never as a ranking factor\n\n"
    "*The citizen who grows from 0% to 30% outranks the citizen who stays at 90%.*"
)


def load_all_citizens(root: Path | str = ".") -> list[CitizenRecord]:
    """Read every citizen ledger beneath ``root``, skipping unreadable files."""
    directory = Path(root) / CITIZENS_DIR
    if not directory.is_dir():
        return []

    records = []
    for path in sorted(directory.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as handle:
                records.append(CitizenRecord.from_dict(json.load(handle)))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return records


AGENT_VIEW_MIN_CLEARANCE = 3
"""ORANGE. Below it, a citizen is not shown agent data and is not shown that it exists."""


class ClearanceRequired(PermissionError):
    """A viewer asked for a board their band does not open."""


def may_view(kind: str | None, clearance: int) -> bool:
    """Whether a citizen at ``clearance`` may open a board of ``kind``."""
    return kind == KIND_HUMAN or clearance >= AGENT_VIEW_MIN_CLEARANCE


def generate_leaderboard(
    root: Path | str = ".",
    *,
    kind: str | None = KIND_HUMAN,
    viewer_clearance: int | None = None,
    generated_at: str | None = None,
) -> str:
    """Render one board as markdown.

    Boards partition by ``kind`` - see design_docs/LEADERBOARD.md. A human
    citizen and an agent are in different modes, the way walking and driving
    are different modes: same units, same destination, meaningless comparison.
    Pass ``kind=None`` for the mixed view, which is a specialist instrument
    and never the default.

    Returns the document even when there are no citizens yet - an empty course
    is a valid state, not an error worth exiting on.
    """
    if viewer_clearance is not None and not may_view(kind, viewer_clearance):
        raise ClearanceRequired(
            f"agent data requires clearance {AGENT_VIEW_MIN_CLEARANCE} (ORANGE); "
            f"viewer holds {viewer_clearance}"
        )

    records = load_all_citizens(root)
    if kind is not None:
        # Partition first, then rank. Ranking a mixed list and filtering
        # afterwards produces the right names against the wrong denominator.
        records = [record for record in records if record.kind == kind]
    records.sort(key=lambda record: record.last_velocity, reverse=True)

    lines = [
        HEADER if kind == KIND_HUMAN else f"{HEADER} - {_board_name(kind)}",
        "",
        "> *The Algorithm celebrates those who grow, not those who rest.*",
        "",
    ]
    if kind is None:
        lines += [
            "**Mixed-kind view.** Human citizens and agents appear in one ranking here. "
            "They are not comparable; this board exists for fleet analysis, not for "
            "assessment. See `design_docs/LEADERBOARD.md`.",
            "",
        ]
    if generated_at:
        lines += [f"**Last Updated**: {generated_at}", ""]

    lines += [
        "## \U0001f680 Velocity Rankings",
        "",
        "| Rank | Citizen | Velocity | Trend | Submissions | Coverage |",
        "|------|---------|----------|-------|-------------|----------|",
    ]

    if not records:
        lines.append("| - | *No submissions yet* | - | - | - | - |")

    for rank, record in enumerate(records, start=1):
        coverage = record.last_metrics.coverage if record.last_metrics else 0.0
        glyph = TREND_GLYPHS.get(record.velocity_trend, TREND_GLYPHS[TREND_NEW])
        lines.append(
            f"| {rank} | {record.display.label(record.citizen)} | "
            f"{record.last_velocity:.1f} | {glyph} | {record.pr_count} | {coverage:.0f}% |"
        )

    lines += ["", "---", "", "## \U0001f4c8 Growth Philosophy", "", PHILOSOPHY, ""]
    return "\n".join(lines)
