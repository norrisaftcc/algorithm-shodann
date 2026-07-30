"""Reading the hard-analysis reports.

Rung 1 counted what could be counted without running anything, because reading
source cannot execute a student's code. Coverage can only be measured by
*running their tests*, which is a different kind of act: it executes untrusted
code, and it must therefore happen somewhere that holds nothing worth stealing.

Nothing in this module runs anything. It reads machine-readable reports that
some other, unprivileged job produced, and it is deliberately incapable of
producing them itself - the separation is the security property, and code that
could shell out to pytest would quietly erode it.

Both readings are optional. An absent report means *not instrumented*, which
is a different thing from zero and is carried through the whole system as
such: the ledger records the gap, the prompt states it, and no model is handed
a zero to celebrate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

__all__ = [
    "COMPLEXITY_RULE",
    "COVERAGE_REPORT",
    "LINT_REPORT",
    "SYNTAX_RULE",
    "TEST_REPORT",
    "AnalysisReports",
    "read_complexity",
    "read_coverage",
    "read_lint_issues",
    "read_style_breakdown",
    "read_syntax_errors",
    "read_test_outcomes",
]

COVERAGE_REPORT = "coverage.json"
"""Written by `pytest --cov --cov-report=json`."""

LINT_REPORT = "ruff.json"
"""Written by `ruff check --output-format=json`."""

TEST_REPORT = "tests.xml"
"""Written by `pytest --junitxml`.

The only machine-readable record pytest keeps of what passed. coverage.py
records lines, not outcomes, so before this file was collected the DATA layer
had no source for a tally at all and substituted zeros - which is how a citizen
with a fully red suite came to be told that nothing had failed.
"""

SYNTAX_RULE = "invalid-syntax"
"""ruff's code for a file it could not parse.

PRD section 8 names `python -m py_compile` for this, and ruff answers the same
question on a pass it is already making over every file, with a pin already
frozen. A second full traversal would buy a second opinion about whether Python
can parse Python.

Not E999: ruff retired that code, and 0.16 reports parse failures under this
name even with `--isolated`. Verified against the pinned version rather than
inferred, because the same assumption about C901's default availability had
already cost one silently-unreachable metric.
"""

COMPLEXITY_RULE = "C901"
"""The one rule whose diagnostics are counted separately from the rest.

