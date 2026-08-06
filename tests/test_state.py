"""The citizen ledger: round-tripping, degradation, and the streak bug."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shodann.state import (
    KIND_AGENT,
    QUARANTINE_DIRNAME,
    SCHEMA_VERSION,
    TREND_ASCENDING,
    TREND_NEW,
    VISIBILITY_ANONYMOUS,
    VISIBILITY_NAMED,
    CitizenRecord,
    Display,
    assigned_handle,
    citizen_path,
    compute_trend,
    load_citizen_history,
    quarantine_dir,
    save_citizen_history,
)
from shodann.velocity import CodeMetrics, calculate_velocity

LIVE_LEDGER = Path(__file__).parent.parent / ".shodann" / "citizens" / "norrisaftcc.json"


def submit(root, citizen="octocat", *, coverage=30.0, test_count=3, iterations=2, previous=None):
    current = CodeMetrics(coverage=coverage, test_count=test_count)
    result = calculate_velocity(current, previous, iterations)
    return save_citizen_history(citizen, current, result, root), result


def quarantined(root) -> list[Path]:
    directory = quarantine_dir(root)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


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


def test_channel_is_stored_on_the_citizen_record(tmp_path) -> None:
    submit(tmp_path, citizen="octocat")
    record = save_citizen_history(
        "octocat",
        CodeMetrics(coverage=45.0),
        calculate_velocity(CodeMetrics(coverage=45.0), None, 1),
        tmp_path,
        channel="algocratic/futures",
    )

    assert record.channel == "algocratic/futures"
    reloaded = load_citizen_history("octocat", tmp_path, channel="algocratic/futures")
    assert reloaded.channel == "algocratic/futures"

    payload = json.loads(citizen_path("octocat", tmp_path).read_text(encoding="utf-8"))
    assert payload["channel"] == "algocratic/futures"


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


def test_nobody_is_conscripted_into_a_public_ranking(tmp_path) -> None:
    """S1-14. This test asserted `Display().label(...) == "@octocat"`.

    It was green, and it was pinning the defect. `PRD.md`:448 - "nobody is
    conscripted into a public ranking of their coursework" - and the `Display`
    docstring - "opt-in by name, never by default" - both said the opposite of
    the field beneath them, and the test agreed with the field. Nothing
    prompts a citizen to open their ledger, so the default *was* the policy for
    every citizen who ever existed.

    Latent until S1-12 built the thing that publishes. Asserted end to end
    through a real save rather than on `Display` alone, because the defect was
    never in the dataclass in isolation - it was in what a review writes for a
    citizen who never chose.
    """
    submit(tmp_path, citizen="octocat")
    record = load_citizen_history("octocat", tmp_path)

    assert record.display.visibility == VISIBILITY_ANONYMOUS
    assert record.display.label("octocat") == assigned_handle("octocat")
    assert "octocat" not in record.display.label("octocat")


def test_choosing_to_be_named_still_works_and_survives_a_reload(tmp_path) -> None:
    """Opt-in has to be reachable, or the default is not a default but a wall."""
    path = citizen_path("loud", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"citizen": "loud", "display": {"visibility": VISIBILITY_NAMED}}),
        encoding="utf-8",
    )

    assert load_citizen_history("loud", tmp_path).display.label("loud") == "@loud"

    submit(tmp_path, citizen="loud")
    assert load_citizen_history("loud", tmp_path).display.visibility == VISIBILITY_NAMED, (
        "a stored choice must survive the write that follows it"
    )


def test_assigned_handles_are_stable_and_distinct() -> None:
    """US-3.2 requires every citizen to appear, which a constant string defeats.

    "Citizen-Anonymous" listed eleven times has shown one citizen eleven times.
    Stability matters for the same reason: a handle that moved between runs
    would make a citizen's own row untrackable to them, which is the one reader
    the row exists for.
    """
    assert assigned_handle("octocat") == assigned_handle("octocat")
    assert assigned_handle("octocat") != assigned_handle("octodog")
    assert "octocat" not in assigned_handle("octocat")


# -- S1-15: a ledger we cannot read is not a ledger we may destroy -----------


def test_corrupt_ledger_is_preserved_before_it_is_overwritten(tmp_path) -> None:
    """S1-15. The degradation used to be terminal: load failed, a blank record
    came back, and the very next save overwrote the only copy of the citizen's
    history. One conflict marker erased a growth record silently and forever.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = '<<<<<<< HEAD\n{"citizen": "octocat", "pr_count": 14}\n=======\n'
    path.write_text(original, encoding="utf-8")

    submit(tmp_path)

    kept = quarantined(tmp_path)
    assert len(kept) == 1, "the unreadable bytes must survive the overwrite"
    assert kept[0].read_text(encoding="utf-8") == original
    assert "corrupt" in kept[0].name
    # And the citizen still got their review recorded, per PRD section 8.
    assert load_citizen_history("octocat", tmp_path).pr_count == 1


