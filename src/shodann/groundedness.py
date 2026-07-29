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
    "clearance_promised_as_earned",
    "constructs_claimed_in_data_files",
    "coverage_kinds_never_measured",
    "ungrounded_attribution",
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


_SCORE_TERMS = (
    "coverage", "lint", "style", "complexity", "docstring", "documentation",
    "test count", "test-count", "iteration", "velocity",
)

_COMPOSITION_NOUNS = ("component", "term", "weight", "weighting", "factor", "multiplier")

_ATTRIBUTION = re.compile(
    r"\b(?:" + "|".join(_SCORE_TERMS) + r")(?:\s+\w+){0,2}?\s+"
    r"(?:" + "|".join(_COMPOSITION_NOUNS) + r")s?\b",
    re.IGNORECASE,
)


def ungrounded_attribution(response: str, prompt: str) -> list[str]:
    """Claims about which part of the score a reading feeds.

    The third probe, and the one the first two were always going to need. The
    percentage probe was written for a review that told a citizen a *style*
    cleanup would get them "back to 98%+ coverage territory" - two unrelated
    instruments joined by an invented mechanism. It catches that sentence
    because of the 98. On 2026-07-29 SHODANN reviewed its own pull request and
    produced the identical fabrication with the number removed:

        "Next iteration could systematically address these, which would further
        increase your velocity score's coverage component"

    said of twenty style diagnostics. Style diagnostics feed the lint term and
    do not touch coverage at all, and three paragraphs later the same comment
    said "raise your velocity score's lint component" about the same suggested
    action - so it contradicted itself about mechanism, inside one review, and
    every existing check passed it. `EARLY_RUNS.md` 16 predicted precisely this:
    the figure probe catches every consequence of the causal error *that carries
    a number*, and prose against the class is unfalsifiable by anything except
    the next run. This is the next run.

    **The rule is grounded in an absence, which is what makes it cheap.** No
    template in `prompts/` names a component, term, weight or multiplier of the
    composite - grep finds zero - so the model is never told the score's
    composition and cannot describe it correctly even by accident. Any such
    claim is therefore ungrounded by construction, and the check needs no model
    of the formula: it needs only to notice that the response is discussing a
    structure it was never shown.

    Checked against the prompt anyway rather than unconditionally, so that
    supplying the composition later turns this off by itself instead of
    becoming a rule nobody can find the reason for.
    """
    found: list[str] = []
    seen: set[str] = set()

    for match in _ATTRIBUTION.findall(_prose(response)):
        phrase = " ".join(match.split())
        lowered = phrase.lower()
        if lowered in seen or lowered in prompt.lower():
            continue
        seen.add(lowered)
        found.append(phrase)
    return found


def check_groundedness(
    response: str, prompt: str, *, blocking_threshold: int = BLOCKING_THRESHOLD
) -> list[Violation]:
    """Report identifiers and figures the model supplied from outside its input."""
    findings = (
        _percentage_findings(response, prompt)
        + _attribution_findings(response, prompt)
        + _construct_findings(response)
        + _clearance_findings(response)
        + _coverage_kind_findings(response, prompt)
    )
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


def _attribution_findings(response: str, prompt: str) -> list[Violation]:
    """Blocking, like the figure probe and for the same reason.

    A citizen sent to fix style diagnostics because it will raise their coverage
    has been sent to do work that cannot succeed - the prompt's own words for
    why an invented cause is worse than no explanation. There is no reading of
    this that helps them, so there is nothing to weigh against blocking, and the
    retry names the violation so the ordinary outcome is the model dropping the
    clause and keeping the advice.
    """
    invented = ungrounded_attribution(response, prompt)
    if not invented:
        return []
    quoted = ", ".join(f'"{phrase}"' for phrase in invented)
    return [
        Violation(
            "ungrounded_attribution",
            BLOCKING,
            f"{quoted} describe(s) the composition of the velocity score, which "
            "no template states and you were never shown. Report what each "
            "reading is; never say which part of a score it feeds, and never "
            "say that acting on one reading will move another.",
            quoted,
        )
    ]


_CODE_CONSTRUCTS = (
    "function", "functions", "class", "classes", "method", "methods",
    "docstring", "docstrings", "variable", "variables", "import", "imports",
)

_NON_CODE_SUFFIX = ("md", "json", "yml", "yaml", "toml", "txt", "cfg", "ini", "lock", "rst")

_CONSTRUCTS = "|".join(_CODE_CONSTRUCTS)
_SUFFIXES = "|".join(_NON_CODE_SUFFIX)

