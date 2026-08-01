"""The citizen ledger.

One JSON file per citizen at ``.shodann/citizens/{citizen}.json``, living in
the repository being reviewed. That file is the authoritative record; the
course-level ``METRICS.md`` is a derived mirror, and if the two disagree the
citizen's own file wins.

Schema decided 2026-07-25 (see PRD section 8): snake_case throughout, numbers
unquoted, a ``kind`` discriminator so agent citizens can share the registry,
and a ``display`` block so appearing on the leaderboard under one's own name
is a choice rather than an assumption.

Two properties added 2026-07-29, both about a ledger outliving the build that
wrote it. It is versioned (:data:`SCHEMA_VERSION`) and it round-trips keys it
does not recognise, so a file written by a newer SHODANN and read by an older
one loses nothing; and a file this build cannot read is moved aside rather
than overwritten, so degrading to a fresh record never destroys the growth
record it degraded away from.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .config import DEFAULT_CONFIG, VelocityConfig
from .velocity import CodeMetrics, VelocityResult

__all__ = [
    "CITIZENS_DIR",
    "CLEARANCES_FILE",
    "DEFAULT_CLEARANCE",
    "DISCONTINUITY_COUNTING_CHANGE",
    "DISCONTINUITY_DEFECT_RESIDUE",
    "DISCONTINUITY_UNIT_CHANGE",
    "QUARANTINE_DIRNAME",
    "SCHEMA_VERSION",
    "CitizenRecord",
    "Display",
    "assigned_handle",
    "atomic_write",
    "citizen_path",
    "load_citizen_history",
    "quarantine_dir",
    "read_clearance",
    "save_citizen_history",
    "utcnow",
]
# Still omits seven names that four modules import, including `clearance_name`
# - S1-26 in the sprint backlog. Left alone rather than fixed in passing.

CITIZENS_DIR = Path(".shodann/citizens")

QUARANTINE_DIRNAME = "quarantine"
"""Sub-directory of `CITIZENS_DIR` holding ledgers that were moved aside.

A *sub-directory* rather than a sibling filename, and the reason is in another
module: `leaderboard.load_all_citizens` globs `*.json` non-recursively over the
citizens directory, so a preserved copy left beside the original would be read
back as a second citizen. That is fine for a corrupt file - it fails to parse
and is skipped - but a schema-downgrade copy is valid JSON and would appear as
a duplicate row. Nesting it costs nothing and needs no change there.
"""


def quarantine_dir(root: Path | str = ".") -> Path:
    """Where preserved ledgers land beneath ``root``. Created only when used."""
    return Path(root) / CITIZENS_DIR / QUARANTINE_DIRNAME


CLEARANCES_FILE = Path(".shodann/clearances.json")
"""Where a citizen's band is set, in their own repository.

The ledger stores `clearance_level` and always has, but nothing ever wrote it
to anything but its default - so every citizen was permanently RED and the
INFRARED and BLUE+ branches were built, tested, and unreachable. This file is
the missing source.

It is deliberately the instructor's to set, not SHODANN's to infer. A band
inferred from readings is a second score, and the whole product rests on
improvement outranking position; `prompts/03`'s `INFER_CLEARANCE` sketch is
declined for that reason and not merely unimplemented.

It lives in the citizen's repository rather than a central store, for the same
reason the ledger does: local truth, and a student can read the file that
governs how they are spoken to.
"""

DEFAULT_CLEARANCE = 2
"""RED. Everyone starts here.

INFRARED is an onboarding state rather than a tracked one - a citizen without
a GitHub account has no record to hold a band. It stays in the ladder because
the register defines it and the renderer must not fail on it, not because a
citizen is expected to sit there.
"""

SCHEMA_VERSION = 1
"""The ledger shape this build writes, and the shape it claims to understand.

S1-19: `to_dict` emitted a fixed key list and `from_dict` read a fixed key
list, so a ledger written by a newer SHODANN lost every key this build had
never heard of on its next write - silently, and in the one file the student's
whole history lives in. Cross-repo drift is the normal case here, not the
exotic one: the ledger lives in the citizen's repository and the code lives in
the course repository, so the two versions are only ever coincidentally equal.

**The rule this field establishes**, stated so a later reader can act on it:

* **Adding a key never bumps the version.** Unknown keys round-trip through
  `CitizenRecord.extra`, so an addition is already forward-compatible. The
  version moves only when an existing key changes *meaning, units or type* -
  the class of change that makes a stored number and a fresh one
  incomparable, which is exactly what `discontinuities` documents per-file.
