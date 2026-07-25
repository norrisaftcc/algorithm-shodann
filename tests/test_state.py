"""The citizen ledger: round-tripping, degradation, and the streak bug."""

from __future__ import annotations

import json

from shodann.state import (
    KIND_AGENT,
    TREND_ASCENDING,
    TREND_NEW,
    VISIBILITY_ANONYMOUS,
    CitizenRecord,
    Display,
    citizen_path,
    compute_trend,
    load_citizen_history,
    save_citizen_history,
)
from shodann.velocity import CodeMetrics, calculate_velocity


def submit(root, citizen="octocat", *, coverage=30.0, test_count=3, iterations=2, previous=None):
    current = CodeMetrics(coverage=coverage, test_count=test_count)
    result = calculate_velocity(current, previous, iterations)
    return save_citizen_history(citizen, current, result, root), result


def test_unknown_citizen_reads_as_new(tmp_path) -> None:
    record = load_citizen_history("nobody", tmp_path)
    assert record.pr_count == 0
    assert record.velocity_trend == TREND_NEW
    assert record.last_metrics is None


def test_round_trip(tmp_path) -> None:
    submit(tmp_path)
    reloaded = load_citizen_history("octocat", tmp_path)

    assert reloaded.pr_count == 1
    assert reloaded.baseline_established
    assert reloaded.last_metrics.coverage == 30.0
    assert reloaded.first_submission is not None


def test_streak_survives_a_reload(tmp_path) -> None:
    """The retired engine wrote 'streak' and read 'iterationStreak', so this always read 0."""
    submit(tmp_path)
    assert load_citizen_history("octocat", tmp_path).iteration_streak == 1

    submit(tmp_path, coverage=45.0, test_count=6)
    assert load_citizen_history("octocat", tmp_path).iteration_streak == 2

    submit(tmp_path, coverage=45.0, test_count=6)
    third = load_citizen_history("octocat", tmp_path)
    assert third.pr_count == 3
    assert third.iteration_streak == 3


def test_history_is_capped_and_newest_first(tmp_path) -> None:
    for index in range(14):
        submit(tmp_path, coverage=float(index), test_count=index)

    record = load_citizen_history("octocat", tmp_path)
    assert len(record.velocity_history) == 10
    dates = [entry["date"] for entry in record.velocity_history]
    assert dates == sorted(dates, reverse=True)


def test_trend_enum_not_emoji() -> None:
    """PRD US-3.2 requires the enum. Glyphs belong to the renderer."""
    assert compute_trend([]) == TREND_NEW
    assert compute_trend([{"score": 5.0}]) == TREND_NEW
    assert compute_trend([{"score": 9.0}, {"score": 3.0}, {"score": 3.0}]) == TREND_ASCENDING


def test_corrupt_ledger_degrades_to_a_new_citizen(tmp_path) -> None:
    """PRD section 8: state corruption resets to a default; a student still gets feedback."""
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json at all", encoding="utf-8")

    record = load_citizen_history("octocat", tmp_path)
    assert record.citizen == "octocat"
    assert record.pr_count == 0


def test_written_file_uses_the_agreed_schema(tmp_path) -> None:
    submit(tmp_path)
    with citizen_path("octocat", tmp_path).open(encoding="utf-8") as handle:
        raw = json.load(handle)

    assert set(raw) >= {
        "citizen",
        "kind",
        "display",
        "clearance_level",
        "pr_count",
        "iteration_streak",
        "last_metrics",
        "last_velocity",
        "velocity_trend",
        "velocity_history",
    }
    assert isinstance(raw["pr_count"], int), "numbers are unquoted in this schema"
    assert isinstance(raw["last_velocity"], (int, float))
    assert "prCount" not in raw, "camelCase is the retired schema"
    assert "streak" not in raw, "the key that never round-tripped"


def test_agent_citizens_share_the_registry(tmp_path) -> None:
    record = CitizenRecord(citizen="oracle-warden", kind=KIND_AGENT)
    restored = CitizenRecord.from_dict(record.to_dict())
    assert restored.kind == KIND_AGENT


def test_anonymous_citizens_are_never_named() -> None:
    display = Display(visibility=VISIBILITY_ANONYMOUS, handle="Citizen-7")
    assert display.label("realname") == "Citizen-7"
    assert "realname" not in display.label("realname")


def test_named_is_the_stated_default_and_still_explicit() -> None:
    assert Display().label("octocat") == "@octocat"
