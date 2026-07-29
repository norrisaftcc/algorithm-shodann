"""Command line entry point, used by the workflow and by anyone poking at fixtures.

Paths resolve against ``--root`` (default: the current directory) rather than
being silently relative to wherever the process happened to start.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .leaderboard import generate_leaderboard
from .prompt_section import generate_prompt_section
from .state import load_citizen_history, save_citizen_history
from .velocity import CodeMetrics, calculate_velocity

__all__ = ["main"]

COVERAGE_KEY = "coverage"
"""The metrics-file key whose *presence* is this CLI's evidence that coverage ran."""


@dataclass(frozen=True)
class MetricsReading:
    """A parsed metrics file, plus the one fact parsing it destroys.

    `CodeMetrics.coverage` is a float feeding an arithmetic engine, so it
    cannot carry "nobody looked": 0.0 there means both *no lines were covered*
    and *no coverage tool ran*, and `CodeMetrics.from_dict` manufactures that
    same 0.0 for a file with no coverage key at all. The distinction lives in
    `CitizenRecord.coverage_instrumented` instead, and it has to survive the
    parse to get there - hence a second field beside the metrics rather than a
    sentinel inside them.

    It is not bookkeeping. `review.reconcile_coverage` reads that stored flag
    to decide whether the *next* review may claim a coverage delta at all; a
    false one there produced both a fabricated 98-point celebration and a -405
    score (EARLY_RUNS 9, and `CitizenRecord.coverage_instrumented` in
    `state.py`). A wrong answer here is therefore not wrong in this run's
    output - this run prints a score either way - it is wrong in the next one's
    arithmetic, which is why it went unnoticed (S1-21).
    """

    metrics: CodeMetrics
    coverage_present: bool


def _read_metrics(path: str) -> MetricsReading:
    """Parse a metrics JSON, keeping the coverage-key answer from the same read.

    Answered from the parse rather than by re-opening the file later, because a
    second read answers a question about a different read: a file edited
    between the two would have its metrics taken from one state and its
    instrumentation claim from another. `state.CitizenRecord.unreadable_source`
    is carried for the identical reason and says so at length.
    """
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return MetricsReading(CodeMetrics.from_dict(data), coverage_present=COVERAGE_KEY in data)


def coverage_was_measured(reading: MetricsReading, override: bool | None) -> bool:
    """Whether the coverage figure about to be stored was actually measured.

    S1-21: this used to have no answer at all. `main` called
    `save_citizen_history` without the keyword-only `coverage_instrumented`,
    took its ``False`` default, and so wrote *unmeasured* beside a coverage
    figure read from a real `coverage.json` - poisoning the ledger that the
    next run's `reconcile_coverage` trusts.

    The evidence is the presence of the ``coverage`` key in ``--current``,
    which is the only thing this CLI can honestly observe. It never runs a tool
    (`analysis.py` explains why nothing in this project does) and it is handed
    a file, so the file is the whole of the record: a producer that measured
    coverage writes the key, and one that did not omits it. A stated
    ``"coverage": 0.0`` is therefore read as a **measured zero**, which is the
    right reading and the important one - 0 to 30 is US-1.3's flagship case and
    must keep scoring as the gain it is.

    ``override`` exists because that inference is defeasible in exactly one
    direction the file cannot express: a hand-written fixture carrying
    ``"coverage": 0.0`` as boilerplate nobody measured, or a file assembled by
    hand from a run that did measure but whose key got dropped. Rather than
    default to a lie in either direction, the operator can assert the fact with
    ``--coverage-instrumented`` / ``--no-coverage-instrumented``; ``None`` means
    they did not, and the inference stands.
    """
    return reading.coverage_present if override is None else override


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
    # Tri-state on purpose: True, False, and "you did not say". `store_true`
    # would collapse the third into the second, which is the shape of the
    # defect being fixed - see `coverage_was_measured`.
    parser.add_argument("--coverage-instrumented", action=argparse.BooleanOptionalAction,
                        default=None,
                        help="state whether --current's coverage figure was measured; "
                             "default: inferred from whether the file carries a coverage key")
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
    # Only `--current`'s instrumentation is stored: the ledger records what was
    # measured *this* cycle, and the previous side's answer already sits in the
    # record `reconcile_coverage` reads it from.
    previous = _read_metrics(args.previous).metrics if args.previous else record.last_metrics

    result = calculate_velocity(current.metrics, previous, args.iterations)

    if not args.dry_run:
        record = save_citizen_history(
            args.citizen,
            current.metrics,
            result,
            args.root,
            coverage_instrumented=coverage_was_measured(current, args.coverage_instrumented),
        )

    if args.action == "prompt":
        sys.stdout.write(generate_prompt_section(result, record) + "\n")
    else:
        sys.stdout.write(json.dumps(result.to_dict(), indent=2) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