* **A reader whose `SCHEMA_VERSION` is greater than the stored one owes a
  migration** for every version it skipped. There is one version today, so
  there is no migration; the field exists so that the first bump has somewhere
  to branch instead of guessing from which keys happen to be present.
* **A reader whose `SCHEMA_VERSION` is *less* than the stored one is reading
  from the future.** It keeps reading - refusing would deny a citizen their
  review, which PRD section 8 forbids - but on write it stamps its own version
  and preserves the original first (see `_preserve`), because by the rule
  above a higher stored version means at least one key it just wrote means
  something different from what it read.
* **Absent means 1.** Every ledger written before this field existed is
  version 1 by construction; the live record is one of them.
"""

DISCONTINUITY_UNIT_CHANGE = "unit_change"
"""A stored field kept its name and changed what it measures."""

DISCONTINUITY_COUNTING_CHANGE = "counting_change"
"""A counter kept counting, but of a different event."""

DISCONTINUITY_DEFECT_RESIDUE = "defect_residue"
"""A stored figure is the output of a defect, retained rather than corrected."""

TREND_NEW = "new"
TREND_ASCENDING = "ascending"
TREND_DESCENDING = "descending"
TREND_STABLE = "stable"

KIND_HUMAN = "human"
KIND_AGENT = "agent"

CLEARANCE_NAMES = {
    1: "INFRARED",
    2: "RED",
    3: "ORANGE",
    4: "YELLOW",
    5: "GREEN",
    6: "BLUE+",
}
"""Clearance ladder. Anything above 6 is BLUE+; see design_docs/CLEARANCE_REGISTER.md."""


def clearance_name(level: int) -> str:
    """Name for a clearance level, saturating at BLUE+ rather than failing."""
    return CLEARANCE_NAMES.get(max(1, min(level, 6)), "RED")

VISIBILITY_NAMED = "named"
VISIBILITY_ANONYMOUS = "anonymous"


def utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assigned_handle(citizen: str) -> str:
    """A stable stand-in name for a citizen who has not chosen to be named.

    `PRD.md`:448 offers two ways to appear - "under their GitHub username or an
    assigned handle" - and until an instructor assigns one, something has to
    fill the second slot. The obvious filler does not work: a constant string
    makes every unnamed citizen render identically, which collides with US-3.2's
    requirement that *all* citizens appear. A board listing "Citizen-Anonymous"
    eleven times has not shown eleven citizens.

    Derived from the username so it is stable without being stored. A citizen
    who opts out and back in gets the same handle both times, their row keeps
    its identity across runs, and no migration is needed for records written
    before this existed.

    This is pseudonymity, not anonymity, and the difference matters enough to
    write down. A course roster is a small domain, so anyone holding the list
    of usernames can recover the mapping by trying them all - which is minutes
    of work, not a research project. What it defends against is the thing that
    actually happens: a public repository indexed by a search engine, tying a
    named person to a ranking of their coursework, forever, for a class they
    took once. Nobody with the roster is learning anything they did not know.
    """
    digest = hashlib.sha256(citizen.encode("utf-8")).hexdigest()[:6].upper()
    return f"Citizen-{digest}"


@dataclass
class Display:
    """Leaderboard participation. Opt-in by name, never by default.

    That sentence was here before the field beneath it agreed with it. The
    default was `named`, so a citizen who never opened this file - which is
    every citizen, since nothing prompts them to - was published on a public
    leaderboard under their GitHub username, and opting out meant hand-editing
    JSON they did not know existed. `PRD.md`:448 is unambiguous: "nobody is
    conscripted into a public ranking of their coursework." The code disagreed
    with the PRD and with its own docstring, and the docstring lost.

    It was harmless only because nothing published. S1-12 built the publisher,
    which is what made this worth fixing in the same change rather than after
    it - a defect that is latent until one specific commit lands should be
    fixed by that commit.

    Records written before this change carry `visibility: "named"` explicitly,
    and `from_dict` keeps what it finds, so the flip does not retroactively
    anonymise anyone. There is exactly one such record and it is the author's.
    Any student ledger created from here on defaults to a handle.
    """

    visibility: str = VISIBILITY_ANONYMOUS
    handle: str | None = None

    def label(self, citizen: str) -> str:
        """What the leaderboard is allowed to print for this citizen."""
        if self.visibility == VISIBILITY_ANONYMOUS:
            return self.handle or assigned_handle(citizen)
        return f"@{citizen}"


@dataclass
class CitizenRecord:
    citizen: str
    channel: str | None = None
    kind: str = KIND_HUMAN
    display: Display = field(default_factory=Display)
    clearance_level: int = 2
    first_submission: str | None = None
    last_updated: str | None = None
    baseline_established: bool = False
    pr_count: int = 0
    iteration_streak: int = 0
    rage_state_encounters: int = 0
    last_metrics: CodeMetrics | None = None
    last_velocity: float = 0.0
    velocity_trend: str = TREND_NEW
    velocity_history: list[dict] = field(default_factory=list)
    last_degradation: str | None = None
    """Why the most recent review went out uninterpreted, or None."""
    coverage_instrumented: bool = False
    """Whether ``last_metrics.coverage`` was measured or is a stand-in zero.

    ``CodeMetrics.coverage`` cannot hold this: it is a float feeding an
    arithmetic engine, and 0.0 there means both *no lines covered* and *nobody
    looked*. Those two need to stay apart in the ledger, because the next
    review subtracts from this number and would otherwise announce a 98-point
    gain to a citizen whose coverage did not move - it was simply measured for
    the first time. Defaults False, so ledgers written before coverage
    instrumentation existed are correctly read as unmeasured.
    """
    discontinuities: list[dict] = field(default_factory=list)
    """Seams in this citizen's own history, where a stored figure stopped
    being comparable to the ones before it.

    S1-16, S1-17 and S1-39 are all the same shape: a number in the live ledger
    that is honest about what the instrument did and misleading about what a
    reader assumes it means. `pr_count` counted pushes and stacked-PR
    double-writes rather than merges; a `velocity_history` entry is residue of
    the absent-vs-zero defect (EARLY_RUNS 9); `complexity` changed from a
    ``def`` count to a ruff `C901` count on 2026-07-29 without changing name.

    The alternative was to correct the figures, and this repository refuses
    that: editing a metric in a ledger to what it should have been is the move
    `oracle-warden` names as the most damaging edit available here, and it is
    why the spurious first baseline was deleted rather than fixed (EARLY_RUNS
    1). So the numbers stand and the seam is written down beside them, in the
    JSON, where anyone reading the file can see it - a note in a source file
    nobody opens would not reach the reader of a `velocity_history`.

    Each entry is ``{"date", "fields", "kind", "note"}``: where the seam falls,
    which stored paths it touches, one of the ``DISCONTINUITY_*`` kinds, and
    prose saying why a delta spanning that date subtracts two different
    quantities. Defaults empty, so every other citizen file is unaffected.
    """
    schema_version: int = SCHEMA_VERSION
    """Which ledger shape this record was read as. See `SCHEMA_VERSION`."""
    extra: dict = field(default_factory=dict)
    """Top-level keys this build does not recognise, carried through unchanged.

    Written back on the next save so an older SHODANN reading a newer ledger
    degrades to *ignoring* what it cannot use rather than deleting it (S1-19).
    Known keys always win on write - `extra` can never shadow a field this
    build actually maintains.
    """
    unreadable_source: Path | None = field(default=None, compare=False, repr=False)
    """Set when this record is a degraded stand-in for a file that failed to load.

    Transient: never serialised, and deliberately not a stored field. It is the
    answer to the question `save_citizen_history` could not previously ask -
    "was this bare record a genuinely new citizen, or the wreckage of one?" -
    because both used to arrive as an identical default `CitizenRecord`
    (S1-15).

    It travels on the record rather than being re-derived at write time on
    purpose. Re-reading the file to decide whether to preserve it would answer
    a question about *a different read*, and a file that became readable (or
    unreadable) in between would be preserved on the wrong evidence. This flag
    is set by the same read that produced the record being written.

    ``compare=False`` because it describes how a record was obtained, not what
    it says; two records with the same history are the same record.
    """

    # -- serialisation -----------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> CitizenRecord:
        display = data.get("display") or {}
        metrics = data.get("last_metrics")
        return cls(
            citizen=data["citizen"],
            channel=data.get("channel"),
            kind=data.get("kind", KIND_HUMAN),
            display=Display(
                visibility=display.get("visibility", VISIBILITY_ANONYMOUS),
                handle=display.get("handle"),
            ),
            clearance_level=data.get("clearance_level", 2),
            first_submission=data.get("first_submission"),
            last_updated=data.get("last_updated"),
            baseline_established=data.get("baseline_established", False),
            pr_count=data.get("pr_count", 0),
            iteration_streak=data.get("iteration_streak", 0),
            rage_state_encounters=data.get("rage_state_encounters", 0),
            last_metrics=CodeMetrics.from_dict(metrics) if metrics else None,
            last_velocity=data.get("last_velocity", 0.0),
            velocity_trend=data.get("velocity_trend", TREND_NEW),
            velocity_history=list(data.get("velocity_history", [])),
            last_degradation=data.get("last_degradation"),
            # `is True`, never `bool(...)`. Python reads every non-empty string as
            # truthy, so a hand-written `"coverage_instrumented": "false"` meant
            # exactly the opposite of what its author typed - and the consequence
            # is not a cosmetic one: `review.reconcile_coverage` consults this to
            # decide whether a coverage delta may be claimed at all, so the wrong
            # answer fabricates a gain nobody earned (EARLY_RUNS 9). `"0"`, `"no"`
            # and `"yes"` all read True as well. Found by Copilot on #61.
            #
            # Anything that is not literally `true` reads as unmeasured, which is
            # the safe direction: an unreadable flag means we do not know, and not
            # knowing means claiming nothing.
            coverage_instrumented=data.get("coverage_instrumented") is True,
            discontinuities=list(data.get("discontinuities", [])),
            # Absent means 1: every ledger written before versioning existed is
            # version 1 by construction, including the live record.
            schema_version=_as_version(data.get("schema_version")),
            # Everything this build has never heard of, kept whole so the next
            # write does not delete a newer SHODANN's fields (S1-19). Computed
            # against `_STORED_KEYS` rather than the dataclass fields, because
            # not every field is stored (`unreadable_source`) and the two sets
            # would drift the moment one of them did.
            extra={k: v for k, v in data.items() if k not in _STORED_KEYS},
        )

    def to_dict(self) -> dict:
        payload = {
            "citizen": self.citizen,
            "channel": self.channel,
            "kind": self.kind,
            "display": asdict(self.display),
            "clearance_level": self.clearance_level,
            "first_submission": self.first_submission,
            "last_updated": self.last_updated,
            "baseline_established": self.baseline_established,
            "pr_count": self.pr_count,
            "iteration_streak": self.iteration_streak,
            "rage_state_encounters": self.rage_state_encounters,
            "last_metrics": self.last_metrics.to_dict() if self.last_metrics else None,
            "last_velocity": self.last_velocity,
            "velocity_trend": self.velocity_trend,
            "velocity_history": list(self.velocity_history),
            "last_degradation": self.last_degradation,
            "coverage_instrumented": self.coverage_instrumented,
            # Appended, never interleaved. Other modules and the live file read
            # this shape, and the two new keys go last so no existing key moves.
            "discontinuities": list(self.discontinuities),
            "schema_version": self.schema_version,
        }
        # `setdefault`, so a stale unknown key can never shadow a field this
        # build maintains - the round trip preserves them, it does not let them
        # win.
        for key, value in self.extra.items():
            payload.setdefault(key, value)
        return payload


_STORED_KEYS = frozenset(CitizenRecord(citizen="_").to_dict())
"""Every top-level key this build writes; anything else is an unknown (S1-19).

