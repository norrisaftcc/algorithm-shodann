"""The leaderboard mirror: everyone appears, and only by consent."""

from __future__ import annotations

import json

from shodann.leaderboard import generate_leaderboard, load_all_citizens
from shodann.state import VISIBILITY_ANONYMOUS, CitizenRecord, Display, citizen_path


def write_record(root, citizen, velocity, *, anonymous=False, handle=None, pr_count=1):
    record = CitizenRecord(
        citizen=citizen,
        last_velocity=velocity,
        pr_count=pr_count,
        display=Display(visibility=VISIBILITY_ANONYMOUS, handle=handle) if anonymous else Display(),
    )
    path = citizen_path(citizen, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
    return record


def test_empty_course_is_a_valid_state(tmp_path) -> None:
    """The retired engine exited 1 here. An empty course is not an error."""
    document = generate_leaderboard(tmp_path)
    assert "No submissions yet" in document


def test_ranked_by_velocity(tmp_path) -> None:
    write_record(tmp_path, "slow", 1.5)
    write_record(tmp_path, "fast", 42.0)
    write_record(tmp_path, "middling", 12.0)

    rows = [line for line in generate_leaderboard(tmp_path).splitlines() if line.startswith("| 1 ")]
    assert "@fast" in rows[0]


def test_every_citizen_appears(tmp_path) -> None:
    """PRD US-3.2: all citizens appear. The retired engine sliced to the top 20."""
    for index in range(25):
        write_record(tmp_path, f"citizen{index:02d}", float(index))

    document = generate_leaderboard(tmp_path)
    assert document.count("| citizen") + document.count("| @citizen") == 25
    assert "@citizen00" in document, "the slowest citizen is exactly who this system watches"


def test_anonymous_citizens_appear_without_their_username(tmp_path) -> None:
    write_record(tmp_path, "shyperson", 9.0, anonymous=True, handle="Citizen-7")
    document = generate_leaderboard(tmp_path)

    assert "Citizen-7" in document
    assert "shyperson" not in document


def test_unreadable_ledger_is_skipped_not_fatal(tmp_path) -> None:
    write_record(tmp_path, "good", 5.0)
    bad = citizen_path("bad", tmp_path)
    bad.write_text("{{{", encoding="utf-8")

    assert len(load_all_citizens(tmp_path)) == 1
    assert "@good" in generate_leaderboard(tmp_path)
