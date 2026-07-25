"""Render velocity results into the DATA layer of SHODANN's prompt.

This module produces *facts for the model to reframe*, never prose for a
student to read. The hard/soft split depends on the model receiving numbers it
cannot invent and being told what they mean.
"""

from __future__ import annotations

from .state import CitizenRecord
from .velocity import VelocityResult

__all__ = ["generate_prompt_section"]

DELTA_GLYPHS = ("\U0001f4c8", "\U0001f4c9", "➡️")


def _glyph(value: float) -> str:
    up, down, flat = DELTA_GLYPHS
    if value > 0:
        return up
    if value < 0:
        return down
    return flat


def generate_prompt_section(result: VelocityResult, record: CitizenRecord | None = None) -> str:
    """Format one velocity result as the prompt's growth-velocity block."""
    lines = [
        "## \U0001f4c8 Growth Velocity Analysis",
        "",
        f"### Velocity Score: {result.score}",
        result.assessment,
        "",
        "### Metric Deltas (change since previous submission)",
    ]

    for key, value in result.deltas.to_dict().items():
        sign = "+" if value > 0 else ""
        lines.append(f"- {key}: {sign}{value} {_glyph(value)}")

    lines += ["", "### \U0001f389 Celebrate these", *[f"- {item}" for item in result.celebrations]]

    if result.opportunities:
        lines += [
            "",
            "### \U0001f4a1 Growth opportunities",
            *[f"- {item}" for item in result.opportunities],
        ]

    if record and record.pr_count > 0:
        lines += [
            "",
            "### Historical context",
            f"- Total submissions: {record.pr_count}",
            f"- Velocity trend: {record.velocity_trend}",
            f"- Iteration streak: {record.iteration_streak}",
        ]

    return "\n".join(lines)