Derived from `to_dict` rather than restated, because a hand-maintained copy of
a key list is precisely the thing that drifts - and the failure mode of drift
here is silent: a key that `to_dict` writes but this set omits would be read
back into `extra`, written twice, and the `setdefault` would then quietly
serve the stale copy. `to_dict` is unconditional, so one instantiation names
the whole set.
"""


def citizen_path(citizen: str, root: Path | str = ".") -> Path:
    """Locate a citizen file beneath ``root``.

    ``root`` is explicit because the JS engine resolved its paths against the
    process working directory, which silently wrote state to whatever folder
    the workflow happened to be standing in.
    """
    return Path(root) / CITIZENS_DIR / f"{citizen}.json"


def read_clearance(citizen: str, root: Path | str = ".") -> int | None:
    """The band set for this citizen, or ``None`` if nothing sets one.

    A flat ``{"username": "3"}`` map. Values are strings because
    `shodann-core.yml:98` wrote them that way and an instructor editing this
    file by hand should not have to know which; ints are accepted too.

    ``None`` means *unset*, which is not the same as RED. The caller decides
    what an unset band means, and every failure here is an unset band rather
    than an exception: a citizen must never lose their review because someone
    left a trailing comma in a config file.
    """
    path = Path(root) / CLEARANCES_FILE
    try:
        with path.open(encoding="utf-8") as handle:
            table = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(table, dict):
        return None
    try:
        level = int(table[citizen])
    except (KeyError, TypeError, ValueError):
        return None
    # Saturate rather than reject. A band of 9 is a typo, not grounds for
    # refusing to review someone's work.
    return max(1, min(level, 6))


def _as_version(value) -> int:
    """A stored `schema_version`, or 1 when it is absent or unreadable.

    Was `int(data.get("schema_version", 1))`, which raises `ValueError` on any
    non-numeric string - and `load_citizen_history` catches `OSError`,
    `UnicodeDecodeError`, `json.JSONDecodeError`, `KeyError` and `TypeError`, not
    `ValueError`. `json.JSONDecodeError` *is* a `ValueError` subclass, which is
    what makes this easy to miss: the tuple looks like it covers the family and
    catches only one member of it.

    So one mistyped version in one ledger raised out of `from_dict`, past the
    degradation path, and denied that citizen their review - which PRD section 8
    forbids in as many words. Every other unreadable thing in this module
    degrades to a default; this one crashed.

    Found by checking the neighbour of a defect Copilot reported on #61. The
    reported one was a wrong value; this one is a citizen losing their feedback,
    and it was two lines away.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def load_citizen_history(
    citizen: str,
    root: Path | str = ".",
    *,
    channel: str | None = None,
) -> CitizenRecord:
    """Read a citizen's ledger, or return a fresh record if they are new.

    A malformed file is treated as a new citizen rather than an exception:
    PRD section 8 requires state corruption to degrade to a default, not to
    deny a student their feedback. That much is unchanged.

    What changed (S1-15) is that the degradation used to be *terminal*. The
    fresh record went straight back out through `save_citizen_history`, which
    overwrote the file it had just failed to parse - so one git conflict
    marker in a ledger permanently erased a citizen's entire growth record,
    silently, with nobody told. The record now carries `unreadable_source`,
    naming the file that failed, and the write path preserves it first.

    Two failures are separated here that used to be one. `FileNotFoundError`
    is a genuinely new citizen: there is nothing to preserve, and flagging it
    would mint a quarantine entry on every citizen's first submission.
    Everything else means the file was *there* and could not be read.

    The caught set matches `read_clearance` in this module rather than
    inventing a second policy - `OSError` and `UnicodeDecodeError` included,
    because a ledger truncated mid-write or written in the wrong encoding is
    no more the student's fault than a trailing comma is, and an uncaught
    exception here costs them their review.
    """
    path = citizen_path(citizen, root)
    try:
        with path.open(encoding="utf-8") as handle:
            record = CitizenRecord.from_dict(json.load(handle))
    except FileNotFoundError:
        # Ordered first: it is an OSError subclass, and it is the one absence
        # that must not look like damage.
        return CitizenRecord(citizen=citizen, channel=channel)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        return CitizenRecord(citizen=citizen, channel=channel, unreadable_source=path)
    if channel is not None:
        record.channel = channel
    return record


