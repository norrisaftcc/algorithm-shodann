"""Reading the hard-analysis reports.

Absent is not zero, and every test here is about keeping those two apart all
the way from a missing file to the sentence a citizen reads.
"""

from __future__ import annotations

import json

from shodann.analysis import (
    STYLE_RULES_SHOWN,
    TEST_REPORT,
    AnalysisReports,
    read_complexity,
    read_coverage,
    read_lint_issues,
    read_style_breakdown,
    read_syntax_errors,
    read_test_outcomes,
)
from shodann.review import collect_metrics


def write(path, payload) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --- coverage -------------------------------------------------------------


def test_coverage_is_read_from_the_report(tmp_path) -> None:
    path = write(tmp_path / "coverage.json", {"totals": {"percent_covered": 87.4321}})
    assert read_coverage(path) == 87.4


def test_a_missing_report_is_absent_not_zero(tmp_path) -> None:
    assert read_coverage(tmp_path / "nope.json") is None
    assert not AnalysisReports.from_directory(tmp_path).coverage_instrumented


def test_a_truncated_report_degrades_rather_than_raising(tmp_path) -> None:
    path = tmp_path / "coverage.json"
    path.write_text('{"totals": {"percent_cov', encoding="utf-8")

    assert read_coverage(path) is None, "a malformed report is a missing report"


def test_a_report_without_totals_is_absent(tmp_path) -> None:
    """The analysis job writes `{}` when pytest produced nothing at all."""
    path = write(tmp_path / "coverage.json", {})
    assert read_coverage(path) is None


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


# --- syntax ---------------------------------------------------------------


def test_files_that_do_not_parse_are_counted(tmp_path) -> None:
    path = write(
        tmp_path / "ruff.json",
        [diagnostic("invalid-syntax"), diagnostic("invalid-syntax"), diagnostic("E501")],
    )
    assert read_syntax_errors(path) == 2


def test_a_clean_parse_is_a_measured_zero(tmp_path) -> None:
    path = write(tmp_path / "ruff.json", [diagnostic("E501")])
    assert read_syntax_errors(path) == 0, "every file parsed is an answer, not a gap"


def test_no_ruff_run_is_absent_not_a_clean_parse(tmp_path) -> None:
    """The whole point. "Nothing failed to compile" and "nobody checked" differ."""
    assert read_syntax_errors(tmp_path / "nope.json") is None


def test_syntax_diagnostics_stay_inside_the_frozen_lint_count(tmp_path) -> None:
    """`lint_issues` is a score input; netting the syntax errors out would move it."""
    path = write(tmp_path / "ruff.json", [diagnostic("invalid-syntax"), diagnostic("E501")])
    assert read_lint_issues(path) == 2
    assert read_syntax_errors(path) == 1


# --- test outcomes --------------------------------------------------------


def junit(tmp_path, **attributes) -> str:
    rendered = " ".join(f'{name}="{value}"' for name, value in attributes.items())
    path = tmp_path / TEST_REPORT
    path.write_text(
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<testsuites name="pytest tests"><testsuite name="pytest" {rendered}>'
        f"</testsuite></testsuites>",
        encoding="utf-8",
    )
    return str(path)


def test_a_green_run_reads_as_all_passing(tmp_path) -> None:
    path = junit(tmp_path, errors=0, failures=0, skipped=0, tests=324)
    assert read_test_outcomes(path) == (324, 0)


def test_a_fully_red_suite_is_the_case_this_exists_for(tmp_path) -> None:
    """The defect: a citizen with eleven failures was told nothing had failed."""
    path = junit(tmp_path, errors=0, failures=11, skipped=0, tests=11)
    assert read_test_outcomes(path) == (0, 11)


def test_a_collection_error_counts_as_a_pre_success_state(tmp_path) -> None:
    """A test whose fixture blew up never ran, but the citizen's next move is the same."""
    path = junit(tmp_path, errors=1, failures=1, skipped=1, tests=5)
    assert read_test_outcomes(path) == (2, 2), "pytest itself reports 1 failed, 2 passed"


def test_skips_are_neither_passed_nor_failed(tmp_path) -> None:
    path = junit(tmp_path, errors=0, failures=0, skipped=3, tests=10)
    assert read_test_outcomes(path) == (7, 0)


def test_an_absent_report_is_not_a_run_where_nothing_failed(tmp_path) -> None:
    assert read_test_outcomes(tmp_path / TEST_REPORT) == (None, None)
    assert not AnalysisReports.from_directory(tmp_path).tests_instrumented


def test_a_report_without_a_total_is_absent(tmp_path) -> None:
    path = junit(tmp_path, errors=0, failures=0)
    assert read_test_outcomes(path) == (None, None)


def test_truncated_xml_degrades_rather_than_raising(tmp_path) -> None:
    path = tmp_path / TEST_REPORT
    path.write_text('<testsuites><testsuite tests="4" fail', encoding="utf-8")
    assert read_test_outcomes(path) == (None, None)