PRD section 8 names C901 as SHODANN's complexity metric, replacing radon's
Maintainability Index: "this function has 12 branches" is actionable, "your MI
is 64" reads as a grade. Until this reader existed nothing anywhere consumed a
C901 diagnostic - `collect_metrics` reported a count of `def ` under the name
complexity - so the frozen ruff pin was protecting a number that was never
computed.
"""


@dataclass(frozen=True)
class AnalysisReports:
    """What the unprivileged job managed to measure.

    ``None`` means the tool did not run or its report is unreadable. It never
    means zero - a citizen with no coverage tool and a citizen with no tests
    are in very different situations, and the difference has to survive all
    the way to the sentence a student reads.
    """

    coverage: float | None = None
    lint_issues: int | None = None
    style_breakdown: list[tuple[str, int]] | None = None
    style_fixable: int | None = None
    complexity: int | None = None
    syntax_errors: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None

    @property
    def coverage_instrumented(self) -> bool:
        return self.coverage is not None

    @property
    def tests_instrumented(self) -> bool:
        """Whether anything reported an outcome for this cycle.

        The companion to `coverage_instrumented`, and it exists for the same
        reason: something downstream has to be able to ask "was this measured"
        without inspecting two fields and inventing its own rule for what a
        half-measured run means.
        """
        return self.tests_passed is not None and self.tests_failed is not None

    @classmethod
    def from_directory(cls, directory: Path | str) -> AnalysisReports:
        """Read whichever reports are present in ``directory``."""
        base = Path(directory)
        lint_report = base / LINT_REPORT
        breakdown = read_style_breakdown(lint_report)
        passed, failed = read_test_outcomes(base / TEST_REPORT)
        return cls(
            coverage=read_coverage(base / COVERAGE_REPORT),
            lint_issues=read_lint_issues(lint_report),
            style_breakdown=(breakdown or (None, None))[0],
            style_fixable=(breakdown or (None, None))[1],
            complexity=read_complexity(lint_report),
            syntax_errors=read_syntax_errors(lint_report),
            tests_passed=passed,
            tests_failed=failed,
        )


def _load(path: Path | str):
    """Parse a report, or return ``None`` for anything that goes wrong.

    A malformed report is a missing report. PRD section 8 requires degradation
    rather than refusal, and a citizen should not lose their review because a
    tool wrote truncated JSON.
    """
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def read_coverage(path: Path | str) -> float | None:
    """Percent covered.

    Coverage only. This used to return the test tallies alongside it, reading
    `tests_passed` and `tests_failed` keys out of the coverage report - keys
    coverage.py does not write and nothing in this project ever wrote either,
    so both resolved to `None` on every run there has ever been. Correct
    reader, no producer, and the zeros downstream filled the silence.

    `tests.xml` is the producer now, and it is the only one. Two sources for
    one fact would need a precedence rule, and this codebase already owns one
    undefined precedence rule too many (see RAGE's trigger checks, each of
    which unconditionally overwrites the last).
    """
    data = _load(path)
    if not isinstance(data, dict):
        return None

    totals = data.get("totals")
    percent = totals.get("percent_covered") if isinstance(totals, dict) else None
    if not isinstance(percent, (int, float)):
        return None
    return round(float(percent), 1)


def read_lint_issues(path: Path | str) -> int | None:
    """How many diagnostics ruff emitted.

    Counted rather than categorised on purpose. The velocity engine inverts
    this delta - fewer issues is improvement - and a citizen is told the count
    moved, never which rule they violated. Rule-level feedback belongs in the
    review's prose, where it can be explained.
    """
    diagnostics = _diagnostics(_load(path))
    return None if diagnostics is None else len(diagnostics)


def read_style_breakdown(path: Path | str) -> tuple[list[tuple[str, int]], int] | None:
    """Which rules the diagnostics are, and how many ruff can fix itself.

    `read_lint_issues` above says rule-level feedback "belongs in the review's
    prose, where it can be explained". That was the right destination and nothing
    ever delivered to it: the prose received a bare total, so the model invented
    the missing half. Across five of ten reviews of PR #61 it guessed the
    categories ("likely spacing or naming conventions" - they are `RUF100`,
    `ISC004` and `C408`), guessed the fixable count ("clear the 20 in one pass"
    when ruff reported 11 of 20 fixable), and told the citizen to run a check that
    shows them nothing. S1-45.

    The data was never missing. `ruff.json` carries `code` and `fix` on every
    diagnostic and this module parsed the file to call `len()` on it.

    **Not a score change.** `lint_issues` is a frozen input feeding the sqrt term
    and is untouched; these are descriptive fields beside it, never read by
    `calculate_velocity`. PRD section 8 permits adding a signal and forbids
    changing one, and this does not even add a signal - it adds an explanation of
    one already taken.

    Returns ``(top rules newest-first by frequency, fixable count)``, or ``None``
    when ruff did not run - the same absent-is-not-zero contract as its siblings.
    """
    diagnostics = _diagnostics(_load(path))
    if diagnostics is None:
        return None
    tally: dict[str, int] = {}
    fixable = 0
    for item in diagnostics:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        if isinstance(code, str) and code:
            tally[code] = tally.get(code, 0) + 1
        if item.get("fix"):
            fixable += 1
    ranked = sorted(tally.items(), key=lambda pair: (-pair[1], pair[0]))
    return ranked[:STYLE_RULES_SHOWN], fixable


STYLE_RULES_SHOWN = 4
"""How many rules reach the prompt.