def test_an_absent_ledger_is_a_new_citizen_and_not_damage(tmp_path) -> None:
    """Absent is not corrupt, and the two used to be indistinguishable - both
    arrived as an identical default record, which is why nothing could tell
    "new citizen" from "wreckage" at write time (S1-15).

    The flag is asserted directly, not only through its consequence. Collapsing
    the two cases happens to quarantine nothing anyway, because there is no
    file to move - so a test that checked only the directory would stay green
    with the distinction deleted, which is EARLY_RUNS 13 exactly.
    """
    record = load_citizen_history("newcomer", tmp_path)
    assert record.unreadable_source is None, "an absent file is not a damaged one"

    submit(tmp_path, citizen="newcomer")
    assert quarantined(tmp_path) == []


def test_quarantine_names_are_legal_on_windows(tmp_path) -> None:
    """`.github/workflows/tests.yml` gates this suite on Windows as well as
    Linux, where a colon in a filename is illegal - so the ISO timestamp cannot
    go into the name as written. On Linux the bad name would simply work, which
    is why this is asserted rather than left to the first corrupt ledger on a
    laptop.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json at all", encoding="utf-8")

    save_citizen_history(
        "octocat",
        CodeMetrics(coverage=30.0),
        calculate_velocity(CodeMetrics(coverage=30.0), None, 1),
        tmp_path,
        now="2026-07-29T02:49:00Z",
    )

    (kept,) = quarantined(tmp_path)
    assert kept.name == "octocat.corrupt-20260729T024900Z.json"
    assert not set(kept.name) & set(':*?"<>|')


def test_a_ledger_in_the_wrong_encoding_is_preserved_not_raised(tmp_path) -> None:
    """`read_clearance` already caught `UnicodeDecodeError` and `OSError`; this
    path caught neither, so a truncated or mis-encoded ledger raised out of the
    review instead of degrading. Same policy in both, not two policies.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'{"citizen": "octocat", "pr_count": \xff\xfe}')

    record = load_citizen_history("octocat", tmp_path)
    assert record.pr_count == 0
    assert record.unreadable_source == path

    submit(tmp_path)
    assert len(quarantined(tmp_path)) == 1


def test_two_corrupt_runs_do_not_overwrite_each_others_quarantine(tmp_path) -> None:
    """A conflict marker survives until someone resolves it, so the second run
    finds the same damage. The first preserved copy is the valuable one.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text("first wreck", encoding="utf-8")
    submit(tmp_path)
    path.write_text("second wreck", encoding="utf-8")
    submit(tmp_path)

    kept = {p.read_text(encoding="utf-8") for p in quarantined(tmp_path)}
    assert kept == {"first wreck", "second wreck"}


def test_a_failed_quarantine_still_writes_the_ledger(tmp_path, monkeypatch) -> None:
    """Preserving history must never become a second way to lose a review. A
    read-only checkout or a full disk is a reason to carry on, not to raise.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json at all", encoding="utf-8")

    def refuse(self, target):
        raise OSError("read-only file system")

    # `Path.replace` is quarantine's move; `atomic_write` uses `os.replace`,
    # so the write under test is untouched by this patch.
    monkeypatch.setattr(Path, "replace", refuse)

    record, _ = submit(tmp_path)
    assert record.pr_count == 1
    assert load_citizen_history("octocat", tmp_path).pr_count == 1


def test_quarantine_hides_from_the_leaderboard_glob(tmp_path) -> None:
    """`leaderboard.load_all_citizens` globs `*.json` non-recursively over the
    citizens directory. A preserved copy left beside the original would read
    back as a second citizen - harmless for unparseable bytes, a duplicate row
    for a schema-downgrade copy, which is valid JSON.
    """
    from shodann.leaderboard import load_all_citizens

    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"citizen": "octocat", "pr_count": 9}), encoding="utf-8")
    # Readable, but written by a SHODANN from the future.
    path.write_text(
        json.dumps({"citizen": "octocat", "pr_count": 9, "schema_version": 99}),
        encoding="utf-8",
    )

    submit(tmp_path)

    assert len(quarantined(tmp_path)) == 1
    # Nested, not a sibling filename - that nesting is the whole mechanism.
    assert quarantine_dir(tmp_path) == path.parent / QUARANTINE_DIRNAME
    assert [r.citizen for r in load_all_citizens(tmp_path)] == ["octocat"]