def compute_trend(history: list[dict]) -> str:
    """Direction over the most recent three scores.

    Returns one of the four values PRD US-3.2 requires. Emoji belong to the
    renderer, not to the ledger.
    """
    if len(history) < 2:
        return TREND_NEW
    recent = [entry["score"] for entry in history[:3]]
    average = sum(recent) / len(recent)
    latest = recent[0]
    if latest > average:
        return TREND_ASCENDING
    if latest < average * 0.8:
        return TREND_DESCENDING
    return TREND_STABLE


def save_citizen_history(
    citizen: str,
    metrics: CodeMetrics,
    result: VelocityResult,
    root: Path | str = ".",
    *,
    config: VelocityConfig = DEFAULT_CONFIG,
    now: str | None = None,
    degradation: str | None = None,
    coverage_instrumented: bool = False,
    channel: str | None = None,
) -> CitizenRecord:
    """Fold one submission into the citizen's ledger and write it atomically.

    The predecessor wrote ``streak`` and read ``iterationStreak``, so streaks
    silently reset to zero on every run. One name, written and read.

    Nothing is overwritten that this build could not read or could not fully
    represent - see `_preserve`. The write itself still goes through
    `atomic_write`, so the sequence is preserve-then-replace and there is no
    moment at which neither copy exists.
    """
    timestamp = now or utcnow()
    record = load_citizen_history(citizen, root, channel=channel)

    if channel is not None:
        record.channel = channel

    record.pr_count += 1
    record.last_metrics = metrics
    # Recorded beside the metrics it qualifies. A run whose analysis job died
    # must not leave last cycle's measured reading looking current.
    record.coverage_instrumented = coverage_instrumented
    record.last_velocity = result.score
    record.last_updated = timestamp
    record.baseline_established = True
    # Recorded whether or not it happened, so a cleared degradation does
    # not leave last cycle's reason looking current.
    record.last_degradation = degradation
    if record.first_submission is None:
        record.first_submission = timestamp

    # The streak counts submissions, not wins - unconditionally, whatever the
    # velocity sign (S1-23, decided 2026-07-29).
    #
    # It used to reset on any non-positive score, which contradicted two
    # product invariants at once: CLAUDE.md states that iteration can never
    # subtract, and that no branch is punitive - a negative score still yields
    # "Refactoring phase detected". A citizen who spent a PR deleting dead
    # code scored negative and lost a streak for doing exactly what the
    # engine's own refactoring branch congratulates them for. That is a
    # penalty for improving the codebase, arriving through the one counter
    # nobody was testing in the losing direction.
    #
    # It is also what the leaderboard already claims to show: the column is
    # "**Submissions**: total PRs, because consistency matters"
    # (`src/shodann/leaderboard.py`). Consistency is the thing being measured,
    # and a refactor is a submission.
    record.iteration_streak += 1

    record.velocity_history = [
        {"score": result.score, "date": timestamp},
        *record.velocity_history,
    ][: config.velocity_history_length]
    record.velocity_trend = compute_trend(record.velocity_history)

    path = citizen_path(citizen, root)
    path.parent.mkdir(parents=True, exist_ok=True)

    if record.unreadable_source is not None:
        # S1-15. The bytes we could not parse are the only copy of this
        # citizen's history; the record about to replace them is a blank.
        _preserve(path, "corrupt", timestamp)
    elif record.schema_version > SCHEMA_VERSION:
        # S1-19. Reading from the future is allowed; overwriting it quietly is
        # not. Unknown keys survive in `extra`, but a higher stored version
        # means at least one key we recognise now means something else, so the
        # original is kept and this build stamps the version it actually
        # wrote.
        _preserve(path, f"schema-v{record.schema_version}", timestamp)
    record.schema_version = SCHEMA_VERSION

    atomic_write(path, json.dumps(record.to_dict(), indent=2) + "\n")
    return record


