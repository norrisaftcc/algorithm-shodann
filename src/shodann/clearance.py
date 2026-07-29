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

__all__ = [
    "DISCLOSURE_BAND",
    "ITERATION_GUIDANCE",
    "clearance_disclosure",
    "clearance_instructions",
    "iteration_guidance",
]

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


NOT_EARNED = (
    "**A band is assigned, never earned.** An instructor sets it in "
    "`.shodann/clearances.json`; nothing a citizen does to their code moves it, "
    "and no reading in this prompt is evidence about it. Never tell a citizen "
    "that work of any kind will raise their clearance, and never frame a "
    "suggestion as a step toward a higher band."
)
"""The rule the templates never stated, and the model twice filled in wrongly.

SHODANN told this citizen that small reversible commits are "how citizens scale
from ORANGE to higher clearance", and separately that a habit "compounds as your
clearance rises". Both invent a promotion mechanism out of nothing: the prompt
supplies a band and instructs the model to calibrate to it, and says nowhere how
a band is obtained.

It is not a small error. Clearance is a role assignment, and #59 *declined*
`prompts/03`'s `INFER_CLEARANCE` sketch rather than leaving it unimplemented,
on the grounds that a band inferred from readings is a second score and this
product rests on improvement outranking position. A citizen told that iterating
well raises their band has been handed exactly that second score - and by the
one voice they have no way to check it against.

Injected at every band rather than written into each posture, because the rule
does not vary and a per-band copy is five places for one answer to drift.
"""


def clearance_instructions(level: int) -> str:
    """The pedagogical guidance injected into LAYER 3 for one band."""
    posture, timebox = BANDS.get(max(1, min(level, 6)), BANDS[2])
    name = clearance_name(level)
    lines = [f"Current band: **{name}**.", "", posture]
    if timebox:
        lines += ["", timebox]
    lines += ["", NOT_EARNED]
    return "\n".join(lines)


DISCLOSURE_BAND = 3
"""ORANGE. Below this, the register exists but is not advertised.

Not a secret - the file is in the citizen's own repository and readable from
the first day. What waits for ORANGE is *being told*, because a beginner
handed a knob for how much explanation they receive will reasonably turn it
down before they know what they are turning down. By ORANGE they do.
"""


DISCLOSURE_ALLOWANCE = 30
"""Words reserved for the footer, out of the budget the output contract caps.

The footer is part of the comment a citizen receives, so it is part of the
budget - appending it after validation would let a review that passed at 400
words post at 447. Reserved up front rather than checked afterwards, because
the alternative is dropping the footer to fit, and a promotion the citizen is
told about only when the model happened to be terse is not a promotion.

`test_clearance.py` asserts the footer stays inside this at every band.
"""


def clearance_disclosure(level: int) -> str:
    """The footer that tells a citizen where their band is set, or nothing.

    Appended rather than requested from the model: it is a fact about the
    system's configuration, and a model asked to reproduce a file path will
    eventually reproduce a slightly wrong one. Its cost is reserved from the
    word budget by the caller - see `DISCLOSURE_ALLOWANCE`.
    """
    if level < DISCLOSURE_BAND:
        return ""
    return (
        "\n\n---\n\n"
        f"*Your clearance is set in `.shodann/clearances.json` - you are currently "
        f"{clearance_name(level)}. It governs how much The Algorithm explains. "
        "See `design_docs/CLEARANCE_REGISTER.md`.*"
    )


def iteration_guidance(spec: ResponseSpec, level: int) -> str:
    """Bracketed guidance for whichever fourth section this band actually gets."""
    heading = spec.headings[-1] if spec.headings else "Recommended Iteration"
    _, timebox = BANDS.get(max(1, min(level, 6)), BANDS[2])
    template = ITERATION_GUIDANCE.get(heading, ITERATION_GUIDANCE["Recommended Iteration"])
    return template.format(timebox=timebox or "").replace("  ", " ").strip()