# -- S1-19: a versioned ledger that does not eat what it cannot read ---------


def test_unknown_keys_survive_a_round_trip(tmp_path) -> None:
    """S1-19. `to_dict` emitted a fixed key list and `from_dict` read one, so a
    ledger written by a newer SHODANN lost every unrecognised key on its next
    write - in the one file a student's whole history lives in.
    """
    record = CitizenRecord.from_dict(
        {
            "citizen": "octocat",
            "pr_count": 4,
            "peer_reviews_given": 7,
            "cohort": {"name": "spring", "week": 3},
        }
    )
    assert record.extra == {"peer_reviews_given": 7, "cohort": {"name": "spring", "week": 3}}

    payload = record.to_dict()
    assert payload["peer_reviews_given"] == 7
    assert payload["cohort"] == {"name": "spring", "week": 3}
    assert CitizenRecord.from_dict(payload) == record


def test_unknown_keys_reach_the_written_file(tmp_path) -> None:
    """Round-tripping in memory is not the property that matters; surviving the
    write is. The data loss happened on disk.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"citizen": "octocat", "pr_count": 4, "peer_reviews_given": 7}),
        encoding="utf-8",
    )

    submit(tmp_path)

    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    assert raw["peer_reviews_given"] == 7
    assert raw["pr_count"] == 5, "a key this build maintains is still this build's"


def test_a_known_key_is_never_shadowed_by_a_stale_unknown() -> None:
    """`extra` preserves, it does not win. If the two ever collided, the ledger
    would serve a stale copy of a field the build actively maintains.
    """
    record = CitizenRecord(citizen="octocat", pr_count=3, extra={"pr_count": 999})
    assert record.to_dict()["pr_count"] == 3


def test_schema_version_is_written_and_absent_means_one(tmp_path) -> None:
    """Every ledger written before versioning existed is version 1 by
    construction - including the live record, which is why absence is not an
    error and not a zero.
    """
    submit(tmp_path)
    with citizen_path("octocat", tmp_path).open(encoding="utf-8") as handle:
        assert json.load(handle)["schema_version"] == SCHEMA_VERSION

    assert CitizenRecord.from_dict({"citizen": "octocat"}).schema_version == 1


def test_a_ledger_from_the_future_is_preserved_before_a_downgrade(tmp_path) -> None:
    """The version field has to be branched on or it is decoration. This is the
    branch: a stored version above ours means at least one key we recognise
    means something else now, so the original is kept and we stamp what we
    actually wrote rather than re-asserting a version we cannot honour.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    future = {"citizen": "octocat", "pr_count": 11, "schema_version": 99, "streak_kind": "merges"}
    path.write_text(json.dumps(future), encoding="utf-8")

    submit(tmp_path)

    kept = quarantined(tmp_path)
    assert len(kept) == 1
    assert "schema-v99" in kept[0].name
    assert json.loads(kept[0].read_text(encoding="utf-8")) == future

    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    assert raw["schema_version"] == SCHEMA_VERSION, "claim the version we wrote"
    assert raw["streak_kind"] == "merges", "and still lose nothing we did not understand"


def test_a_same_version_ledger_is_not_quarantined(tmp_path) -> None:
    """Otherwise every ordinary submission mints a copy and the directory grows
    without bound.
    """
    submit(tmp_path)
    submit(tmp_path, coverage=45.0, test_count=6)
    assert quarantined(tmp_path) == []


def test_to_dict_key_order_is_unchanged_and_new_keys_are_appended() -> None:
    """Other modules and the live file read this shape. New keys go last so no
    existing key moves - the diff against a live ledger stays additive.
    """
    keys = list(CitizenRecord(citizen="octocat").to_dict())
    assert keys[:16] == [
        "citizen",
        "kind",
        "display",
        "clearance_level",
        "first_submission",
        "last_updated",
        "baseline_established",
        "pr_count",
        "iteration_streak",
        "rage_state_encounters",
        "last_metrics",
        "last_velocity",
        "velocity_trend",
        "velocity_history",
        "last_degradation",
        "coverage_instrumented",
    ]
    assert keys[16:] == ["channel", "discontinuities", "schema_version"]


