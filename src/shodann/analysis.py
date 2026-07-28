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

__all__ = [
    "COMPLEXITY_RULE",
    "COVERAGE_REPORT",
    "LINT_REPORT",
    "AnalysisReports",
    "read_complexity",
    "read_coverage",
    "read_lint_issues",
]

COVERAGE_REPORT = "coverage.json"
"""Written by `pytest --cov --cov-report=json`."""

LINT_REPORT = "ruff.json"
"""Written by `ruff check --output-format=json`."""

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
    complexity: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None

    @property
    def coverage_instrumented(self) -> bool:
        return self.coverage is not None

    @classmethod
    def from_directory(cls, directory: Path | str) -> AnalysisReports:
        """Read whichever reports are present in ``directory``."""
        base = Path(directory)
        coverage, passed, failed = read_coverage(base / COVERAGE_REPORT)
        lint_report = base / LINT_REPORT
        return cls(
            coverage=coverage,
            lint_issues=read_lint_issues(lint_report),
            complexity=read_complexity(lint_report),
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


def read_coverage(path: Path | str) -> tuple[float | None, int | None, int | None]:
    """Percent covered, and the test tallies if the report carries them."""
    data = _load(path)
    if not isinstance(data, dict):
        return None, None, None

    totals = data.get("totals")
    percent = totals.get("percent_covered") if isinstance(totals, dict) else None
    if not isinstance(percent, (int, float)):
        return None, None, None

    # coverage.py does not record test outcomes; a harness may add them.
    passed = data.get("tests_passed")
    failed = data.get("tests_failed")
    return (
        round(float(percent), 1),
        passed if isinstance(passed, int) else None,
        failed if isinstance(failed, int) else None,
    )


def read_lint_issues(path: Path | str) -> int | None:
    """How many diagnostics ruff emitted.

    Counted rather than categorised on purpose. The velocity engine inverts
    this delta - fewer issues is improvement - and a citizen is told the count
    moved, never which rule they violated. Rule-level feedback belongs in the
    review's prose, where it can be explained.
    """
    diagnostics = _diagnostics(_load(path))
    return None if diagnostics is None else len(diagnostics)


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
    diagnostics = _diagnostics(_load(path))
    if diagnostics is None:
        return None
    return sum(
        1
        for item in diagnostics
        if isinstance(item, dict) and item.get("code") == COMPLEXITY_RULE
    )
