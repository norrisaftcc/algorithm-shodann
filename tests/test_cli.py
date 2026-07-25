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
