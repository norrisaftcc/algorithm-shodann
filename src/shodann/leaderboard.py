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
    TREND_ASCENDING,
    TREND_DESCENDING,
    TREND_NEW,
    TREND_STABLE,
    CitizenRecord,
)

__all__ = ["generate_leaderboard", "load_all_citizens"]

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


def generate_leaderboard(root: Path | str = ".", *, generated_at: str | None = None) -> str:
    """Render the full leaderboard as markdown.

    Returns the document even when there are no citizens yet - an empty course
    is a valid state, not an error worth exiting on.
    """
    records = load_all_citizens(root)
    records.sort(key=lambda record: record.last_velocity, reverse=True)

    lines = [
        HEADER,
        "",
        "> *The Algorithm celebrates those who grow, not those who rest.*",
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
