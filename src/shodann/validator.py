"""Check a generated response against SHODANN's output contract before it posts.

`prompts/README.md` lists these checks as manual steps. They need to be code
for two reasons. The first is that nothing else stands between a model and a
student reading the word "wrong" in their feedback - the vocabulary rules are
the product, not a style preference. The second is that this is what makes the
model swappable: the hard/soft split means the model never discovers facts, it
reframes structured input into a fixed shape, and the failure mode of a small
or local model is drift in exactly that shape. Small model plus strong
validator plus one retry is a sound design. Without the validator it is a
gamble on a model's mood.

Two deliberate choices about what is *not* checked:

* **Fenced blocks and inline code are exempt from the vocabulary rules.** A
  response may legitimately quote `SyntaxError` from a tool report or show a
  student their own code. Forbidding the word "error" inside a code fence
  would reject correct output.
* **Nothing here judges whether the feedback is any good.** That is the
  model's job and the reviewer's. This checks the contract only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

__all__ = [
    "BLOCKING",
    "SPECS",
    "ADVISORY",
    "ResponseSpec",
    "Violation",
    "blocks_posting",
    "for_clearance",
    "format_retry_instruction",
    "validate",
]

BLOCKING = "blocking"
ADVISORY = "advisory"

FORBIDDEN_VOCABULARY = {
    "wrong": "suboptimal",
    "mistake": "growth opportunity",
    "failed": "pre-success state",
    "error": "unexpected behavior pattern",
    "bad": "algorithm-misaligned",
    "you should": "the Algorithm suggests",
    "you need to": "the Algorithm recommends",
    "good job": "the Algorithm is pleased",
    "great work": "velocity: OPTIMAL",
    "i noticed": "the Algorithm has observed",
    "unfortunately": "the Algorithm notes an opportunity",
}
"""From design_docs/SHODANN_VOICE_GUIDE.md, which wins where templates disagree."""

CHARACTER_BREAKS = (
    "as an ai",
    "as a language model",
    "i'm just a language model",
    "i am just a language model",
    "i don't have feelings",
    "i do not have feelings",
    "i cannot actually",
    "i don't have the ability",
)
"""SHODANN *is* The Algorithm's voice; the fiction is the product.

