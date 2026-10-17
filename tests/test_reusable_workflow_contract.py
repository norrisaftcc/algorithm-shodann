"""The reusable workflow, the subscriber template, and the self-review workflow agree.

`shodann.yml` reviews this repository, where the thing under review IS the
engine and `pip install .` is right. `shodann-review.yml` reviews somebody
else's repository, and every property below is what stops that from becoming
"install the student's code next to the write token".

Same style as `test_workflow_contract.py`: the YAML is read as text, because the
defects that matter live between a green CI run and a wrong number. The shared
half is parametrised over BOTH workflows rather than copied, so the frozen
measurement set cannot drift between the door this repository uses and the door
a subscriber uses. Nothing in `test_workflow_contract.py` is weakened or moved.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SELF_REVIEW = ROOT / ".github" / "workflows" / "shodann.yml"
REUSABLE = ROOT / ".github" / "workflows" / "shodann-review.yml"
TEMPLATE = ROOT / "templates" / "subscriber" / "shodann.yml"
SRC = ROOT / "src" / "shodann"

BOTH = [SELF_REVIEW, REUSABLE]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _executable(block: str) -> str:
    """Drop comment lines. A comment naming a defect is documentation, not the defect."""
    return "\n".join(
        line for line in block.splitlines() if line.strip() and not line.strip().startswith("#")
    )


def _job(workflow: str, name: str) -> str:
    """The text of one top-level job, from its `  name:` line to the next job."""
    jobs = workflow.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([A-Za-z][\w-]*):[ \t]*$", jobs, flags=re.MULTILINE)
    # re.split with one group yields [preamble, name1, body1, name2, body2, ...]
    bodies = dict(zip(parts[1::2], parts[2::2], strict=True))
    assert name in bodies, f"job {name!r} not found; have {sorted(bodies)}"
    return bodies[name]


def _step(workflow: str, name: str) -> str:
    """One step, from its `- name:` line to the next step or job.

    Comment lines that precede the *next* step land at the tail of this one, so
    callers that assert on content read `_executable(...)` of the result.
    """
    marker = f"- name: {name}"
    assert workflow.count(marker) == 1, f"expected exactly one step named {name!r}"
    tail = workflow.split(marker, 1)[1]
    return re.split(r"^      - name:|^  [A-Za-z][\w-]*:[ \t]*$", tail, maxsplit=1, flags=re.M)[0]


@pytest.fixture(params=BOTH, ids=lambda p: p.name)
def workflow(request: pytest.FixtureRequest) -> str:
    return _read(request.param)


@pytest.fixture(scope="module")
def reusable() -> str:
    return _read(REUSABLE)


@pytest.fixture(scope="module")
def self_review() -> str:
    return _read(SELF_REVIEW)


@pytest.fixture(scope="module")
def template() -> str:
    return _read(TEMPLATE)


def test_the_files_under_test_exist() -> None:
    """A parametrised fixture over a missing file errors at collection, not here."""
    assert len(BOTH) == 2
    for path in (*BOTH, TEMPLATE):
        assert path.is_file(), f"{path} is missing"


# --- the shared half: both doors must measure identically -------------------


def test_the_job_split_holds(workflow: str) -> None:
    """The job that runs a citizen's code holds no secret; the one with the key runs none."""
    analyse = _executable(_job(workflow, "analyse"))
    review = _executable(_job(workflow, "review"))

    assert "contents: read" in analyse
    assert "secrets." not in analyse, "a hostile test cannot read a key that is not mapped"
    assert "pytest" in analyse
    for runner in ("pytest", "ruff check"):
        assert runner not in review, f"{runner} belongs in the unprivileged job"


def test_coverage_excludes_the_citizens_own_tests(workflow: str) -> None:
    run = _executable(_step(workflow, "Tests and coverage"))

    assert "--cov=." not in run
    assert '"--cov=$COV"' in run
    assert "if [ -d src ]" in run


def test_the_citizen_does_not_choose_the_lint_rules(workflow: str) -> None:
    run = _executable(_step(workflow, "Style and complexity"))

    assert "ruff check" in run
    assert "--isolated" in run
    assert "--extend-select" in run and "C90" in run
    assert "max-complexity" in run
    assert "--select " not in run, "a bare --select rescores every citizen's lint delta"


