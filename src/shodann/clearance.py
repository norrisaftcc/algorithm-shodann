"""What SHODANN says differently to each band, and why.

The ladder changes posture twice, not once (design_docs/CLEARANCE_REGISTER.md):
it *teaches* from INFRARED to YELLOW, *mentors* at GREEN, and *reports* at
BLUE+. Until now that was decided in two design documents and enforced by the
validator, while the prompt said nothing about it at all - LAYER 3's clearance
slot rendered as an empty string for every citizen.

Worse, the two halves disagreed. The validator swapped `Recommended Iteration`
for `Observations` at BLUE+ while the template kept instructing the old
heading, so a BLUE+ citizen's review was rejected, retried, rejected and
dropped to the fallback every single time.

The fix is not to correct the template. It is to derive the format rules the
prompt states from the same :class:`~shodann.validator.ResponseSpec` the
validator checks, so the two cannot drift apart again.
"""

from __future__ import annotations

from .state import clearance_name
from .validator import ResponseSpec

__all__ = ["ITERATION_GUIDANCE", "clearance_instructions", "iteration_guidance"]

TEACHES = """\
This citizen is building a reference frame and cannot yet calibrate absolute
position, so speak only about movement. Explain one concept at a time with a
concrete example drawn from their own submission. Define any term you
introduce. Do not compare them to anyone."""

MENTORS = """\
This citizen leads work that others depend on. Name the *consequence* rather
than the fix - "this module's complexity is now carried by one person" rather
than "split this function". The recommended step may be delegation,
documentation or a review practice rather than code."""

REPORTS = """\
This citizen may have written the standard you are applying, so do not teach
them their own rules. Report findings and stop. State uncertainty plainly when
two metrics disagree - "these two readings conflict and I cannot tell which is
right" is the most useful sentence available at this band. Drop the
encouragement scaffolding; the vocabulary rules still apply, because they are
the persona rather than a beginner accommodation."""

BANDS = {
    1: (TEACHES, "Keep the next step under 15 minutes."),
    2: (TEACHES, "Keep the next step under 30 minutes."),
    3: (TEACHES, "Keep the next step under 30 minutes."),
    4: (TEACHES, "The next step may take up to an hour."),
    5: (MENTORS, "The next step may take up to an hour."),
    6: (REPORTS, ""),
}

ITERATION_GUIDANCE = {
    "Recommended Iteration": (
        "[ONE specific, actionable thing they can do in their next commit. "
        "{timebox} Frame as \"level up\" not \"fix this\".]"
    ),
    "Observations": (
        "[What you noticed and could not resolve from the data. Phrase as open "
        "questions to a peer, not as assignments. Omit this section entirely "
        "rather than manufacturing an observation.]"
    ),
}


def clearance_instructions(level: int) -> str:
    """The pedagogical guidance injected into LAYER 3 for one band."""
    posture, timebox = BANDS.get(max(1, min(level, 6)), BANDS[2])
    name = clearance_name(level)
    lines = [f"Current band: **{name}**.", "", posture]
    if timebox:
        lines += ["", timebox]
    return "\n".join(lines)


def iteration_guidance(spec: ResponseSpec, level: int) -> str:
    """Bracketed guidance for whichever fourth section this band actually gets."""
    heading = spec.headings[-1] if spec.headings else "Recommended Iteration"
    _, timebox = BANDS.get(max(1, min(level, 6)), BANDS[2])
    template = ITERATION_GUIDANCE.get(heading, ITERATION_GUIDANCE["Recommended Iteration"])
    return template.format(timebox=timebox or "").replace("  ", " ").strip()
