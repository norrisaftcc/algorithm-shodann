"""Reading the hard-analysis reports.

Absent is not zero, and every test here is about keeping those two apart all
the way from a missing file to the sentence a citizen reads.
"""

from __future__ import annotations

import json

from shodann.analysis import (
    AnalysisReports,
    read_complexity,
    read_coverage,
    read_lint_issues,
)
from shodann.review import collect_metrics


def write(path, payload) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --- coverage -------------------------------------------------------------


def test_coverage_is_read_from_the_report(tmp_path) -> None:
    path = write(tmp_path / "coverage.json", {"totals": {"percent_covered": 87.4321}})
    assert read_coverage(path) == (87.4, None, None)


def test_a_missing_report_is_absent_not_zero(tmp_path) -> None:
    assert read_coverage(tmp_path / "nope.json") == (None, None, None)
    assert not AnalysisReports.from_directory(tmp_path).coverage_instrumented


def test_a_truncated_report_degrades_rather_than_raising(tmp_path) -> None:
    path = tmp_path / "coverage.json"
    path.write_text('{"totals": {"percent_cov', encoding="utf-8")

    assert read_coverage(path) == (None, None, None), "a malformed report is a missing report"


def test_a_report_without_totals_is_absent(tmp_path) -> None:
    """The analysis job writes `{}` when pytest produced nothing at all."""
    path = write(tmp_path / "coverage.json", {})
    assert read_coverage(path) == (None, None, None)


def test_genuine_zero_coverage_is_instrumented(tmp_path) -> None:
    """A citizen with no tests measured at 0% is *not* the same as unmeasured."""
    write(tmp_path / "coverage.json", {"totals": {"percent_covered": 0.0}})
    reports = AnalysisReports.from_directory(tmp_path)

    assert reports.coverage == 0.0
    assert reports.coverage_instrumented, "measured zero is a reading, not a gap"


# --- lint -----------------------------------------------------------------


def test_lint_issues_are_counted(tmp_path) -> None:
    path = write(tmp_path / "ruff.json", [{"code": "E501"}, {"code": "F401"}])
    assert read_lint_issues(path) == 2


def test_a_clean_run_is_zero_not_absent(tmp_path) -> None:
    path = write(tmp_path / "ruff.json", [])
    assert read_lint_issues(path) == 0


def test_a_wrapped_diagnostics_object_is_understood(tmp_path) -> None:
    path = write(tmp_path / "ruff.json", {"diagnostics": [{"code": "E501"}]})
    assert read_lint_issues(path) == 1


def test_a_missing_lint_report_is_absent(tmp_path) -> None:
    assert read_lint_issues(tmp_path / "nope.json") is None


# --- folding into the metrics --------------------------------------------


def test_metrics_use_the_reports_when_they_exist(tmp_path) -> None:
    (tmp_path / "thing.py").write_text("def one():\n    return 1\n", encoding="utf-8")
    write(tmp_path / "coverage.json", {"totals": {"percent_covered": 62.5}})
    write(tmp_path / "ruff.json", [{"code": "E501"}, {"code": "E502"}, {"code": "E503"}])

    metrics = collect_metrics(tmp_path, AnalysisReports.from_directory(tmp_path))

    assert metrics.coverage == 62.5
    assert metrics.lint_issues == 3
    assert metrics.functions == 1, "source counting still happens without running anything"


def test_metrics_without_reports_stay_at_the_rung_one_shape(tmp_path) -> None:
    (tmp_path / "thing.py").write_text("def one():\n    return 1\n", encoding="utf-8")
    metrics = collect_metrics(tmp_path)

    assert metrics.coverage == 0.0
    assert metrics.lint_issues == 0


def test_a_coverage_gain_now_moves_the_velocity_score(tmp_path) -> None:
    """The whole point. Until now every coverage delta was structurally zero."""
    from shodann.velocity import CodeMetrics, calculate_velocity

    previous = CodeMetrics(coverage=30.0, test_count=4)
    current = CodeMetrics(coverage=55.0, test_count=4)

    assert calculate_velocity(current, previous, 1).score > 0
    assert calculate_velocity(current, previous, 1).deltas.coverage == 25.0


# --- complexity, the metric the pin was protecting but nobody computed -----


def diagnostic(code: str) -> dict:
    """One ruff diagnostic, trimmed to the fields anything here reads."""
    return {"code": code, "message": f"{code} happened", "filename": "x.py"}


def test_complexity_counts_only_the_branch_rule(tmp_path) -> None:
    path = write(
        tmp_path / "ruff.json",
        [diagnostic("C901"), diagnostic("E501"), diagnostic("C901"), diagnostic("F401")],
    )
    assert read_complexity(path) == 2
    assert read_lint_issues(path) == 4, "the lint term still counts every diagnostic"


def test_a_clean_report_is_a_measured_zero(tmp_path) -> None:
    """No function over the threshold is the answer, not the absence of one."""
    path = write(tmp_path / "ruff.json", [])
    assert read_complexity(path) == 0


def test_an_absent_report_is_not_a_clean_codebase(tmp_path) -> None:
    assert read_complexity(tmp_path / "nope.json") is None
    assert AnalysisReports.from_directory(tmp_path).complexity is None


def test_a_truncated_lint_report_degrades_rather_than_raising(tmp_path) -> None:
    path = tmp_path / "ruff.json"
    path.write_text('[{"code": "C90', encoding="utf-8")
    assert read_complexity(path) is None


def test_the_wrapped_diagnostics_shape_is_read_too(tmp_path) -> None:
    """Some ruff versions wrap the list in an object; read_lint_issues handles both."""
    path = write(tmp_path / "ruff.json", {"diagnostics": [diagnostic("C901")]})
    assert read_complexity(path) == 1
    assert read_lint_issues(path) == 1


def test_complexity_reaches_the_metrics_from_the_report(tmp_path) -> None:
    """It used to be a count of `def `, which is what `functions` already was."""
    (tmp_path / "thing.py").write_text(
        "def one():\n    return 1\n\n\ndef two():\n    return 2\n", encoding="utf-8"
    )
    write(tmp_path / "ruff.json", [diagnostic("C901"), diagnostic("E501")])

    metrics = collect_metrics(tmp_path, AnalysisReports.from_directory(tmp_path))

    assert metrics.complexity == 1, "one function over the branch threshold"
    assert metrics.functions == 2, "two functions defined"
    assert metrics.complexity != metrics.functions, (
        "these were the same number for as long as nothing measured C901"
    )