def test_every_score_feeding_tool_is_pinned_exactly(workflow: str) -> None:
    run = _executable(_step(workflow, "Install the frozen toolchain"))
    project = _read(ROOT / "pyproject.toml")

    for tool in ("ruff", "pytest-cov"):
        in_workflow = re.search(rf'"{re.escape(tool)}==([0-9][^"]*)"', run)
        in_project = re.search(rf'"{re.escape(tool)}==([0-9][^"]*)"', project)
        assert in_workflow and in_project, f"{tool} must be pinned in both files"
        assert in_workflow.group(1) == in_project.group(1), f"{tool} pins disagree"


def test_the_tally_is_written_and_handed_over(workflow: str) -> None:
    assert "--junitxml=tests.xml" in workflow
    artifact = _executable(_step(workflow, "Hand the readings over"))
    for report in ("coverage.json", "ruff.json", "tests.xml"):
        assert report in artifact, f"{report} never leaves the analysis job"


def test_stale_reports_are_deleted_before_any_tool_runs(workflow: str) -> None:
    analyse = _executable(_job(workflow, "analyse"))

    assert "rm -rf" in analyse, "rm -f exits 1 on a directory under bash -e"
    assert "rm -f coverage.json" not in analyse
    removal = analyse.index("rm -rf")
    for report in ("coverage.json", "ruff.json", "tests.xml"):
        assert report in analyse[removal : removal + 120]
    for invocation in ("ruff check . --isolated", 'pytest "--cov=$COV"'):
        assert removal < analyse.index(invocation), "deleting after the tools run protects nothing"


def test_no_citizen_text_is_interpolated_into_a_shell(workflow: str) -> None:
    for field in ("pull_request.title", "pull_request.body"):
        assert f"${{{{ github.event.{field} }}}}" not in workflow


def test_a_review_writes_no_state_and_a_record_is_told_where_the_readings_are(
    workflow: str,
) -> None:
    run = _executable(_job(workflow, "review"))
    invocations = re.findall(r"python\b[^\n]*?-m shodann\.review(?:[^\n]*\\\n)*[^\n]*", run)

    assert len(invocations) == 2, "one review, one record"
    assert sum("--dry-run" in invocation for invocation in invocations) == 1
    for invocation in invocations:
        assert "--reports" in invocation, "downloading an artifact and not reading it"


def test_the_ledger_is_only_written_for_a_merge_to_the_default_branch(workflow: str) -> None:
    run = _job(workflow, "review")
    anchor = run.index("Record the citizen ledger")
    condition = run[anchor:].split("run:")[0]

    assert "github.event.pull_request.merged == true" in condition
    assert "github.event.pull_request.base.ref == github.event.repository.default_branch" in (
        condition
    )
    assert "'main'" not in condition, "a subscriber's default branch is not ours"


def test_the_ledger_push_rebases_retries_and_warns_rather_than_fails(workflow: str) -> None:
    review = _executable(_job(workflow, "review"))
    loop = review.split("for attempt in", 1)[1]

    assert 'git fetch origin "$GITHUB_BASE_REF"' in loop
    assert "git rebase FETCH_HEAD" in loop
    push = loop.index('git push origin "HEAD:${GITHUB_BASE_REF}"')
    assert loop.index("git rebase FETCH_HEAD") < push
    assert "continue" in loop.split("git fetch")[1].split("git rebase")[0], "a fetch is transient"
    rebase = loop.split("! git rebase")[1].split("git push")[0]
    assert "rebase --abort" in rebase and "exit 0" in rebase and "continue" not in rebase
    assert "::warning::" in loop and "exit 1" not in loop
    assert loop.rstrip().endswith("exit 0")


# --- the reusable half: somebody else's repository --------------------------


