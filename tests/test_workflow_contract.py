"""The workflow is code too, and nothing else in this suite can see it.

Coverage instrumentation shipped, ran green, uploaded an artifact, downloaded
it - and then never told the CLI where it was. The `--reports` flag was
dropped by a silent string replacement, so every reading was discarded at the
last step while every job reported success.

These assertions are crude on purpose. They check that the workflow passes the
arguments the program needs, which is exactly the class of defect that hides
between a green CI run and a wrong number.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "shodann.yml"


@pytest.fixture(scope="module")
def workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_the_workflow_exists(workflow: str) -> None:
    assert "SHODANN Educational Oversight Protocol" in workflow


def test_both_invocations_are_told_where_the_readings_are(workflow: str) -> None:
    """Downloading an artifact and not reading it is worse than not having one."""
    invocations = workflow.count("python -m shodann.review")
    assert invocations == 2, "one review, one record"
    assert workflow.count("--reports shodann-reports") == invocations


def test_the_review_never_writes_state(workflow: str) -> None:
    """A review is not a merge. The ledger is written once, on close."""
    assert "--dry-run" in workflow


def test_the_analysis_job_holds_no_secrets(workflow: str) -> None:
    """The job that runs a citizen's code must not be the job holding the key."""
    analyse = workflow.split("analyse:")[1].split("  review:")[0]

    assert "contents: read" in analyse
    assert "secrets." not in analyse, "a hostile test cannot read a key that is not mapped"
    assert "pytest" in analyse, "and it is the job that runs the tests"


def test_the_review_job_never_runs_citizen_code(workflow: str) -> None:
    review = workflow.split("  review:")[1]

    for runner in ("pytest", "ruff check"):
        assert runner not in review, f"{runner} belongs in the unprivileged job"


# --- the score must not be gameable by the citizen being scored -------------
#
# Both of these are frozen-toolchain items. PRD section 8 freezes the
# measurement set for cohort 1 because changing a measurement resets every
# baseline, so these are free before the first real submission and impossible
# after it. They are asserted here rather than trusted to a comment.


def test_coverage_does_not_instrument_the_citizens_own_tests(workflow: str) -> None:
    """`--cov=.` counts test files in the denominator.

    Test modules run end to end, so they enter the average at ~100% and inflate
    the 2.0-weighted term - the largest in the score. A citizen raises their
    velocity by adding a test file that asserts nothing, which is the
    lines-of-code metric wearing a different unit.
    """
    step = workflow.split("Tests and coverage")[1].split("- name:")[0]
    # Only the executable lines. A comment naming the old flag to explain why
    # it is wrong is documentation, not a defect - the first version of this
    # test failed on its own rationale.
    run = "\n".join(
        line for line in step.splitlines() if line.strip() and not line.strip().startswith("#")
    )

    assert "--cov=." not in run, "the denominator must exclude the citizen's tests"
    assert '"--cov=$COV"' in run
    assert "if [ -d src ]" in run, "a flat-layout submission still gets measured"


def test_the_citizen_does_not_choose_which_lint_rules_count(workflow: str) -> None:
    """Without --isolated, ruff reads config from the repository being analysed.

    The lint delta feeds the velocity score through the sqrt term, so rule
    selection is a score input. A citizen could otherwise raise their own
    velocity by editing their pyproject.toml, and counts would not be
    comparable between citizens.
    """
    style = workflow.split("Style and complexity")[1].split("- name:")[0]

    assert "ruff check" in style
    assert "--isolated" in style, "rule selection is a score input, not a preference"


def test_isolating_ruff_does_not_also_discard_the_complexity_rule(workflow: str) -> None:
    """--isolated throws away our configuration along with the citizen's.

    C901 is not in ruff's default set: run it isolated against a function with
    twelve branches and it reports nothing. So the complexity metric PRD
    section 8 names was unreachable from the moment --isolated shipped,
    whatever this repository's `select` said - and `pyproject.toml` claimed
    the ruff pin was protecting a baseline that nothing computed.
    """
    style = workflow.split("Style and complexity")[1].split("- name:")[0]
    run = "\n".join(
        line for line in style.splitlines() if line.strip() and not line.strip().startswith("#")
    )

    assert "C90" in run, "C901 is the complexity metric; without it nothing is measured"
    assert "max-complexity" in run, "the threshold decides what counts as a violation"


def test_the_complexity_rule_is_added_without_replacing_the_lint_set(workflow: str) -> None:
    """--extend-select, never a bare --select, and the distinction is a rescore.

    `lint_issues` is a frozen score input feeding the sqrt term. Replacing
    ruff's default selection rather than extending it moves that count: on
    this repository an explicit `E4,E7,E9,F,C90` took it from 19 to 0, and the
    full house rule set took it to 492 - mostly S101, one per assert, so every
    citizen who wrote a test would have watched their lint reading get worse.

    Adding a signal is permitted mid-cohort. Changing one is not.
    """
    style = workflow.split("Style and complexity")[1].split("- name:")[0]
    run = "\n".join(
        line for line in style.splitlines() if line.strip() and not line.strip().startswith("#")
    )

    assert "--extend-select" in run, "extending adds C901; selecting would rewrite the lint term"
    assert "--select " not in run, "a bare --select silently rescores every citizen's lint delta"