def test_a_nonsense_count_never_yields_a_negative_pass_tally(tmp_path) -> None:
    """A floor, so a malformed report cannot hand the prompt "-6 passed" to praise."""
    path = junit(tmp_path, errors=0, failures=9, skipped=0, tests=3)
    passed, failed = read_test_outcomes(path)
    assert (passed, failed) == (0, 9)


def test_a_declaration_is_refused_even_when_the_document_is_otherwise_fine(tmp_path) -> None:
    """A pytest report has no DOCTYPE, so one is a reason to stop reading.

    Written this way after the first version proved nothing. That one fed in a
    billion-laughs and asserted `(None, None)` - which it got with the guard
    *removed*, because CPython's expat caps internal entity expansion on its
    own. A guard whose test passes without it is not a guard, it is a comment.

    So the document here is valid, parseable, and would yield `(7, 2)` from any
    reader that looked. Only the declaration makes it refusable, which means
    deleting the check turns this red.

    The policy is worth having on top of the parser's own limits: "already
    fails" is a property of the interpreter this happens to run on, and the
    job doing the parsing holds the write token and the model key.
    """
    path = tmp_path / TEST_REPORT
    path.write_text(
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE testsuites [<!ENTITY greeting "hello">]>\n'
        '<testsuites><testsuite tests="9" failures="2" errors="0" skipped="0">'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    assert read_test_outcomes(path) == (None, None)


def test_the_tallies_reach_the_reports_object(tmp_path) -> None:
    junit(tmp_path, errors=0, failures=2, skipped=0, tests=9)
    reports = AnalysisReports.from_directory(tmp_path)

    assert (reports.tests_passed, reports.tests_failed) == (7, 2)
    assert reports.tests_instrumented


# --- S1-45: the count was never the only thing in the file ------------------


def test_the_rules_behind_the_style_count_are_read(tmp_path) -> None:
    """S1-45. The prose was handed a total and invented the rest.

    `read_lint_issues` says rule-level feedback "belongs in the review's prose,
    where it can be explained". Nothing ever delivered it, so across five of ten
    reviews of PR #61 the model supplied the missing half itself: guessed
    categories ("likely spacing or naming conventions" - they are RUF100, ISC004
    and C408), a guessed fixable count ("clear the 20 in one pass" against ruff's
    reported 11 of 20), and a command that shows the citizen nothing.

    The data was never missing. `ruff.json` carries `code` and `fix` on every
    diagnostic, and this module parsed the file only to call `len()` on it.
    """
    report = tmp_path / "ruff.json"
    report.write_text(
        json.dumps([
            {"code": "C408", "fix": {"applicability": "safe"}},
            {"code": "C408", "fix": {"applicability": "safe"}},
            {"code": "RUF100", "fix": None},
            {"code": "I001", "fix": {"applicability": "safe"}},
            {"code": "C408", "fix": None},
        ]),
        encoding="utf-8",
    )

    ranked, fixable = read_style_breakdown(report)

    assert ranked[0] == ("C408", 3), "ranked by frequency, not by first appearance"
    assert dict(ranked) == {"C408": 3, "RUF100": 1, "I001": 1}
    assert fixable == 3


def test_the_frozen_lint_count_is_untouched_by_the_breakdown(tmp_path) -> None:
    """The whole legality of this change. `lint_issues` feeds the sqrt term and
    PRD section 8 freezes it for cohort 1; the breakdown is an explanation of a
    reading already taken, never a second reading and never a score input."""
    report = tmp_path / "ruff.json"
    report.write_text(
        json.dumps([{"code": "C408", "fix": None}, {"code": "RUF100", "fix": None}]),
        encoding="utf-8",
    )

    assert read_lint_issues(report) == 2, "the count is still every diagnostic"
    reports = AnalysisReports.from_directory(tmp_path)
    assert reports.lint_issues == 2
    assert reports.style_breakdown == [("C408", 1), ("RUF100", 1)]


def test_an_absent_report_gives_no_breakdown_rather_than_an_empty_one(tmp_path) -> None:
    """Absent is not zero, here too. An empty list would read as 'no rules
    matched', which is a measurement; `None` is 'ruff did not run'."""
    assert read_style_breakdown(tmp_path / "missing.json") is None
    assert AnalysisReports.from_directory(tmp_path).style_breakdown is None


def test_only_a_bounded_number_of_rules_reaches_the_caller(tmp_path) -> None:
    """A review is not a lint report. Four rules name a pattern; twenty would
    turn Growth Opportunities into a transcript and blow the word cap."""
    report = tmp_path / "ruff.json"
    report.write_text(
        json.dumps([{"code": f"X{i:03d}", "fix": None} for i in range(20)]), encoding="utf-8"
    )

    ranked, _ = read_style_breakdown(report)
    assert len(ranked) == STYLE_RULES_SHOWN