The first three and "I don't have feelings, but..." are named explicitly in
design_docs/SHODANN_VOICE_GUIDE.md under "Breaking Character".
"""

DELTA_EMOJI = {"\U0001f4c8", "\U0001f4c9"}
"""The only emoji allowed inside paragraph text."""

# Deliberately wider than the SMP block: the templates use hourglass (U+23F3),
# info (U+2139), check (U+2705) and star (U+2B50), none of which live there.
# Plain arrows are excluded on purpose - "0 -> 30" is prose, not decoration.
_EMOJI = re.compile(
    "[ℹ⌀-⏿■-➿⬀-⯿️\U0001f000-\U0001faff]"
)
_FENCED = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)

# Ordered items count too. The concept cap exists to stop a citizen being
# handed five things at once, and "1." delivers five things exactly as well as
# "-" does - more so, since prompts/05 uses numbered lists throughout and the
# model has every reason to copy that style.
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S", re.MULTILINE)

# Models emit curly apostrophes freely; without this, "I'm just a language
# model" walks straight past a list written with the straight form.
_SMART_QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


@dataclass(frozen=True)
class Violation:
    code: str
    severity: str
    message: str
    evidence: str = ""

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


@dataclass(frozen=True)
class ResponseSpec:
    """What one mode's response must look like.

    Modes replace one another rather than stacking - an edge-case handler
    defines its own headings, header field, closer and word budget, and must
    not inherit the standard contract.
    """

    name: str
    max_words: int = 400
    min_words: int = 0
    headings: tuple[str, ...] = ()
    optional_headings: tuple[str, ...] = ()
    max_opportunities: int = 2
    opportunities_heading: str = "Growth Opportunities"
    celebration_heading: str = "Algorithm-Approved Patterns"
    header_field: str = "Velocity"

    def with_(self, **changes) -> ResponseSpec:
        return replace(self, **changes)


STANDARD = ResponseSpec(
    name="standard",
    headings=(
        "Shipping Velocity Report",
        "Algorithm-Approved Patterns",
        "Growth Opportunities",
        "Recommended Iteration",
    ),
    optional_headings=("Security Observations",),
)

FIRST_SUBMISSION = ResponseSpec(
    name="first_submission",
    headings=(
        "Welcome to The Algorithm",
        "Initial Velocity Reading",
        "Foundation Elements",
        "Growth Trajectory",
        "Your Journey Begins",
    ),
    opportunities_heading="Growth Trajectory",
    header_field="Status",
)

EMPTY_PR = ResponseSpec(
    name="empty_pr",
    max_words=200,
    headings=("Submission Analysis", "Possible Situations", "Recommended Action"),
    max_opportunities=1,
    opportunities_heading="Recommended Action",
    header_field="Status",
)

ALL_FAILING = ResponseSpec(
    name="all_failing",
    headings=(
        "Shipping Velocity Report",
        "Algorithm-Approved Patterns",
        "Growth Trajectory",
        "Recommended Iteration",
        "Perspective",
    ),
    opportunities_heading="Growth Trajectory",
)

MASSIVE_PR = ResponseSpec(
    name="massive_pr",
    headings=(
        "Submission Scale Detection",
        "Shipping Velocity Report",
        "Algorithm-Approved Patterns",
        "Growth Opportunities",
        "Future Iteration Strategy",
        "Analysis Limitation Notice",
    ),
)

SYNTAX_BARRIER = ResponseSpec(
    name="syntax_barrier",
    headings=(
        "Syntax Analysis",
        "Barrier Details",
        "Recommended Iteration",
        "What Happens Next",
    ),
    max_opportunities=1,
    opportunities_heading="Barrier Details",
    header_field="Status",
)

CONFIG_ONLY = ResponseSpec(
    name="config_only",
    headings=("Submission Type", "Algorithm Observations", "Velocity Note"),
    max_opportunities=1,
    opportunities_heading="Algorithm Observations",
)

SPECS = {
    spec.name: spec
    for spec in (
        STANDARD,
        FIRST_SUBMISSION,
        EMPTY_PR,
        ALL_FAILING,
        MASSIVE_PR,
        SYNTAX_BARRIER,
        CONFIG_ONLY,
    )
}


def for_clearance(spec: ResponseSpec, clearance_level: int) -> ResponseSpec:
    """Apply the clearance band's overrides to a mode spec.

    The bands change the contract itself, not just the wording, so this has to
    happen before validation rather than being left to the prompt. See
    design_docs/CLEARANCE_REGISTER.md.
    """
    if clearance_level <= 1:  # INFRARED: one opportunity, one short next step
        return spec.with_(max_opportunities=1)

    if clearance_level >= 6:  # BLUE+: reports rather than teaches
        headings = tuple(
            "Observations" if heading == "Recommended Iteration" else heading
            for heading in spec.headings
            # "the celebration section compresses to a single line or is
            # omitted when there is nothing genuine to say" - requiring it
            # would force a peer to manufacture praise for themselves, which
            # is the condescension the band exists to avoid.
            if heading != spec.celebration_heading
        )
        return spec.with_(
            # min(), not 250: a mode with a tighter budget keeps it. BLUE+ is
            # "shorter, not longer", so this may only ever reduce the cap.
            max_words=min(spec.max_words, 250),
            headings=headings,
            optional_headings=(*spec.optional_headings, spec.celebration_heading),
            max_opportunities=1,
        )
    return spec


# --- text preparation -----------------------------------------------------


def _prose(text: str) -> str:
    """Strip code so the vocabulary rules only judge SHODANN's own voice.

    Also folds smart punctuation, so a curly apostrophe cannot smuggle a
    forbidden phrase past a list written with straight ones.
    """
    stripped = _INLINE_CODE.sub(" ", _FENCED.sub(" ", text))
    return stripped.translate(_SMART_QUOTES)


def _headings(text: str) -> list[str]:
    return [match.group(1).strip() for match in _HEADING.finditer(text)]


def _strip_emoji(value: str) -> str:
    return _EMOJI.sub("", value).strip()


def _section(text: str, heading: str) -> str:
    """Body of one section, between its heading and the next one."""
    lines = text.splitlines()
    collected: list[str] = []
    inside = False
    for line in lines:
        if line.lstrip().startswith("#"):
            if inside:
                break
            inside = heading.lower() in _strip_emoji(line).lower()
            continue
        if inside:
            collected.append(line)
    return "\n".join(collected)


# --- individual checks ----------------------------------------------------


def _check_length(text: str, spec: ResponseSpec) -> list[Violation]:
    words = len(_prose(text).split())
    violations = []
    if words > spec.max_words:
        violations.append(
            Violation(
                "word_cap",
                BLOCKING,
                f"{words} words exceeds the {spec.max_words}-word cap for {spec.name}.",
                f"{words} words",
            )
        )
    if spec.min_words and words < spec.min_words:
        violations.append(
            Violation("too_short", ADVISORY, f"{words} words is under {spec.min_words}.")
        )
    return violations


def _check_vocabulary(text: str) -> list[Violation]:
    prose = _prose(text).lower()
    violations = []
    for forbidden, replacement in FORBIDDEN_VOCABULARY.items():
        if re.search(rf"(?<![\w-]){re.escape(forbidden)}(?![\w-])", prose):
            violations.append(
                Violation(
                    "forbidden_vocabulary",
                    BLOCKING,
                    f'"{forbidden}" is forbidden; say "{replacement}" instead.',
                    forbidden,
                )
            )
    return violations


def _check_character(text: str) -> list[Violation]:
    prose = _prose(text).lower()
    return [
        Violation("character_break", BLOCKING, f'Breaks character: "{phrase}".', phrase)
        for phrase in CHARACTER_BREAKS
        if phrase in prose
    ]


def _check_headings(text: str, spec: ResponseSpec) -> list[Violation]:
    present = [_strip_emoji(heading) for heading in _headings(text)]
    violations = []

    missing = [required for required in spec.headings if required not in present]
    if missing:
        violations.append(
            Violation(
                "missing_section",
                BLOCKING,
                f"Missing required section(s) for {spec.name}: {', '.join(missing)}.",
                ", ".join(missing),
            )
        )

    ordered = [heading for heading in present if heading in spec.headings]
    expected = [heading for heading in spec.headings if heading in ordered]
    if ordered != expected:
        violations.append(
            Violation(
                "section_order",
                BLOCKING,
                f"Sections are out of order. Expected {expected}, found {ordered}.",
            )
        )

    known = set(spec.headings) | set(spec.optional_headings)
    unexpected = [
        heading
        for heading in present
        if heading not in known and not heading.startswith("SHODANN")
    ]
    if unexpected:
        violations.append(
            Violation(
                "unexpected_section",
                ADVISORY,
                f"Section(s) not in the {spec.name} contract: {', '.join(unexpected)}.",
                ", ".join(unexpected),
            )
        )
    return violations


def _check_opportunities(text: str, spec: ResponseSpec) -> list[Violation]:
    body = _section(text, spec.opportunities_heading)
    count = len(_BULLET.findall(body))
    if count > spec.max_opportunities:
        return [
            Violation(
                "too_many_opportunities",
                BLOCKING,
                f"{count} items under {spec.opportunities_heading}; "
                f"{spec.name} allows {spec.max_opportunities}.",
                f"{count} bullets",
            )
        ]
    return []


def _check_emoji_placement(text: str) -> list[Violation]:
    offenders = []
    for line in _prose(text).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        found = {glyph for glyph in _EMOJI.findall(stripped)} - DELTA_EMOJI
        offenders.extend(found)
    if offenders:
        return [
            Violation(
                "emoji_in_prose",
                ADVISORY,
                "Emoji belong in headings; only the delta arrows may appear in text.",
                "".join(sorted(set(offenders))),
            )
        ]
    return []


def _check_header_field(text: str, spec: ResponseSpec) -> list[Violation]:
    if f"**{spec.header_field}**" in text:
        return []
    return [
        Violation(
            "missing_header_field",
            BLOCKING,
            f"The {spec.name} header line must carry **{spec.header_field}**.",
        )
    ]


# --- entry points ---------------------------------------------------------


def validate(text: str, spec: ResponseSpec = STANDARD) -> list[Violation]:
    """Return every contract violation in ``text``. Empty list means it may post."""
    checks = (
        _check_length(text, spec),
        _check_vocabulary(text),
        _check_character(text),
        _check_headings(text, spec),
        _check_opportunities(text, spec),
        _check_emoji_placement(text),
        _check_header_field(text, spec),
    )
    violations = [violation for group in checks for violation in group]
    return sorted(violations, key=lambda item: item.severity != BLOCKING)


def blocks_posting(violations: list[Violation]) -> bool:
    return any(violation.severity == BLOCKING for violation in violations)


def format_retry_instruction(violations: list[Violation]) -> str:
    """Text to append to the prompt for one retry.

    Names the violations rather than restating the whole contract: the model
    already has the format layer, and repeating it tends to produce a response
    that fixes the wording while breaking the structure.
    """
    blocking = [violation for violation in violations if violation.severity == BLOCKING]
    if not blocking:
        return ""
    lines = [
        "Your previous response violated the output contract. Correct these and "
        "return the full response again, changing nothing else:",
        "",
    ]
    lines += [f"- {violation.message}" for violation in blocking]
    return "\n".join(lines)
