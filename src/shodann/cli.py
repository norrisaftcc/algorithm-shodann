"""Command line entry point, used by the workflow and by anyone poking at fixtures.

Paths resolve against ``--root`` (default: the current directory) rather than
being silently relative to wherever the process happened to start.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .leaderboard import generate_leaderboard
from .prompt_section import generate_prompt_section
from .state import load_citizen_history, save_citizen_history
from .velocity import CodeMetrics, calculate_velocity

__all__ = ["main"]


def _read_metrics(path: str) -> CodeMetrics:
    with Path(path).open(encoding="utf-8") as handle:
        return CodeMetrics.from_dict(json.load(handle))


def force_utf8_output() -> None:
    """Make stdout and stderr carry emoji on every platform.

    SHODANN's output is emoji-dense by design, and Python defaults stdout to
    the locale codec - cp1252 on Windows - which raises UnicodeEncodeError on
    the very first heading. Linux runners never see this, so it would
    otherwise only ever break on a maintainer's machine.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shodann-velocity", description="SHODANN velocity engine")
    parser.add_argument("-a", "--action", choices=("velocity", "leaderboard", "prompt"),
                        default="velocity")
    parser.add_argument("-c", "--citizen")
    parser.add_argument("--current", help="path to the current metrics JSON")
    parser.add_argument("--previous", help="path to previous metrics JSON (defaults to the ledger)")
    parser.add_argument("-i", "--iterations", type=int, default=1)
    parser.add_argument("--root", default=".", help="repository root holding .shodann/")
    parser.add_argument("--dry-run", action="store_true",
                        help="compute without writing to the ledger")
    return parser


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    args = build_parser().parse_args(argv)

    if args.action == "leaderboard":
        sys.stdout.write(generate_leaderboard(args.root) + "\n")
        return 0

    if not args.citizen or not args.current:
        sys.stderr.write("error: --citizen and --current are required\n")
        return 2

    current = _read_metrics(args.current)
    record = load_citizen_history(args.citizen, args.root)
    previous = _read_metrics(args.previous) if args.previous else record.last_metrics

    result = calculate_velocity(current, previous, args.iterations)

    if not args.dry_run:
        record = save_citizen_history(args.citizen, current, result, args.root)

    if args.action == "prompt":
        sys.stdout.write(generate_prompt_section(result, record) + "\n")
    else:
        sys.stdout.write(json.dumps(result.to_dict(), indent=2) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
