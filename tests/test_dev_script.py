"""The developer entry point is the one thing every session runs first.

`scripts/dev.py` exists because this repository spent months telling a fresh
session to run `.venv/Scripts/python.exe`, which works on exactly one machine.
A task runner that is itself platform-specific would be the same defect in a
new costume, so the parts that can be tested from here are tested from here.

`dev.py` is loaded by path rather than imported: it deliberately lives outside
the package, because it has to run on a system interpreter with nothing
installed.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dev() -> ModuleType:
    return _load("dev")


def test_every_command_is_reachable_from_the_parser(dev: ModuleType) -> None:
    """A subcommand missing from either half is a command nobody can run."""
    choices = set(dev.build_parser()._actions[-1].choices)
    assert choices == set(dev.COMMANDS)
    assert {"bootstrap", "test", "check", "render", "all"} <= choices


def test_the_platform_branch_exists_exactly_once(dev: ModuleType) -> None:
    """Scripts-versus-bin is resolved in one place, and it is this one."""
    source = (SCRIPTS / "dev.py").read_text(encoding="utf-8")
    assert source.count('"Scripts"') == 1, "one branch, or the scar reopens"
    assert dev.BIN_DIR in ("Scripts", "bin")
    assert dev.venv_python().parent.name == dev.BIN_DIR


def test_venv_detection_reads_the_prefix_not_the_interpreter_path(
    dev: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression test for a bug that made every interpreter look correct.

    `.venv/bin/python` is a symlink to the system interpreter, so comparing
    resolved *executable* paths reported True under `/usr/local/bin/python3`.
    `dev.py` then handed that interpreter work needing the installed package,
    and `render` died on `ModuleNotFoundError: shodann` with a perfectly good
    venv sitting beside it. PEP 405 puts the venv root in `sys.prefix`.
    """
    monkeypatch.setattr(sys, "prefix", str(ROOT / "not-the-venv"))
    assert dev.running_inside_venv() is False

    monkeypatch.setattr(sys, "prefix", str(dev.VENV))
    assert dev.running_inside_venv() is True


def test_a_foreign_interpreter_is_never_used_to_run_the_package(
    dev: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Outside the venv, work must be handed to the venv's own interpreter."""
    monkeypatch.setattr(sys, "prefix", str(ROOT / "not-the-venv"))
    assert dev.python_for_run() == dev.venv_python()


@pytest.mark.skipif(
    importlib.util.find_spec("shodann") is None, reason="the package is not importable"
)
def test_render_produces_a_review_a_person_could_read() -> None:
    """The check `CLAUDE.md` calls distinct from testing, made runnable.

    Two entries in `EARLY_RUNS.md` were found only by printing the comment and
    reading it. A render that silently emits nothing would retire that check
    while appearing to keep it.
    """
    render = _load("render_review")
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        assert render.main([]) == 0

    body = buffer.getvalue()
    assert "SHODANN Analysis Complete" in body
    assert "@octocat" in body
    assert len(body.split()) > 50


def test_render_never_writes_the_ledger() -> None:
    """A read-through is an observation, not a cycle.

    `review()` defaults to `write_state=True`, and manual runs that persisted
    are how the live ledger collected two entries 58 seconds apart.
    """
    source = (SCRIPTS / "render_review.py").read_text(encoding="utf-8")
    assert "write_state=False" in source
    # An explicit empty config, so a key in the environment cannot turn a
    # local read-through into a billed request.
    assert "config=LLMConfig()" in source