def test_no_maintained_key_leaks_into_extra() -> None:
    """The unknown-key set is derived from `to_dict` rather than restated, and
    this is the assertion that the derivation holds: a key written by this
    build must never come back as an unknown, or it would be written twice and
    `setdefault` would serve the stale copy.
    """
    record = CitizenRecord(citizen="octocat", pr_count=2)
    assert CitizenRecord.from_dict(record.to_dict()).extra == {}


# -- S1-23: the streak counts submissions, not wins --------------------------


def test_a_positive_submission_extends_the_streak(tmp_path) -> None:
    submit(tmp_path)
    _, result = submit(tmp_path, coverage=45.0, test_count=6)
    assert result.score > 0
    assert load_citizen_history("octocat", tmp_path).iteration_streak == 2


def test_a_negative_submission_also_extends_the_streak(tmp_path) -> None:
    """S1-23, decided 2026-07-29: the streak counts submissions, not wins.

    The old one-liner reset it on any non-positive score, which contradicted
    two invariants at once - iteration can never subtract, and no branch is
    punitive. A citizen deleting dead code scores negative and gets
    "Refactoring phase detected" from the engine while the ledger took their
    streak away for the same act. The leaderboard column already says what
    this measures: "**Submissions**: total PRs, because consistency matters".
    """
    submit(tmp_path)
    assert load_citizen_history("octocat", tmp_path).iteration_streak == 1

    _, result = submit(
        tmp_path,
        coverage=0.0,
        test_count=0,
        iterations=0,
        previous=CodeMetrics(coverage=90.0, test_count=50),
    )
    assert result.score < 0, "the fixture has to actually score negative to guard anything"
    assert load_citizen_history("octocat", tmp_path).iteration_streak == 2


# -- S1-16 / S1-17 / S1-39: the live record is annotated, never rewritten -----


def test_discontinuities_default_empty_and_round_trip() -> None:
    """Defaulting empty is what keeps every other citizen file unaffected."""
    assert CitizenRecord(citizen="newcomer").to_dict()["discontinuities"] == []

    seam = {
        "date": "2026-07-29T00:00:00Z",
        "fields": ["last_metrics.complexity"],
        "kind": "unit_change",
        "note": "def count before, C901 count after",
    }
    record = CitizenRecord(citizen="octocat", discontinuities=[seam])
    assert CitizenRecord.from_dict(record.to_dict()).discontinuities == [seam]