def test_only_the_pinned_engine_is_ever_installed(reusable: str) -> None:
    """`pip install .` here would install the student's package beside the write token."""
    review = _executable(_job(reusable, "review"))
    installs = [line for line in review.splitlines() if "pip install" in line]

    assert "pip install --quiet ./engine" in review, "non-editable, from the pinned checkout"
    assert installs, "no install found at all"
    for line in installs:
        assert re.search(r"\./engine\b", line), f"installs something besides the engine: {line}"
        assert not re.search(r"pip install\b[^\n]*\s(\.|-e|\S*citizen\S*)(\s|$)", line), line


def test_the_engine_checkout_is_pinned_and_holds_no_credentials(reusable: str) -> None:
    step = _executable(_step(reusable, "Check out the pinned engine"))

    assert "repository: norrisaftcc/algorithm-shodann" in step
    assert "ref: ${{ inputs.engine-ref }}" in step
    assert "path: engine" in step
    assert "persist-credentials: false" in step


def test_the_citizen_is_checked_out_beside_the_engine_not_over_it(reusable: str) -> None:
    citizen = _executable(_step(reusable, "Check out the citizen"))

    assert "path: citizen" in citizen
    assert "persist-credentials: false" not in citizen, "the ledger push needs the token"


def test_the_engine_ref_must_be_a_commit_and_the_workflow_enforces_it(reusable: str) -> None:
    inputs = reusable.split("workflow_call:", 1)[1].split("\njobs:", 1)[0]
    ref = inputs.split("engine-ref:", 1)[1].split("\n      python-version:", 1)[0]
    refusal = _executable(_step(reusable, "Refuse an engine that is not pinned to a commit"))

    assert "required: true" in ref
    assert "[0-9a-f]{40}" in refusal, "a branch or tag moves under every subscriber"
    assert "ENGINE_REF: ${{ inputs.engine-ref }}" in refusal, "env, never in the script body"
    assert "${{" not in refusal.split("run:", 1)[1]
    review = _job(reusable, "review")
    assert review.index("Refuse an engine") < review.index("Check out the pinned engine")


def test_every_python_entry_point_ignores_the_working_directory(reusable: str) -> None:
    """`python -m` puts cwd first on sys.path; the ledger steps run inside citizen/.

    Without -I a citizen who commits a `shodann/` directory has it imported
    instead of the installed engine, inside the job holding `contents: write`.
    """
    review = _executable(_job(reusable, "review"))
    calls = re.findall(r"^\s*(?:run:\s*)?(python(?![-\w])[^\n]*)", review, flags=re.MULTILINE)

    assert len(calls) >= 3, "review, record and leaderboard"
    for call in calls:
        assert call.startswith("python -I "), f"working directory can shadow the engine: {call}"


def test_the_only_python_the_privileged_job_runs_is_the_engines_own_module(
    reusable: str,
) -> None:
    """`-I` alone is not enough: `python -I citizen/x.py` carries it too.

    Every call must name an installed engine module with `-m`, so no path inside
    the citizen's checkout is ever handed to an interpreter that holds the write
    token and the model key.
    """
    review = _executable(_job(reusable, "review"))
    calls = re.findall(r"^\s*(?:run:\s*)?(python(?![-\w])[^\n]*)", review, flags=re.MULTILINE)

    assert calls, "no python invocation found; the pattern is matching nothing"
    for call in calls:
        assert re.match(r"python -I -m shodann\.(review|cli)\b", call), call
    for hazard in ("bash citizen", "sh citizen", "./citizen", "source citizen", "citizen/.venv"):
        assert hazard not in review, f"executes something from the citizen's checkout: {hazard}"


def test_the_review_is_composed_against_the_citizen_root(reusable: str) -> None:
    compose = _executable(_step(reusable, "Compose the review"))
    ledger = _executable(_step(reusable, "Record the citizen ledger"))
    ledger_header = _step(reusable, "Record the citizen ledger")

    assert "--root citizen" in compose
    assert "--root ." in ledger
    assert "working-directory: citizen" in ledger_header
    assert '--reports "$GITHUB_WORKSPACE/shodann-reports"' in ledger, "cwd is citizen/ here"


