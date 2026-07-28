"""Print a review the way a citizen would receive it.

Runs inside the project venv, so unlike `dev.py` beside it, this file may
import `shodann`.

Two safety properties, both deliberate:

**It never writes the ledger.** `review()` defaults to `write_state=True`, and
a manual run that persists is how `.shodann/citizens/norrisaftcc.json`
collected entries 58 seconds apart. A render is an observation, not a cycle.

**It never calls a model.** `LLMConfig()` is passed explicitly rather than
letting `review()` reach for `LLMConfig.from_env()`, so a key sitting in the
environment cannot turn a local read-through into a billed request. The empty
config takes the REDUCED ALLOCATION path, which is the offline check
`CLAUDE.md` describes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shodann.cli import force_utf8_output
from shodann.llm import LLMConfig
from shodann.review import SPECS, review

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENT = ROOT / "tests" / "fixtures" / "sample_event.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/dev.py render",
        description="Compose a review offline and print it for reading.",
    )
    parser.add_argument("--event", default=str(DEFAULT_EVENT), help="event payload to compose from")
    parser.add_argument("--mode", default="standard", choices=sorted(SPECS))
    parser.add_argument("--root", default=str(ROOT), help="repository to measure")
    parser.add_argument(
        "--reports",
        help="directory holding coverage.json and ruff.json, if you have them",
    )
    args = parser.parse_args(argv)

    # SHODANN's output is emoji-dense by design and Python defaults stdout to
    # the locale codec, which raises on the very first heading under cp1252.
    force_utf8_output()

    with Path(args.event).open(encoding="utf-8") as handle:
        event = json.load(handle)

    body = review(
        event,
        root=args.root,
        reports_dir=args.reports,
        config=LLMConfig(),
        mode=args.mode,
        write_state=False,
    )

    sys.stdout.write(body + "\n")
    sys.stderr.write(f"\n--> {len(body.split())} words\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
