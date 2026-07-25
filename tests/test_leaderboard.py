"""The leaderboard mirror: everyone appears, and only by consent."""

from __future__ import annotations

import json

import pytest

from shodann.leaderboard import ClearanceRequired, generate_leaderboard, load_all_citizens
from shodann.state import (
    KIND_AGENT,
    VISIBILITY_ANONYMOUS,
    CitizenRecord,
    Display,
    citizen_path,
)


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


# --- the partition rule ---------------------------------------------------


def write_agent(root, name, velocity):
    record = CitizenRecord(citizen=name, kind=KIND_AGENT, last_velocity=velocity, pr_count=9)
    path = citizen_path(name, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict()), encoding="utf-8")


def test_agents_never_appear_on_the_citizen_board(tmp_path) -> None:
    """Walking is not driving. An agent shipping fast is a different mode."""
    write_record(tmp_path, "student", 4.0)
    write_agent(tmp_path, "oracle-warden", 900.0)

    document = generate_leaderboard(tmp_path)

    assert "@student" in document
    assert "oracle-warden" not in document
    assert "| 1 |" in document and "@student" in document.splitlines()[
        next(i for i, line in enumerate(document.splitlines()) if line.startswith("| 1 "))
    ], "the student is rank 1 of humans, not rank 2 of everything"


def test_the_agent_board_is_its_own_document(tmp_path) -> None:
    write_record(tmp_path, "student", 4.0)
    write_agent(tmp_path, "oracle-warden", 900.0)

    document = generate_leaderboard(tmp_path, kind=KIND_AGENT)

    assert "oracle-warden" in document
    assert "@student" not in document
    assert "Agent Fleet" in document


def test_the_mixed_view_says_what_it_is(tmp_path) -> None:
    write_record(tmp_path, "student", 4.0)
    write_agent(tmp_path, "oracle-warden", 900.0)

    document = generate_leaderboard(tmp_path, kind=None)

    assert "Mixed-kind view" in document
    assert "not comparable" in document


@pytest.mark.parametrize("clearance", [1, 2])
def test_below_orange_cannot_open_agent_data(tmp_path, clearance: int) -> None:
    """The gate is on the viewer, not the data - and it refuses at generation."""
    with pytest.raises(ClearanceRequired, match="ORANGE"):
        generate_leaderboard(tmp_path, kind=KIND_AGENT, viewer_clearance=clearance)
    with pytest.raises(ClearanceRequired):
        generate_leaderboard(tmp_path, kind=None, viewer_clearance=clearance)


@pytest.mark.parametrize("clearance", [3, 4, 5, 6])
def test_orange_and_up_may_open_it(tmp_path, clearance: int) -> None:
    write_agent(tmp_path, "oracle-warden", 900.0)
    assert "oracle-warden" in generate_leaderboard(
        tmp_path, kind=KIND_AGENT, viewer_clearance=clearance
    )


@pytest.mark.parametrize("clearance", [1, 2, 3, 6])
def test_every_band_may_open_their_own_board(tmp_path, clearance: int) -> None:
    write_record(tmp_path, "student", 4.0)
    assert "@student" in generate_leaderboard(tmp_path, viewer_clearance=clearance)


def test_a_record_without_a_kind_partitions_as_human(tmp_path) -> None:
    """A missing discriminator must not make a citizen vanish from their own board."""
    path = citizen_path("legacy", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"citizen": "legacy", "last_velocity": 3.0}), encoding="utf-8")

    assert "@legacy" in generate_leaderboard(tmp_path)


def test_unreadable_ledger_is_skipped_not_fatal(tmp_path) -> None:
    write_record(tmp_path, "good", 5.0)
    bad = citizen_path("bad", tmp_path)
    bad.write_text("{{{", encoding="utf-8")

    assert len(load_all_citizens(tmp_path)) == 1
    assert "@good" in generate_leaderboard(tmp_path)
