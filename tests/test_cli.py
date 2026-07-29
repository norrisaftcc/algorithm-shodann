"""End-to-end behaviour of the command line entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from shodann.cli import main
from shodann.state import citizen_path

METRICS = {
    "coverage": 34.0,
    "test_count": 4,
    "complexity": 9,
    "loc": 210,
    "functions": 8,
    "docstrings": 3,
    "lint_issues": 2,
}


def write_metrics(tmp_path: Path, name: str = "metrics.json", **overrides) -> str:
    payload = {**METRICS, **overrides}
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_velocity_action_emits_json(tmp_path, capsys) -> None:
    code = main(["-c", "octocat", "--current", write_metrics(tmp_path), "--root", str(tmp_path)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["score"] > 0
    assert payload["is_first_submission"] is True


def test_prompt_action_renders_a_section(tmp_path, capsys) -> None:
    main(["-c", "octocat", "--current", write_metrics(tmp_path), "--root", str(tmp_path),
          "-a", "prompt"])
    assert "Growth Velocity Analysis" in capsys.readouterr().out


def test_leaderboard_action_survives_an_empty_course(tmp_path, capsys) -> None:
    assert main(["-a", "leaderboard", "--root", str(tmp_path)]) == 0
    assert "Velocity Rankings" in capsys.readouterr().out


def test_missing_arguments_exit_nonzero(tmp_path, capsys) -> None:
    assert main(["-c", "octocat", "--root", str(tmp_path)]) == 2
    assert "required" in capsys.readouterr().err


def test_dry_run_leaves_no_ledger(tmp_path) -> None:
    main(["-c", "octocat", "--current", write_metrics(tmp_path), "--root", str(tmp_path),
          "--dry-run"])
    assert not citizen_path("octocat", tmp_path).exists()


def test_state_accumulates_across_runs(tmp_path) -> None:
    current = write_metrics(tmp_path)
    for _ in range(3):
        main(["-c", "octocat", "--current", current, "--root", str(tmp_path)])

    with citizen_path("octocat", tmp_path).open(encoding="utf-8") as handle:
        record = json.load(handle)
    assert record["pr_count"] == 3


def read_ledger(tmp_path, citizen: str = "octocat") -> dict:
    """The stored ledger as a dict.

    Callers assert on the one key they are about, never on the whole document:
    `CitizenRecord` gains fields (`schema_version`, `discontinuities`) and a
    whole-dict comparison here would fail on someone else's addition rather
    than on the behaviour under test.
    """
    with citizen_path(citizen, tmp_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_a_measured_coverage_figure_is_stored_as_measured(tmp_path) -> None:
    """S1-21. The CLI wrote `coverage_instrumented: false` beside a real reading.

    `save_citizen_history`'s keyword-only `coverage_instrumented` defaults to
    False and `main` never passed it, so one manual run against a genuine
    `coverage.json`-derived metrics file stored *unmeasured* next to a measured
    figure. Nothing in this run's output is wrong, which is why it survived -
    the damage lands in the next run, where `review.reconcile_coverage` reads
    the stored flag to decide whether a coverage delta may be claimed at all.
    """
    main(["-c", "octocat", "--current", write_metrics(tmp_path), "--root", str(tmp_path)])
    assert read_ledger(tmp_path)["coverage_instrumented"] is True


def test_a_metrics_file_with_no_coverage_key_is_not_claimed_as_measured(tmp_path) -> None:
    """The other direction of the same rule: absent is not zero, and not measured.

    Guards against over-correcting S1-21 into an unconditional True, which
    would be the identical defect pointing the other way - `from_dict` invents
    0.0 for a missing key, and calling that a reading credits a citizen with a
    measurement nobody took.
    """
    payload = {key: value for key, value in METRICS.items() if key != "coverage"}
    path = tmp_path / "no-coverage.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    main(["-c", "octocat", "--current", str(path), "--root", str(tmp_path)])
    assert read_ledger(tmp_path)["coverage_instrumented"] is False


def test_a_stated_zero_is_a_measurement(tmp_path) -> None:
    """0 to 30 is US-1.3's flagship case, so a written zero must not read as a gap."""
    main(["-c", "octocat", "--current", write_metrics(tmp_path, coverage=0.0),
          "--root", str(tmp_path)])
    assert read_ledger(tmp_path)["coverage_instrumented"] is True


def test_the_operator_may_overrule_the_inference_in_both_directions(tmp_path) -> None:
    """The inference is defeasible, and saying so beats defaulting to a lie.

    A hand-written fixture carrying a boilerplate coverage figure nobody
    measured is the case the file cannot express, so the flag exists; the
    tri-state default (`None`, not False) is what keeps "you did not say" from
    collapsing into "it was not measured".
    """
    main(["-c", "denied", "--current", write_metrics(tmp_path), "--root", str(tmp_path),
          "--no-coverage-instrumented"])
    assert read_ledger(tmp_path, "denied")["coverage_instrumented"] is False

    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps({"test_count": 4}), encoding="utf-8")
    main(["-c", "asserted", "--current", str(bare), "--root", str(tmp_path),
          "--coverage-instrumented"])
    assert read_ledger(tmp_path, "asserted")["coverage_instrumented"] is True


def test_emoji_output_survives_a_non_utf8_console(tmp_path) -> None:
    """Regression: the CLI used to die on Windows before printing a single line.

    SHODANN's headings are emoji, and Python encodes stdout with the locale
    codec - cp1252 on Windows - unless told otherwise. Forcing the child's
    stdio to cp1252 reproduces that console on any platform.
    """
    metrics = write_metrics(tmp_path)
    env = {
        **dict(__import__("os").environ),
        "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
        "PYTHONIOENCODING": "cp1252",
    }
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, sys.executable only
        [sys.executable, "-m", "shodann.cli", "-c", "octocat", "--current", metrics,
         "--root", str(tmp_path), "-a", "prompt"],
        capture_output=True,
        env=env,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert "UnicodeEncodeError" not in completed.stderr.decode("utf-8", "replace")
    assert "\U0001f4c8".encode() in completed.stdout


def test_the_leaderboard_can_be_written_to_a_file(tmp_path) -> None:
    """S1-12. The producer. `--action leaderboard` could only ever print.

    stdout is not an artifact an instructor finds, and the workflow that would
    have redirected it did not exist - so `leaderboard.py` was complete, tested
    and unreachable for the whole life of the project. Writing goes through
    `state.atomic_write` for the same reason the ledger does: a killed job must
    not leave half a board for someone to read as a whole one.
    """
    out = tmp_path / "METRICS.md"

    assert main(["--action", "leaderboard", "--root", str(tmp_path), "--out", str(out)]) == 0

    board = out.read_text(encoding="utf-8")
    assert "SHODANN Growth Velocity Leaderboard" in board
    assert "Last Updated" in board, "an undated mirror cannot be told from a stale one"