def test_every_score_feeding_tool_is_pinned_exactly(workflow: str) -> None:
    """An open version bound on a measurement tool is an unannounced rescore.

    The freeze in PRD section 8 is about the numbers, not the source: a
    coverage.py release that changes how partial branches are counted moves
    every citizen's heaviest input with nothing in the diff to show for it.
    ruff carried an exact pin from the start; pytest-cov, which produces the
    2.0-weighted term, ran open beside it.

    pytest is deliberately absent from this list. Test count is counted from
    source in `collect_metrics`, never from a run, so no pytest release can
    move it.
    """
    step = workflow.split("Install the frozen toolchain")[1].split("- name:")[0]
    run = "\n".join(
        line for line in step.splitlines() if line.strip() and not line.strip().startswith("#")
    )

    for tool in ("ruff", "pytest-cov"):
        assert re.search(rf'"{re.escape(tool)}==[0-9]', run), (
            f"{tool} output reaches the velocity score and must carry an exact pin"
        )


def test_the_pinned_versions_match_the_project_metadata(workflow: str) -> None:
    """Two files install the measurement set; they must agree on which one.

    The workflow measures the citizen and `pyproject.toml` builds the
    maintainer's environment. A drift between them means a defect reproduces
    on one and not the other, which is the slowest possible way to find it.
    """
    extras = (WORKFLOW.parent.parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    for tool in ("ruff", "pytest-cov"):
        in_workflow = re.search(rf'"{re.escape(tool)}==([0-9][^"]*)"', workflow)
        in_project = re.search(rf'"{re.escape(tool)}==([0-9][^"]*)"', extras)
        assert in_workflow and in_project, f"{tool} must be pinned in both files"
        assert in_workflow.group(1) == in_project.group(1), f"{tool} pins disagree"


def test_the_fallback_key_reaches_the_step_that_composes(workflow: str) -> None:
    """A fallback nothing maps into the environment is a fallback that never fires.

    This is the defect class `EARLY_RUNS.md` collects: the workflow ran green,
    the code was correct, and the two never agreed about what was passed
    between them. `--reports` was dropped by a silent string replacement the
    same way.
    """
    compose = workflow.split("Compose the review")[1].split("- name:")[0]
    assert "ANTHROPIC_API_KEY" in compose, "the fallback provider needs its key"
    assert "secrets.ANTHROPIC_API_KEY" in compose, "a key is a secret, never a variable"


def test_no_citizen_text_is_interpolated_into_a_shell(workflow: str) -> None:
    """The defect in design_docs/shodann-core.yml:131, asserted against."""
    for field in ("pull_request.title", "pull_request.body"):
        assert f"${{{{ github.event.{field} }}}}" not in workflow


# --- the tallies have a producer, and it survives an edit ------------------


def test_the_suite_writes_a_machine_readable_tally(workflow: str) -> None:
    """S1-07. `pytest -q` prints its tally to a stdout this workflow discards.

    `AnalysisReports` declared `tests_passed` and `tests_failed`, `read_coverage`
    looked for them in a file coverage.py does not write them to, and the
    template had rows for them - a complete reader with no producer anywhere.
    So the DATA layer substituted zeros and a citizen with a red suite was told
    nothing had failed.
    """
    assert "--junitxml=tests.xml" in workflow, "the only tally pytest records to a file"


def test_the_tally_is_handed_to_the_privileged_job(workflow: str) -> None:
    """Writing a report and not uploading it is the same as not writing it."""
    artifact = workflow.split("Hand the readings over")[1].split("  review:")[0]

    for report in ("coverage.json", "ruff.json", "tests.xml"):
        assert report in artifact, f"{report} never leaves the analysis job"


# --- a report is a tool's output, never a repository's content -------------


def test_stale_reports_are_deleted_before_the_tools_run(workflow: str) -> None:
    """A citizen could ship us their own coverage figure, and it counted.

    `> ruff.json` truncates, so ruff was safe. Coverage was not: the step ends
    in `test -f coverage.json || echo '{}'`, a guard for pytest-cov writing
    nothing. Commit a `coverage.json` claiming 97% and break your own test
    collection - pytest-cov writes nothing, the guard finds the committed file
    and leaves it, and it rides the artifact into the 2.0-weighted term.
    Reproduced end to end before this assertion was written.

    Same family as `--isolated` and `--cov=src`: nothing feeding the score may
    be chosen by the citizen being scored.
    """
    analyse = workflow.split("analyse:")[1].split("  review:")[0]
    removal = analyse.index("rm -f")

    for report in ("coverage.json", "ruff.json", "tests.xml"):
        assert report in analyse[removal : removal + 120], f"{report} survives a hostile commit"

    # The invocations, not the install step - `pip install ... pytest` appears
    # first and would make this assertion pass while proving nothing.
    for invocation in ("ruff check . --isolated", 'pytest "--cov=$COV"'):
        assert removal < analyse.index(invocation), (
            "deleting after the tools run protects nothing"
        )
