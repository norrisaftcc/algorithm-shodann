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
    "COVERAGE_REPORT",
    "LINT_REPORT",
    "AnalysisReports",
    "read_coverage",
    "read_lint_issues",
]

COVERAGE_REPORT = "coverage.json"
"""Written by `pytest --cov --cov-report=json`."""

LINT_REPORT = "ruff.json"
"""Written by `ruff check --output-format=json`."""


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
        return cls(
            coverage=coverage,
            lint_issues=read_lint_issues(base / LINT_REPORT),
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
    data = _load(path)
    if isinstance(data, list):
        return len(data)
    # Some ruff versions wrap diagnostics in an object.
    if isinstance(data, dict) and isinstance(data.get("diagnostics"), list):
        return len(data["diagnostics"])
    return None
