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

    Recursive, and asserted as such. `rm -f` exits 1 on a directory, and a
    citizen can commit one at any of these paths by putting a file inside it -
    which takes the whole analysis job down under `bash -e` and suppresses the
    measurement by a quieter route than faking it. The first version of this
    test keyed on the literal `rm -f`, so hardening the workflow would have
    turned it red while the contract still held.
    """
    analyse = workflow.split("analyse:")[1].split("  review:")[0]
    removal = analyse.index("rm -rf")

    for report in ("coverage.json", "ruff.json", "tests.xml"):
        assert report in analyse[removal : removal + 120], f"{report} survives a hostile commit"

    # The invocations, not the install step - `pip install ... pytest` appears
    # first and would make this assertion pass while proving nothing.
    for invocation in ("ruff check . --isolated", 'pytest "--cov=$COV"'):
        assert removal < analyse.index(invocation), (
            "deleting after the tools run protects nothing"
        )


def test_the_deletion_survives_a_directory_at_the_report_path(workflow: str) -> None:
    """`rm -f` exits 1 on a directory; the step runs under `bash -e`.

    A citizen commits `coverage.json/anything`, the deletion fails, the
    analysis job dies, no artifact is uploaded, and the review reports no
    readings at all. Suppressing a measurement and faking one are the same
    move with different arithmetic, and a citizen whose coverage is falling
    prefers the first.

    Verified both directions in a scratch repository: `rm -f` exits 1 and
    leaves the directory, `rm -rf` exits 0 and removes it.
    """
    analyse = workflow.split("analyse:")[1].split("  review:")[0]

    assert "rm -rf" in analyse
    assert "rm -f coverage.json" not in analyse, "the non-recursive form is the defect"


# --- the ledger records deliveries, and survives losing a race -------------


def _ledger_step(workflow: str) -> str:
    """Everything after the step's own name, so its rationale comment is excluded.

    The comments motivating this step sit above `- name:` and therefore land in
    the *first* half of the split. That matters here for the same reason it
    mattered in `test_coverage_does_not_instrument_the_citizens_own_tests`: a
    comment naming the defect is documentation, and an assertion that reads it
    passes on the prose while the contract is broken.
    """
    return workflow.split("- name: Record the citizen ledger")[1]


def _executable(block: str) -> str:
    return "\n".join(
        line for line in block.splitlines() if line.strip() and not line.strip().startswith("#")
    )


def test_the_ledger_is_only_written_for_a_merge_to_the_default_branch(workflow: str) -> None:
    """S1-38. `merged == true` counts stacked pull requests as deliveries.

    A pull request merged into another feature branch fires an identical
    closed event, and the branch beneath it may never land. #58 merged into
    #56's branch on 2026-07-28 and SHODANN recorded a cycle for it; the live
    ledger reached pr_count 19 and iteration_streak 19 against roughly seven
    merges that actually shipped. Velocity is a rate of shipping, so the base
    ref has to be the branch that ships.

    The comparison is against `github.event.repository.default_branch` and the
    literal 'main' is asserted absent. This file is copied into student
    repositories under the deployment contract, and a hardcoded branch name
    there records nothing at all - a failure that looks exactly like a citizen
    who has not merged yet, which is the quietest way for a ledger to be wrong.
    """
    condition = _ledger_step(workflow).split("env:")[0]

    assert "github.event.pull_request.merged == true" in condition, "still merge-only"
    assert "github.event.pull_request.base.ref == github.event.repository.default_branch" in (
        condition
    ), "a stacked merge is not a delivery"
    assert "'main'" not in condition, "the default branch of a student repository is not ours"


def test_the_ledger_push_rebases_onto_the_fetched_base_and_retries(workflow: str) -> None:
    """S1-18. The concurrency group is per pull request; the push target is not.

    `group: shodann-${{ github.event.pull_request.number }}` serialises runs
    within one pull request and does nothing between two. Two citizens merging
    in the same minute both push a ledger commit to the same default branch and
    the loser is rejected as non-fast-forward - which, under one-repo-per-
    student, is a red X on a student's pull request for a race they cannot see.

    Rebasing onto the freshly fetched tip is what makes the retry meaningful:
    pushing the same rejected commit again three times is not a fix. The push
    must therefore come *after* the fetch and the rebase, which is asserted by
    position rather than by presence - a bare `git push` sitting above an
    unused fetch would satisfy any membership test.
    """
    run = _executable(_ledger_step(workflow))

    assert 'git fetch origin "$GITHUB_BASE_REF"' in run, "the tip has to be re-read to rebase onto"
    assert "git rebase FETCH_HEAD" in run, "a refspec-less fetch may leave origin/<branch> stale"
    assert re.search(r"for attempt in [\d ]+; do", run), "one attempt is not a retry"

    push = run.index('git push origin "HEAD:${GITHUB_BASE_REF}"')
    assert run.index("git rebase FETCH_HEAD") < push, "re-pushing the rejected commit is not a fix"


def test_a_lost_ledger_push_warns_instead_of_failing_the_students_check(workflow: str) -> None:
    """The argument is already made in `_announce_degradation`, src/shodann/review.py.

    Under one-repo-per-student this check appears on the *student's* pull
    request. A red X for our own lost push is a verdict on their submission for
    an infrastructure fault they did not cause, and PRD section 8 says an
    outage of ours must not reflect on a submission. A `::warning::` is visible
    in the Actions tab, where the maintainer is, and invisible as a verdict,
    where the student is. The ledger itself is recoverable: the next merge
    recomputes from the same reports.
    """
    run = _executable(_ledger_step(workflow))

    assert "::warning::" in run, "the maintainer still has to be told"
    assert "exit 1" not in run, "our race is not the citizen's failure"
    assert run.rstrip().endswith("exit 0"), "exhausting the retries must not fail the job"
