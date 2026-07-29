"""Did the model talk about things it was actually shown?

The validator checks structure, vocabulary and length. It has no view of
truth, and cannot acquire one by being made stricter. A 3B model produced a
review with zero contract violations that told a citizen their coverage had
improved "from 0% to 218 complexity", and praised their use of `df` instead of
`dataFrame` in code it had never seen.

This is the cheap check that catches that class of thing: every identifier the
response quotes is compared against the prompt it was given. A token the model
produced that appears nowhere in its input is a token it supplied from
somewhere other than the submission.

**It is a probe, not a proof**, and it is honest about three limits:

* A *suggested* identifier is legitimately new. "Consider naming it
  ``user_age``" is good advice, not a fabrication. That is why one or two
  ungrounded tokens are advisory and only a pattern of them blocks.
* Fenced code is excluded. An example is new text by nature.
* It cannot catch a **mislabelled** figure. "218 complexity" reported as
  coverage uses a number that really was in the prompt, under the wrong name.
  Nothing here sees that.

What it does catch, reliably and for three lines of regex, is a model
inventing filenames, variables and APIs for a codebase it was never shown.
"""

from __future__ import annotations

import re

from .validator import ADVISORY, BLOCKING, Violation

__all__ = [
    "BLOCKING_THRESHOLD",
    "check_groundedness",
    "ungrounded_percentages",
    "ungrounded_tokens",
]

BLOCKING_THRESHOLD = 3
"""One or two novel identifiers read as suggestions. Three is a pattern."""

MIN_LENGTH = 2

_FENCED = re.compile(r"```.*?```", re.DOTALL)
_BACKTICKED = re.compile(r"`([^`\n]{2,60})`")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-/]*")

IGNORED = frozenset(
    {
        # Bare language and tooling nouns carry no claim about this submission.
        "python", "pytest", "ruff", "git", "github", "json", "yaml", "true",
        "false", "none", "null", "def", "class", "import", "return", "self",
        "test", "tests", "src", "main", "todo", "print", "assert",
    }
)


def _prose(text: str) -> str:
    """Response text with fenced examples removed."""
    return _FENCED.sub(" ", text)


def ungrounded_tokens(response: str, prompt: str) -> list[str]:
    """Identifiers the response quotes that appear nowhere in the prompt.

    Order is preserved and duplicates collapse, so the report reads in the
    order a citizen would encounter the claims.
    """
    haystack = prompt.lower()
    found: list[str] = []
    seen: set[str] = set()

    for quoted in _BACKTICKED.findall(_prose(response)):
        for token in _WORD.findall(quoted):
            cleaned = token.strip(".-/")
            lowered = cleaned.lower()
            if (
                len(cleaned) <= MIN_LENGTH
                or lowered in IGNORED
                or lowered in seen
                or lowered in haystack
            ):
                continue
            seen.add(lowered)
            found.append(cleaned)
    return found


_PERCENTAGE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")

ROUNDING_TOLERANCE = 0.05
"""How close a quoted figure must be to a real one to count as the same figure."""


def ungrounded_percentages(response: str, prompt: str) -> list[str]:
    """Percentages the response states that the prompt never contained.

    The one class of fabrication this file said it could not catch. Its own
    docstring named the limit - "it cannot catch a mislabelled figure" - and
    then the second synthesised review produced one in the section a citizen
    is most likely to act on:

        "gets you back to 98%+ coverage territory"

    said of a *style* cleanup, to a citizen whose coverage read 97.5% and had
    never been above 97.9%. Style diagnostics and coverage are unrelated
    instruments, so the sentence invented both a figure and a mechanism, and
    the identifier probe saw nothing because no identifier was quoted.

    A percentage is the unit this product is most about, and unlike an
    identifier it is never legitimately a *suggestion*: "consider naming it
    `user_age`" is good advice, and "this will get you to 98%" is a
    prediction the tools did not make.

    Rounding is allowed. A model writing 97% for a measured 97.5% is being
    readable, not inventive, so a figure matching the integer part of a real
    one passes. 98 against 97.5 does not, which is the case that mattered.
    """
    real = [float(value) for value in _PERCENTAGE.findall(prompt)]
    found: list[str] = []
    seen: set[str] = set()

    for quoted in _PERCENTAGE.findall(_prose(response)):
        value = float(quoted)
        if quoted in seen:
            continue
        grounded = any(
            abs(value - candidate) < ROUNDING_TOLERANCE or int(value) == int(candidate)
            for candidate in real
        )
        if not grounded:
            seen.add(quoted)
            found.append(f"{quoted}%")
    return found


def check_groundedness(
    response: str, prompt: str, *, blocking_threshold: int = BLOCKING_THRESHOLD
) -> list[Violation]:
    """Report identifiers and figures the model supplied from outside its input."""
    findings = _percentage_findings(response, prompt)
    invented = ungrounded_tokens(response, prompt)
    if not invented:
        return findings

    quoted = ", ".join(f"`{token}`" for token in invented)
    severity = BLOCKING if len(invented) >= blocking_threshold else ADVISORY
    detail = (
        "Refer only to what the submission data shows."
        if severity == BLOCKING
        else "Acceptable as a suggestion; not acceptable as a claim about their code."
    )
    return [
        *findings,
        Violation(
            "ungrounded_reference",
            severity,
            f"{len(invented)} identifier(s) not present in the submission data: "
            f"{quoted}. {detail}",
            quoted,
        ),
    ]


def _percentage_findings(response: str, prompt: str) -> list[Violation]:
    """Blocking from the first one, unlike the identifier probe.

    One novel identifier is a suggestion and blocking on it would reject good
    advice. One novel percentage is a measurement nobody took, and there is no
    reading of it that helps a citizen. The retry names the violation, so the
    ordinary outcome is the model dropping a claim it should not have made -
    and if it fails twice the citizen gets MINIMAL RESPONSE, which carries the
    real figures and simply does not interpret them.
    """
    invented = ungrounded_percentages(response, prompt)
    if not invented:
        return []
    return [
        Violation(
            "ungrounded_figure",
            BLOCKING,
            f"{', '.join(invented)} appear(s) in no tool report. State measured "
            "figures only; never predict one, and never imply a figure the "
            "instruments did not produce.",
            ", ".join(invented),
        )
    ]