Enough to name a pattern, few enough that the model cannot present the list as
the whole of the citizen's work. The recommended iteration asks for one category;
four gives it something to choose from without turning a review into a report.
"""


def _diagnostics(data) -> list | None:
    """The diagnostic list, whichever shape ruff wrote it in."""
    if isinstance(data, list):
        return data
    # Some ruff versions wrap diagnostics in an object.
    if isinstance(data, dict) and isinstance(data.get("diagnostics"), list):
        return data["diagnostics"]
    return None


def read_complexity(path: Path | str) -> int | None:
    """How many functions ruff found above the branch threshold.

    This is a count of C901 *violations*, not total cyclomatic complexity.
    ruff reports only what breaches `lint.mccabe.max-complexity`, so a
    codebase of well-shaped functions reads 0 - which is the true and useful
    answer, not a missing one. A citizen learns that no function is over the
    line, or exactly how many are.

    It does not feed the velocity score, deliberately. A positive delta here
    means a citizen *added* an over-threshold function, and the growth term
    would have paid them for it; see the note in `velocity.composite_score`.

    ``None`` means ruff did not run or wrote something unreadable, which is
    not the same as a clean codebase and must never be flattened into one.
    """
    return _count_rule(path, COMPLEXITY_RULE)


def read_syntax_errors(path: Path | str) -> int | None:
    """How many files ruff could not parse.

    A measured 0 is the ordinary case and a real answer: every file parses.
    ``None`` means ruff did not run, and the difference matters more here than
    almost anywhere else - "nothing failed to compile" and "nobody checked
    whether anything compiles" are the same sentence to a model that receives
    a bare zero, and only one of them is true.

    These diagnostics are also inside `read_lint_issues`' count, and they stay
    there. That count is a frozen score input; subtracting them would move
    every citizen's `lint_issues` mid-cohort to make one number tidier.
    """
    return _count_rule(path, SYNTAX_RULE)


def _count_rule(path: Path | str, code: str) -> int | None:
    diagnostics = _diagnostics(_load(path))
    if diagnostics is None:
        return None
    return sum(1 for item in diagnostics if isinstance(item, dict) and item.get("code") == code)


_MAX_START_EVENTS = 100
"""How far into the document to look for a `<testsuite>` before giving up."""

_PROLOGUE_BYTES = 4096
"""How much of the head of the file to inspect before handing it to a parser."""

_DECLARATIONS = (b"<!DOCTYPE", b"<!ENTITY", b"<!doctype", b"<!entity")
"""Markup a pytest report never contains, and which an attack needs.

Refused outright rather than left to the parser. `xml.etree` resolves no
external entities and recent CPython caps internal expansion, so a plain
billion-laughs already fails - but "already fails" is a property of the
interpreter this happens to run on, and the review job holds the write token
and the model key. A declaration in a file that is supposed to be pytest's
output is not a thing to parse carefully; it is a thing to refuse.

Belt and braces with the analysis job's `rm -f`, deliberately. That step
deletes anything the citizen shipped, but it runs in the *other* job, and this
one should not depend on another job's hygiene to stay safe.
"""


def read_test_outcomes(path: Path | str) -> tuple[int | None, int | None]:
    """How many tests passed and how many did not, from `pytest --junitxml`.

    Errors count as failures. A test whose fixture blew up never ran, but to
    the citizen reading the review it is the same fact - something is in a
    pre-success state - and splitting the two would put a distinction in front
    of a beginner that changes nothing about what they do next. Skips count as
    neither; a skipped test made no claim either way.

    Parsed by pulling the first `<testsuite>` element's attributes and stopping
    there. `iterparse` rather than `parse` because this file is produced inside
    the citizen's checkout, and reading the whole of an untrusted document to
    look at one element's attributes is more of the document than the question
    needs. `_MAX_START_EVENTS` bounds even that.

    ``(None, None)`` for anything unreadable, the same posture `_load` takes:
    a citizen does not lose their review because a tool wrote truncated XML,
    and an unwritten tally is never reported as a run where nothing failed.
    """
    try:
        with Path(path).open("rb") as handle:
            if any(marker in handle.read(_PROLOGUE_BYTES) for marker in _DECLARATIONS):
                return None, None
            handle.seek(0)
            events = ElementTree.iterparse(handle, events=("start",))  # noqa: S314
            for index, (_, element) in enumerate(events):
                if element.tag == "testsuite":
                    return _tally(element.attrib)
                if index >= _MAX_START_EVENTS:
                    break
    except (OSError, ElementTree.ParseError, ValueError):
        return None, None
    return None, None


def _tally(attributes: dict) -> tuple[int | None, int | None]:
    """Passed and failed, from a `<testsuite>`'s attributes."""
    try:
        total = int(attributes["tests"])
    except (KeyError, TypeError, ValueError):
        return None, None

    def count(name: str) -> int:
        try:
            return max(0, int(attributes.get(name, 0)))
        except (TypeError, ValueError):
            return 0

    failed = count("failures") + count("errors")
    # Floored, because a malformed report must not hand the prompt a negative
    # count of passing tests to phrase as an achievement.
    passed = max(0, total - failed - count("skipped"))
    return passed, failed