def test_discontinuities_survive_a_write(tmp_path) -> None:
    """The annotation has to outlive the next review, or it is a note that the
    system deletes for you.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    seam = {"date": "2026-07-29", "fields": ["pr_count"], "kind": "counting_change", "note": "x"}
    path.write_text(json.dumps({"citizen": "octocat", "discontinuities": [seam]}), encoding="utf-8")

    record, _ = submit(tmp_path)
    assert record.discontinuities == [seam]
    assert load_citizen_history("octocat", tmp_path).discontinuities == [seam]


@pytest.fixture(scope="module")
def live_ledger() -> dict:
    with LIVE_LEDGER.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_the_live_record_annotates_its_three_known_seams(live_ledger: dict) -> None:
    """S1-16, S1-17, S1-39. Each is a stored figure that is honest about what
    the instrument did and misleading about what a reader assumes it means.
    """
    seams = live_ledger["discontinuities"]
    assert len(seams) == 3
    for seam in seams:
        assert set(seam) == {"date", "fields", "kind", "note"}
        assert seam["note"].strip(), "a seam with no prose explains nothing"

    covered = {field for seam in seams for field in seam["fields"]}
    assert {"pr_count", "iteration_streak"} <= covered, "S1-16: counters counted pushes"
    assert "velocity_history" in covered, "S1-17: the 410.0 residue"
    assert "last_metrics.complexity" in covered, "S1-39: def count became C901 count"


def test_the_live_record_was_annotated_and_not_corrected(live_ledger: dict) -> None:
    """The whole point of the annotation is that the numbers stand. Editing a
    stored metric to what it should have been is the one edit this repository
    refuses - it is why the spurious first baseline was deleted rather than
    fixed (EARLY_RUNS 1). This pins the figures the seams describe.

    Pinned by *direction*, not by value, and the distinction is the whole test.
    The first version asserted `pr_count == 19` against a file the shipped
    workflow rewrites on every merge to the default branch - so it was green
    when written and would have gone red on the merge that landed it, accusing
    a maintainer of correcting a ledger figure that SHODANN's own writer had
    incremented. A correction of the S1-16 overcount would take these counters
    *down*, to roughly the seven merges that actually shipped; a merge only
    ever takes them up. `>=` separates those two, and a test that survives its
    own subject changing under it is the only kind worth having here.

    The 410.0 assertion is left as an exact membership check on purpose, and it
    is a fuse rather than a bomb: the entry sits in a ten-deep newest-first ring
    and will be evicted by ordinary use, at which point this line fails while
    the seam annotation describing it remains. That is the correct moment to
    revisit whether an annotation should outlive the datum it annotates - a
    question this rung has not answered, and one nobody should have to
    rediscover from a red suite with no explanation attached.
    """
    assert live_ledger["pr_count"] >= 19, "a correction would reduce this, a merge raises it"
    assert live_ledger["iteration_streak"] >= 19
    assert live_ledger["pr_count"] == live_ledger["iteration_streak"], (
        "S1-23 made both counters unconditional, so they cannot diverge again"
    )
    assert live_ledger["last_metrics"]["complexity"] == 0
    assert 410.0 in [entry["score"] for entry in live_ledger["velocity_history"]]


def test_the_live_record_still_loads(live_ledger: dict) -> None:
    """An annotation that broke the reader would be worse than no annotation."""
    record = CitizenRecord.from_dict(live_ledger)
    assert record.citizen == "norrisaftcc"
    assert record.schema_version == 1, "written before versioning; absent means 1"
    assert record.extra == {}
    assert len(record.discontinuities) == 3


# --- what a hand-edited ledger may and may not do ---------------------------


@pytest.mark.parametrize(
    "stored", ["false", "true", "0", "no", "yes", 1, 0, None, [], {}, "True"]
)
def test_only_a_literal_true_marks_coverage_as_measured(stored) -> None:
    """`bool("false")` is True, and the consequence is a fabricated gain.

    Reported by Copilot on #61. Python reads every non-empty string as truthy, so
    a hand-written `"coverage_instrumented": "false"` meant the exact opposite of
    what its author typed - and this flag is what `review.reconcile_coverage`
    consults to decide whether a coverage delta may be claimed at all. The wrong
    answer here manufactures a gain nobody earned, which is EARLY_RUNS 9 with a
    new cause. `"0"`, `"no"` and even `"True"` all read True under `bool`.

    Everything that is not literally `true` reads as unmeasured, which is the
    safe direction on purpose: an unreadable flag means we do not know, and not
    knowing means claiming nothing. Under-claiming costs a citizen a
    celebration; over-claiming tells them they achieved something they did not.
    """
    record = CitizenRecord.from_dict({"citizen": "octocat", "coverage_instrumented": stored})
    assert record.coverage_instrumented is False


def test_a_real_true_still_reads_as_measured() -> None:
    """The strictness must not cost the case that matters - the live record."""
    assert CitizenRecord.from_dict(
        {"citizen": "octocat", "coverage_instrumented": True}
    ).coverage_instrumented is True

    with LIVE_LEDGER.open(encoding="utf-8") as handle:
        assert CitizenRecord.from_dict(json.load(handle)).coverage_instrumented is True


@pytest.mark.parametrize("stored", ["not-a-number", "", "1.5.2", [], {}, None])
def test_an_unreadable_schema_version_does_not_deny_a_review(stored, tmp_path) -> None:
    """Found by checking the neighbour of Copilot's finding, two lines away.

    `int(data.get("schema_version", 1))` raises `ValueError` on any non-numeric
    string, and `load_citizen_history` catches `OSError`, `UnicodeDecodeError`,
    `json.JSONDecodeError`, `KeyError` and `TypeError` - not `ValueError`.
    `json.JSONDecodeError` *is* a `ValueError` subclass, which is what makes it
    easy to miss: the tuple looks like it covers the family and catches one
    member of it.

    So one mistyped version raised out of `from_dict`, past the degradation path,
    and denied that citizen their review - which PRD section 8 forbids in as many
    words. Every other unreadable thing in this module degrades to a default.
    Copilot's finding was a wrong value; this one is a citizen losing their
    feedback, and it was adjacent to it.
    """
    path = citizen_path("octocat", tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"citizen": "octocat", "schema_version": stored}), encoding="utf-8"
    )

    record = load_citizen_history("octocat", tmp_path)

    assert record.schema_version == SCHEMA_VERSION, "unreadable means 1, like absent"
    assert record.citizen == "octocat", "and the citizen still gets a review"
