"""Transcription check against the retired JavaScript engine.

These are not parity tests in the usual sense - we are not committed to the
predecessor's behaviour, and PRD US-1.3 requires diverging from it. They exist
for one narrow purpose: catching a mistyped weight or an inverted comparison
in the port.

Every case is scored under ``ORACLE_CONFIG``, which disables the first-test
bonus and so reproduces the pre-US-1.3 engine exactly. Production runs on
``DEFAULT_CONFIG``; the deliberate divergences live in
``test_velocity_contracts.py``.

The fixture was captured once, on 2026-07-25, from a local Node run. Node is
not a test dependency and must not become one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shodann.config import ORACLE_CONFIG
from shodann.velocity import CodeMetrics, calculate_velocity

FIXTURE = Path(__file__).parent / "fixtures" / "oracle_snapshot.json"

# The JS engine emitted camelCase; the Python engine speaks snake_case.
KEY_MAP = {
    "testCount": "test_count",
    "lintIssues": "lint_issues",
    "syntaxErrors": "syntax_errors",
}


def _to_snake(data: dict) -> dict:
    return {KEY_MAP.get(key, key): value for key, value in data.items()}


def _load_cases() -> list[tuple[str, dict]]:
    with FIXTURE.open(encoding="utf-8") as handle:
        return sorted(json.load(handle)["cases"].items())


CASES = _load_cases()


@pytest.mark.parametrize("name,case", CASES, ids=[name for name, _ in CASES])
def test_matches_oracle(name: str, case: dict) -> None:
    current = CodeMetrics.from_dict(_to_snake(case["current"]))
    previous = (
        CodeMetrics.from_dict(_to_snake(case["previous"])) if case["previous"] else None
    )

    result = calculate_velocity(
        current, previous, case["iterations"], config=ORACLE_CONFIG
    )

    assert result.score == pytest.approx(case["score"]), f"{name}: score drifted from the oracle"
    assert result.assessment == case["assessment"]
    assert result.deltas.to_dict() == _to_snake(case["deltas"])
    assert result.celebrations == case["celebrations"]
    assert result.opportunities == case["opportunities"]


def test_fixture_records_its_own_provenance() -> None:
    """If someone regenerates this file, the note explaining what it is must survive."""
    with FIXTURE.open(encoding="utf-8") as handle:
        provenance = json.load(handle)["_provenance"]
    assert provenance["source"] == "design_docs/growth-velocity.js"
    assert provenance["captured"]