def test_gh_is_told_the_repository_because_the_workspace_root_is_not_one(reusable: str) -> None:
    for name in ("Post the review", "Announce the fault"):
        step = _executable(_step(reusable, name))
        assert "gh pr comment" in step
        assert "GH_REPO: ${{ github.repository }}" in step, f"{name} has no checkout to infer from"


# --- the leaderboard is a ranking of students and is off unless asked -------


def _input_block(reusable: str, name: str) -> str:
    inputs = reusable.split("workflow_call:", 1)[1].split("\njobs:", 1)[0]
    body = inputs.split(f"      {name}:\n", 1)[1]
    return re.split(r"^      [a-z-]+:[ \t]*$", body, maxsplit=1, flags=re.M)[0]


def test_the_leaderboard_defaults_off_and_the_ledger_defaults_on(reusable: str) -> None:
    board = _input_block(reusable, "leaderboard")
    ledger = _input_block(reusable, "record-ledger")

    assert "type: boolean" in board and "default: false" in board
    assert "type: boolean" in ledger and "default: true" in ledger


def test_metrics_md_is_produced_and_committed_only_when_the_board_is_on(reusable: str) -> None:
    review = _executable(_job(reusable, "review"))
    producer = _step(reusable, "Regenerate the leaderboard")
    commit = _executable(_step(reusable, "Commit and push the ledger"))

    assert re.search(r"if:\s*>-?\s*\n?\s*inputs\.leaderboard", producer), "the step is guarded"
    assert "--action leaderboard" in producer and "--out METRICS.md" in producer
    assert review.count("--action leaderboard") == 1, "one producer, or they race"
    assert "LEADERBOARD: ${{ inputs.leaderboard }}" in commit
    # METRICS.md reaches `git add` only through the guarded array append.
    assert commit.count("METRICS.md") == 1
    assert re.search(r'if \[ "\$LEADERBOARD" = "true" \]; then paths\+=\(METRICS\.md\)', commit)
    assert "git add -- \"${paths[@]}\"" in commit
    assert "git add .shodann METRICS.md" not in commit


def test_record_ledger_false_writes_nothing(reusable: str) -> None:
    steps = (
        "Record the citizen ledger",
        "Regenerate the leaderboard",
        "Commit and push the ledger",
    )
    for name in steps:
        header = _step(reusable, name).split("run:", 1)[0]
        assert "inputs.record-ledger" in header, f"{name} ignores record-ledger: false"


# --- every variable the program reads reaches the step that composes --------


def _env_names_read_by_the_program() -> set[str]:
    """Derived, never hand-listed: a hand list is how a new knob goes unmapped.

    Quoted names only, so a docstring that mentions `SHODANN_LLM_*` in prose is
    not mistaken for a variable the program reads.
    """
    source = (SRC / "llm.py").read_text(encoding="utf-8")
    return set(re.findall(r"""["'](SHODANN_[A-Z0-9_]+|ANTHROPIC_API_KEY)["']""", source))


def test_llm_py_is_the_only_module_that_reads_the_environment() -> None:
    """If another module starts reading a variable, the derivation above stops being complete."""
    readers = [
        path.name
        for path in SRC.glob("*.py")
        if re.search(r"os\.environ|getenv|environ\.get", path.read_text(encoding="utf-8"))
    ]
    assert readers == ["llm.py"]


def test_the_derived_variable_list_is_not_empty() -> None:
    """An empty derivation makes the mapping tests below pass on nothing."""
    names = _env_names_read_by_the_program()
    assert len(names) >= 13, sorted(names)
    for known in ("SHODANN_LLM_WIRE", "SHODANN_LLM_EFFORT", "SHODANN_FALLBACK_TEMPERATURE"):
        assert known in names


KEYS = {"SHODANN_LLM_API_KEY", "ANTHROPIC_API_KEY"}