def _filename_stamp(timestamp: str) -> str:
    """An ISO timestamp reduced to characters a filename may hold.

    ``2026-07-29T02:49:00Z`` becomes ``20260729T024900Z``. Colons are illegal
    in Windows filenames and `.github/workflows/tests.yml` gates this suite on
    Windows as well as Linux, so the naive `str.replace` of the separator is a
    cross-platform break waiting for the first corrupt ledger on a laptop.
    """
    return "".join(character for character in timestamp if character.isalnum())


def _preserve(path: Path, tag: str, timestamp: str) -> Path | None:
    """Move a ledger we are about to overwrite into the quarantine directory.

    Returns where it landed, or ``None`` if there was nothing to preserve or
    the move failed.

    **Failure is not fatal, by design.** Quarantining exists so a citizen does
    not lose their history; it must never become a second way to lose their
    review. A read-only checkout, a full disk, a permissions problem - each is
    a reason to carry on and write, not to raise. PRD section 8's degradation
    rule applies to this code path as much as to the one that created it.

    The move is `Path.replace`, which is a rename within one filesystem and so
    atomic: the file is never half-moved, and `save_citizen_history` calls
    `atomic_write` immediately after, so the pair leaves either the old file
    or the new one on disk at every instant and never neither.

    Timestamped rather than a single ``.corrupt.json``, because the failure
    that produces one of these tends to produce several - a conflict marker
    survives until someone resolves it - and the second run must not overwrite
    the first quarantine with the blank it caused. The collision counter
    covers two failures inside the same second.
    """
    try:
        if not path.exists():
            return None
        destination = path.parent / QUARANTINE_DIRNAME
        destination.mkdir(parents=True, exist_ok=True)
        base = f"{path.stem}.{tag}-{_filename_stamp(timestamp)}"
        target = destination / f"{base}.json"
        collision = 0
        while target.exists():
            collision += 1
            target = destination / f"{base}-{collision}.json"
        path.replace(target)
    except OSError:
        return None
    return target


def atomic_write(path: Path, payload: str) -> None:
    """Write via a temporary file and replace, so a killed job cannot truncate a ledger."""
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    try:
        with handle:
            handle.write(payload)
        os.replace(handle.name, path)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise
