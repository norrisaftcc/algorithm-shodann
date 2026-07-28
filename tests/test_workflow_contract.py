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


def test_no_citizen_text_is_interpolated_into_a_shell(workflow: str) -> None:
    """The defect in design_docs/shodann-core.yml:131, asserted against."""
    for field in ("pull_request.title", "pull_request.body"):
        assert f"${{{{ github.event.{field} }}}}" not in workflow