@pytest.mark.parametrize(
    ("path", "source"),
    [(SELF_REVIEW, "vars"), (REUSABLE, "inputs")],
    ids=["shodann.yml", "shodann-review.yml"],
)
def test_every_variable_the_program_reads_is_mapped_in_the_compose_step(
    path: Path, source: str
) -> None:
    """The EARLY_RUNS 8 class: the code is right, the workflow never passes it."""
    compose = _executable(_step(_read(path), "Compose the review"))
    names = _env_names_read_by_the_program()
    assert names

    for name in sorted(names):
        match = re.search(rf"^\s+{name}:\s*(\$\{{\{{[^}}]+\}}\}})\s*$", compose, flags=re.MULTILINE)
        assert match, f"{path.name} never maps {name}; the program would read nothing"
        expression = match.group(1)
        if name in KEYS:
            assert f"secrets.{name}" in expression, f"{name} is a key and must be a secret"
        else:
            assert re.search(rf"\b{source}\.", expression), f"{name}: expected {source}.*"
            assert "secrets." not in expression


def test_a_key_is_never_an_input_or_a_variable(reusable: str, self_review: str) -> None:
    for text in (reusable, self_review):
        assert not re.search(r"(?:inputs|vars)\.[A-Za-z_-]*(?:API_KEY|api-key)", text, re.I)


# --- the subscriber template ------------------------------------------------


def _declared(reusable: str, section: str) -> set[str]:
    block = reusable.split("workflow_call:", 1)[1].split("\njobs:", 1)[0]
    block = block.split(f"\n    {section}:\n", 1)[1]
    block = re.split(r"^    [a-z]+:[ \t]*$", block, maxsplit=1, flags=re.M)[0]
    return set(re.findall(r"^      ([A-Za-z][\w-]*):[ \t]*$", block, flags=re.M))


def test_the_template_pins_workflow_and_engine_to_the_same_commit(template: str) -> None:
    uses = re.findall(
        r"uses:\s*norrisaftcc/algorithm-shodann/\.github/workflows/shodann-review\.yml@(\S+)",
        _executable(template),
    )
    engine = re.findall(r"engine-ref:\s*'?([^'\s]+)'?", _executable(template))

    assert len(uses) == 1 and len(engine) == 1
    assert re.fullmatch(r"[0-9a-f]{40}", uses[0]), "a branch or tag moves under every subscriber"
    assert re.fullmatch(r"[0-9a-f]{40}", engine[0])
    assert uses[0] == engine[0], "the workflow and the engine it installs must be one commit"


def test_the_template_is_the_cts285_profile_with_the_board_off(template: str) -> None:
    body = _executable(template)

    assert re.search(r"^\s+leaderboard: false\s*$", body, flags=re.M)
    assert "llm-wire: anthropic" in body
    assert "llm-model: claude-haiku-5-5" in body
    assert "llm-effort: low" in body
    assert re.search(r"llm-max-tokens: '2000'", body)
    assert "pull_request_target" not in body, "branch pull requests only; see PRD section 8"


def test_the_template_scopes_permissions_and_serialises_per_pull_request(template: str) -> None:
    body = _executable(template)

    assert "contents: write" in body and "pull-requests: write" in body
    assert "concurrency:" in body
    assert "group: shodann-${{ github.event.pull_request.number }}" in body
    assert "cancel-in-progress: true" in body


def test_the_template_only_passes_what_the_workflow_declares(template: str, reusable: str) -> None:
    """Passing an undeclared input is a hard error in Actions and green in this suite."""
    body = _executable(template)
    with_block = body.split("with:")[1].split("secrets:")[0]
    passed_inputs = set(re.findall(r"^      ([a-z][\w-]*):", with_block, re.M))
    passed_secrets = set(re.findall(r"^      ([A-Z_]+):", body.split("secrets:")[1], re.M))

    declared_inputs = _declared(reusable, "inputs")
    declared_secrets = _declared(reusable, "secrets")
    assert passed_inputs and passed_secrets
    assert declared_inputs and declared_secrets
    assert passed_inputs <= declared_inputs, passed_inputs - declared_inputs
    assert passed_secrets <= declared_secrets, passed_secrets - declared_secrets
    assert "engine-ref" in passed_inputs, "the one required input"


def test_the_template_header_states_the_prerequisites(template: str) -> None:
    header = template.split("name: SHODANN", 1)[0].lower()

    for needle in ("fork", "secret", "40-character", "spend limit", "leaderboard"):
        assert needle in header, f"the header no longer mentions {needle!r}"
