"""The leaderboard mirror: everyone appears, and only by consent."""

from __future__ import annotations

import json

import pytest

from shodann.leaderboard import ClearanceRequired, generate_leaderboard, load_all_citizens
from shodann.state import (
    KIND_AGENT,
    VISIBILITY_ANONYMOUS,
    VISIBILITY_NAMED,
    CitizenRecord,
    Display,
    assigned_handle,
    citizen_path,
)


def write_record(root, citizen, velocity, *, anonymous=False, handle=None, pr_count=1):
    # Named is stated, never taken from the default - S1-14 flipped that default
    # to anonymous, and seventeen tests here failed because they had been
    # asserting `@username` while relying on a default that was the defect. The
    # subject of these tests is ranking and partitioning, so consent is declared
    # rather than assumed; a fixture that silently agrees with the production
    # default cannot notice when that default is wrong.
    record = CitizenRecord(
        citizen=citizen,
        last_velocity=velocity,
        pr_count=pr_count,
        display=(
            Display(visibility=VISIBILITY_ANONYMOUS, handle=handle)
            if anonymous
            else Display(visibility=VISIBILITY_NAMED)
        ),
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
    # Declared, for the same reason as `write_record` - and worth a note, since
    # `Display`'s default is now anonymous for every `kind`. An agent has no
    # privacy interest to protect, so whoever registers one sets its display
    # block; the default protects people, and applying it uniformly is simpler
    # than a `kind`-dependent one and wrong in no case that matters.
    record = CitizenRecord(
        citizen=name,
        kind=KIND_AGENT,
        last_velocity=velocity,
        pr_count=9,
        display=Display(visibility=VISIBILITY_NAMED),
    )
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
    """A missing discriminator must not make a citizen vanish from their own board.

    It asserted `@legacy` until S1-14, and the change of assertion is the point
    rather than a concession to it: a record carrying no `display` block has, by
    construction, nobody who chose to be named, so it now appears under an
    assigned handle. Both halves matter and they are different claims - a
    missing `kind` must not remove a citizen from the board, and a missing
    `display` must not put their username on it.
    """
    path = citizen_path("legacy", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"citizen": "legacy", "last_velocity": 3.0}), encoding="utf-8")

    document = generate_leaderboard(tmp_path)
    assert assigned_handle("legacy") in document, "a missing kind partitions as human"
    assert "@legacy" not in document, "a missing display block is not consent"


def test_unreadable_ledger_is_skipped_not_fatal(tmp_path) -> None:
    write_record(tmp_path, "good", 5.0)
    bad = citizen_path("bad", tmp_path)
    bad.write_text("{{{", encoding="utf-8")

    assert len(load_all_citizens(tmp_path)) == 1
    assert "@good" in generate_leaderboard(tmp_path)


def test_one_undecodable_byte_does_not_empty_the_whole_board(tmp_path) -> None:
    """S1-22. `UnicodeDecodeError` was not caught, so one bad byte cost everyone.

    The previous test passes with the old except clause: `json.JSONDecodeError`
    covers a file whose *contents* are malformed. This one is about a file that
    cannot become text at all - a latin-1 byte from an editor with the wrong
    default, which is a plausible thing to find in a student's repository. That
    raised out of the `for` loop, discarding `records` entirely, so the board
    lost every citizen because of one file belonging to one of them.
    """
    write_record(tmp_path, "alpha", 5.0)
    write_record(tmp_path, "zeta", 7.0)
    mojibake = citizen_path("mojibake", tmp_path)
    # Valid JSON in latin-1; the 0xE9 is `é`, which is not valid UTF-8 alone.
    mojibake.write_bytes(b'{"citizen": "mojibake", "display": {"handle": "Caf\xe9"}}')

    assert sorted(record.citizen for record in load_all_citizens(tmp_path)) == ["alpha", "zeta"]
    document = generate_leaderboard(tmp_path)
    assert "@alpha" in document
    assert "@zeta" in document


def test_a_ledger_that_cannot_be_opened_does_not_empty_the_board(tmp_path) -> None:
    """The `OSError` half of S1-22, and the half a permissions test cannot check.

    A ledger truncated mid-write, on a mount that went away, or left unopenable
    by a permissions mishap all arrive as `OSError`. A directory standing where
    a `*.json` file is expected reproduces that on every platform this suite
    gates on - `IsADirectoryError` on Linux, `PermissionError` on Windows, both
    `OSError` - whereas `chmod` is a no-op on Windows and would make this guard
    silently vacuous there.
    """
    write_record(tmp_path, "alpha", 5.0)
    (citizen_path("alpha", tmp_path).parent / "ghost.json").mkdir()

    assert [record.citizen for record in load_all_citizens(tmp_path)] == ["alpha"]
    assert "@alpha" in generate_leaderboard(tmp_path)


# --- S1-44: a figure the record itself says is wrong ------------------------


def write_seamed(root, citizen, velocity, fields, *, pr_count=19):
    record = CitizenRecord(
        citizen=citizen,
        last_velocity=velocity,
        pr_count=pr_count,
        display=Display(visibility=VISIBILITY_NAMED),
        discontinuities=[{"date": "2026-07-25T00:00:00Z", "fields": list(fields), "note": "x"}],
    )
    path = citizen_path(citizen, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict()), encoding="utf-8")


def test_a_seamed_figure_is_marked_and_explained(tmp_path) -> None:
    """S1-44. The annotation reached a reader of the JSON and nobody else.

    The live record states that its `pr_count` counts write events rather than
    merges and that the stored 19 is roughly seven real deliveries. The first
    METRICS.md ever generated printed "Submissions: 19" with nothing attached,
    to the one audience the board exists for. The figure still stands -
    correcting a stored metric is the edit this repository refuses - so the
    reader is told instead.
    """
    write_seamed(tmp_path, "seamed", 149.5, ["pr_count", "iteration_streak"])

    document = generate_leaderboard(tmp_path)
    row = next(line for line in document.splitlines() if "@seamed" in line)

    assert "19*" in row, "the Submissions figure spans a discontinuity"
    assert "149.5*" not in row, "last_velocity carries no seam and must not be marked"
    assert "spans a recorded discontinuity" in document, "a mark with no key is noise"


def test_a_seam_on_an_unpublished_field_marks_nothing(tmp_path) -> None:
    """`last_metrics.complexity` carries a seam on the live record and appears
    in no column. Marking every row because something invisible moved trains a
    reader to ignore the mark, which costs more than it buys."""
    write_seamed(tmp_path, "quiet", 5.0, ["last_metrics.complexity"])

    document = generate_leaderboard(tmp_path)

    assert "*" not in document.split("Growth Philosophy")[0].split("Rankings")[1]
    assert "spans a recorded discontinuity" not in document


def test_a_clean_record_carries_no_footnote(tmp_path) -> None:
    write_record(tmp_path, "clean", 5.0)
    assert "spans a recorded discontinuity" not in generate_leaderboard(tmp_path)