_CONSTRUCT_IN_DATA_FILE = re.compile(
    rf"\b(?:{_CONSTRUCTS})\b(?:\W+\w+){{0,3}}?\W+in\W+(?:the\s+)?([\w./-]+\.(?:{_SUFFIXES}))\b"
    rf"|\b([\w./-]+\.(?:{_SUFFIXES}))(?:\'s|\u2019s)?\s+(?:\w+\s+){{0,2}}?(?:{_CONSTRUCTS})\b",
    re.IGNORECASE,
)


def constructs_claimed_in_data_files(response: str) -> list[str]:
    """Code constructs attributed to a file that cannot contain any.

    The third fabrication class found by reading three consecutive reviews of
    one pull request, and the one most likely to reach a beginner as an
    instruction. SHODANN told the citizen:

        "examining whether your new functions in METRICS.md have narrative
        explanations"

    `METRICS.md` is a generated markdown leaderboard. It has no functions.

    The model had less to go on than that sentence implies, which is the part
    worth recording: template 01 supplies `FILES_CHANGED` as a *count* and no
    file list at all, so the only place the name could have come from is
    `PR_TITLE`. A filename in a title became a file with contents, and then a
    file with functions in it that could be reviewed for docstrings.

    Not reachable by the other probes, and the module docstring predicted the
    shape: "it cannot catch a mislabelled figure... a number that really was in
    the prompt, under the wrong name." Here it is a *filename* that really was
    in the prompt, with invented contents - so `ungrounded_tokens` sees a
    grounded token and passes.

    Checked without reference to the prompt, unlike its siblings. The other two
    probes ask whether a claim was given; this one is false regardless of what
    was given, because a `.md` file has no functions no matter what any template
    says. Narrow on purpose: "describe no file's contents" is the rule and it is
    not mechanically checkable, while this subset is always wrong and costs one
    regex. The general rule is stated in template 01 where the model reads it.
    """
    found: list[str] = []
    seen: set[str] = set()

    for match in _CONSTRUCT_IN_DATA_FILE.finditer(_prose(response)):
        phrase = " ".join(match.group(0).split())
        lowered = phrase.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        found.append(phrase)
    return found


def _construct_findings(response: str) -> list[Violation]:
    """Blocking. There is no version of this a citizen can use.

    A beginner told to add docstrings to the functions in a markdown file will
    open it, find no functions, and conclude they have misunderstood something.
    The retry names the violation and the ordinary outcome is the model keeping
    the advice and dropping the location it invented for it.
    """
    invented = constructs_claimed_in_data_files(response)
    if not invented:
        return []
    quoted = ", ".join(f'"{phrase}"' for phrase in invented)
    return [
        Violation(
            "invented_file_contents",
            BLOCKING,
            f"{quoted} attribute(s) code to a file that contains none. You were "
            "given no file list and no source - only readings, counts and a "
            "title - so you do not know what any file contains. Give the advice "
            "without naming a location for it.",
            quoted,
        )
    ]


_ASCENT = (
    "scale", "scales", "scaling", "rise", "rises", "rising", "climb", "climbs",
    "advance", "advances", "advancing", "progress", "progresses", "earn", "earns",
    "reach", "reaches", "unlock", "unlocks", "promote", "promoted", "promotion",
    "graduate", "graduates", "raise", "raises", "higher", "toward", "towards",
)

_BAND_WORDS = ("clearance", "clearances", "band", "bands")

_ASCENT_RE = "|".join(_ASCENT)
_BANDS_RE = "|".join(_BAND_WORDS)

_EARNED_CLEARANCE = re.compile(
    rf"\b(?:{_ASCENT_RE})\b(?:\W+\w+){{0,5}}?\W+(?:{_BANDS_RE})\b"
    rf"|\b(?:{_BANDS_RE})\b(?:\W+\w+){{0,4}}?\W+(?:{_ASCENT_RE})\b",
    re.IGNORECASE,
)


