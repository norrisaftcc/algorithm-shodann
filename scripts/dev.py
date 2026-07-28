"""One command string for every platform.

This repository was hardwired to a single Windows machine for months, not in
its runtime - `shodann.cli.force_utf8_output` has handled the console encoding
on every platform since it shipped - but in the instructions a fresh session
reads first. `CLAUDE.md` named `.venv/Scripts/python.exe` and nothing else, so
a container, a Codespace, and a Mac all started from a command that cannot
work, and no gate ever noticed because nothing ran this repository's own tests
on a pull request.

The fix is not to document both answers. It is to make the question stop
arriving:

    python scripts/dev.py bootstrap
    python scripts/dev.py test
    python scripts/dev.py check
    python scripts/dev.py render

Those strings are identical on Windows, Linux, macOS and a Codespace. This
file runs on the *system* interpreter with nothing installed, because the
first thing it has to do is build the environment everything else needs.
Standard library only, and it must stay that way.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"

# The Scripts-versus-bin branch exists exactly once, here. It was never that
# the branch is avoidable - it is that every reader forced to hold it is a
# reader who can get it wrong, and this project has the scar to prove it.
BIN_DIR = "Scripts" if os.name == "nt" else "bin"
EXE = ".exe" if os.name == "nt" else ""


def venv_python() -> Path:
    return VENV / BIN_DIR / f"python{EXE}"


def venv_script(name: str) -> Path:
    return VENV / BIN_DIR / f"{name}{EXE}"


def running_inside_venv() -> bool:
    """True when this interpreter already *is* the project venv.

    Re-executing the same interpreter through itself works, but it doubles
    every process and makes a traceback twice as long as the defect it
    describes. Cheap to check, so check.

    Compare `sys.prefix`, never the interpreter path. `.venv/bin/python` is a
    *symlink to the system interpreter*, so resolving both sides makes every
    interpreter on the machine look like the venv - this returned True under
    `/usr/local/bin/python3` and then handed that interpreter work that needed
    the installed package. PEP 405 points `sys.prefix` at the venv root and
    nowhere else.
    """
    try:
        return Path(sys.prefix).resolve() == VENV.resolve()
    except OSError:
        return False


def python_for_run() -> Path:
    return Path(sys.executable) if running_inside_venv() else venv_python()


def run(argv: list[str | Path], *, label: str) -> int:
    """Run one child process from the repository root and report it plainly."""
    printable = [str(part) for part in argv]
    sys.stderr.write(f"--> {label}\n")
    # noqa: S603 is the honest answer here - argv is a fixed list built from
    # this file's own constants plus arguments the maintainer typed, there is
    # no shell, and nothing citizen-authored reaches it.
    completed = subprocess.run(printable, cwd=ROOT)  # noqa: S603
    return completed.returncode


def bootstrap() -> int:
    """Create the venv if it is absent and install the project into it.

    Idempotent on purpose: `test` and `check` call this rather than failing
    with instructions, so a fresh clone reaches a green suite in one command
    instead of two.
    """
    if not venv_python().exists():
        sys.stderr.write(f"--> creating {VENV.relative_to(ROOT)}\n")
        venv.EnvBuilder(with_pip=True, upgrade_deps=False).create(VENV)

    return run(
        [venv_python(), "-m", "pip", "install", "--quiet", "--editable", ".[dev]"],
        label="installing the project and its dev extras",
    )


def ensure_environment() -> int:
    """Guarantee an interpreter to run things with, saying so if it builds one."""
    if venv_python().exists() or running_inside_venv():
        return 0
    sys.stderr.write("--> no .venv found; bootstrapping first\n")
    return bootstrap()


def cmd_bootstrap(_: argparse.Namespace, extra: list[str]) -> int:
    del extra
    return bootstrap()


def cmd_test(_: argparse.Namespace, extra: list[str]) -> int:
    failed = ensure_environment()
    if failed:
        return failed
    # Trailing arguments pass straight through, so the single-test recipe
    # survives: `python scripts/dev.py test tests/test_review.py::test_name`.
    return run(
        [python_for_run(), "-m", "pytest", "-q", *extra],
        label="pytest -q",
    )


def cmd_check(_: argparse.Namespace, extra: list[str]) -> int:
    failed = ensure_environment()
    if failed:
        return failed
    return run([venv_script("ruff"), "check", ".", *extra], label="ruff check .")


def cmd_render(_: argparse.Namespace, extra: list[str]) -> int:
    """Compose a review and print it.

    `CLAUDE.md` calls this a distinct check from testing, and records two
    defects in `design_docs/EARLY_RUNS.md` that only reading the comment
    found - including a review whose two sections contradicted each other
    about coverage while 243 tests passed. It was documented as a paragraph of
    prose to reassemble by hand, which is a reliable way to have a check
    skipped. Now it is a command.
    """
    failed = ensure_environment()
    if failed:
        return failed
    return run(
        [python_for_run(), ROOT / "scripts" / "render_review.py", *extra],
        label="rendering a review",
    )


def cmd_all(args: argparse.Namespace, extra: list[str]) -> int:
    del extra
    # Fails fast on purpose: a broken test run is reason enough to stop, and
    # `check`'s exit code would otherwise be masked by whichever ran last.
    return cmd_test(args, []) or cmd_check(args, [])


COMMANDS = {
    "bootstrap": cmd_bootstrap,
    "test": cmd_test,
    "check": cmd_check,
    "render": cmd_render,
    "all": cmd_all,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/dev.py",
        description="Cross-platform developer tasks for SHODANN.",
        epilog="Unrecognised trailing arguments are passed to the underlying tool.",
    )
    parser.add_argument("command", choices=sorted(COMMANDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    args, extra = build_parser().parse_known_args(argv)
    return COMMANDS[args.command](args, extra)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
