"""What a configured model is allowed to be asked for.

A backend declares the bands and modes it serves, and SHODANN checks before
generating rather than discovering afterwards. Asking a 3B model for the BLUE+
peer register produced two failed attempts and a fallback; asking it to decline
produces the same outcome in one step, with a reason worth recording.

The scope subset is not a degraded product, it is a correctly configured one.
A local model serving INFRARED through ORANGE on Python submissions covers the
bands where the work is *pattern completion over a fixed vocabulary* - one
concept, defined terms, a short timebox, a small budget. That is what small
models are good at, and the 3B trials bear it out: its failures were always
content, never form.

The higher bands ask for something else. GREEN wants consequence-framing;
BLUE+ wants the model to stop teaching and to omit a section when it has
nothing genuine to say. Suppressing a trained behaviour and judging sufficiency
are the two hardest things to get from a small model, and they only appear at
the top of the ladder.

Deliberate refusal beats silent degradation, which is the same rule
`ClearanceRequired` follows on the leaderboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "FULL",
    "LOCAL_SMALL",
    "Capabilities",
    "refusal_reason",
]


@dataclass(frozen=True)
class Capabilities:
    """The envelope a backend declares. Anything outside it is refused, not attempted."""

    name: str
    max_band: int = 6
    modes: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "standard",
                "first_submission",
                "empty_pr",
                "all_failing",
                "massive_pr",
                "syntax_barrier",
                "config_only",
            }
        )
    )

    def serves(self, *, band: int, mode: str) -> bool:
        return band <= self.max_band and mode in self.modes


FULL = Capabilities(name="full")
"""A hosted model of ordinary size. Serves every band and every mode."""

LOCAL_SMALL = Capabilities(
    name="local-small",
    max_band=3,
    modes=frozenset({"standard", "first_submission", "empty_pr", "syntax_barrier"}),
)
"""INFRARED through ORANGE, simple workflows, Python.

Deliberately excludes GREEN and BLUE+, and the edge-case handlers that ask for
judgement about scale or wholesale failure.
"""


def refusal_reason(capabilities: Capabilities, *, band: int, mode: str) -> str | None:
    """Why this request is outside the envelope, or ``None`` if it is inside.

    The string reaches a citizen, so it says what happened without apology and
    without blaming them.
    """
    if capabilities.serves(band=band, mode=mode):
        return None
    if band > capabilities.max_band:
        return (
            f"this allocation serves clearance {capabilities.max_band} and below; "
            f"this submission is clearance {band}"
        )
    return f"this allocation does not serve {mode.replace('_', ' ')} submissions"