def clearance_promised_as_earned(response: str) -> list[str]:
    """Claims that a citizen's band can be raised by their work.

    A band is a role assignment. An instructor sets it in
    `.shodann/clearances.json`, no reading is evidence about it, and #59
    *declined* `prompts/03`'s `INFER_CLEARANCE` rather than leaving it
    unimplemented - a band inferred from readings is a second score, and this
    product rests on improvement outranking position. A citizen told that
    iterating well raises their band has been handed that second score by the one
    voice they cannot check it against.

    **This exists because the prose version failed.** `clearance.NOT_EARNED` was
    added at every band on the previous commit, in as many words - "nothing a
    citizen does to their code moves it... never tell a citizen that work of any
    kind will raise their clearance". The next review said "this is how citizens
    scale from ORANGE to higher clearance bands" anyway, with that instruction
    present in the rendered prompt and verified present. EARLY_RUNS 16 states the
    general result and this is a clean instance of it: an instruction against a
    *class* of claim is unfalsifiable by anything except the next run, and it lost
    that run. The prose stays, because it is the right thing to tell a model; the
    probe is what makes it hold.

    **Unconditional, and here the reason is sharper than for its siblings.**
    `ungrounded_attribution` checks against the prompt so that supplying the
    score's composition would retire it. The same design would permanently
    disable this one, because the prompt now contains "will raise their
    clearance" *in order to forbid it* - a prompt-relative check would read its
    own prohibition as a licence. A rule stated in the negative cannot be
    enforced by asking whether the words appear.
    """
    found: list[str] = []
    seen: set[str] = set()

    for match in _EARNED_CLEARANCE.finditer(_prose(response)):
        phrase = " ".join(match.group(0).split())
        lowered = phrase.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        found.append(phrase)
    return found


def _clearance_findings(response: str) -> list[Violation]:
    """Blocking. A false belief about their own standing is the worst of these.

    The other probes send a citizen to do work that cannot succeed. This one
    tells them the course works in a way it does not, in the voice of the system
    that assigns the thing being described, and nothing in their experience will
    correct it.
    """
    invented = clearance_promised_as_earned(response)
    if not invented:
        return []
    quoted = ", ".join(f'"{phrase}"' for phrase in invented)
    return [
        Violation(
            "clearance_as_earned",
            BLOCKING,
            f"{quoted} present(s) a clearance band as something work can raise. "
            "A band is assigned by an instructor and no reading here is evidence "
            "about it. Give the advice on its own merits; never as a step toward "
            "a band.",
            quoted,
        )
    ]


_UNMEASURED_COVERAGE = re.compile(
    r"\b(branch|path|condition|decision|mutation|statement)[\s-]+coverage\b"
    r"|\bcoverage\s+(?:of\s+)?(?:branch|path|condition|decision)e?s?\b",
    re.IGNORECASE,
)


def coverage_kinds_never_measured(response: str, prompt: str) -> list[str]:
    """A kind of coverage the tools did not produce.

    The analyse job runs `pytest --cov=src --cov-report=json` with no
    `--cov-branch`, so the only coverage that exists anywhere in this system is
    **line** coverage. SHODANN told the citizen:

        "maintaining this level while adding 2338 lines means some new code paths
        exist without branch coverage. Next iteration could explore whether any
        of those paths are testable"

    Branch coverage was never measured, so there is no reading to maintain, no
    paths to enumerate, and nothing for the citizen to open. It is entry 19's
    class in a new place - a real word from the prompt attached to a thing the
    prompt does not contain - and the word came from us: the complexity row was
    renamed "Functions over the branch threshold" one commit earlier, putting
    "branch" directly beneath the coverage rows for a model to weld them
    together.

    **The fix is a label, and the freeze is why.** Adding `--cov-branch` would
    make the claim true and is not available: PRD section 8 freezes score inputs
    for cohort 1, coverage is the 2.0-weighted term, and switching line coverage
    for branch coverage *changes* an existing signal rather than adding one. Every
    stored baseline would silently mean something else. So the rows carry their
    unit and the prompt says which kinds do not exist.

    Checked against the prompt so that measuring branch coverage between cohorts
    retires this by itself - and safely, unlike `clearance_promised_as_earned`,
    because the prompt names the forbidden kinds only inside a sentence that also
    names line coverage. A prompt that genuinely reports branch coverage will
    have it in a row.
    """
    haystack = prompt.lower()
    found: list[str] = []
    seen: set[str] = set()

    for match in _UNMEASURED_COVERAGE.finditer(_prose(response)):
        phrase = " ".join(match.group(0).split())
        lowered = phrase.lower()
        if lowered in seen or f"**{lowered}**" in haystack:
            continue
        seen.add(lowered)
        found.append(phrase)
    return found


def _coverage_kind_findings(response: str, prompt: str) -> list[Violation]:
    """Blocking. The citizen is sent to a report that does not exist."""
    invented = coverage_kinds_never_measured(response, prompt)
    if not invented:
        return []
    quoted = ", ".join(f'"{phrase}"' for phrase in invented)
    return [
        Violation(
            "unmeasured_coverage_kind",
            BLOCKING,
            f"{quoted} name(s) a kind of coverage no tool here produced. The only "
            "coverage measured is line coverage, and the word 'branch' in this "
            "prompt belongs to a count of functions. Say line coverage or say "
            "nothing about coverage.",
            quoted,
        )
    ]
