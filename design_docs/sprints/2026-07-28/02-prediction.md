# Commit A — prediction

Written **before** `the_algorithm` is cloned or read. Pushed to origin before the
clone, so the ordering is witnessed by a timestamp neither of us controls.

If the clone predates this file's push, the contamination is visible in the
evidence. That is the point: detectable, not promised.

---

## Honest relabel

This is **not** the blind unaided ranking the plan called for. The product owner
gave priority input during triage — the LOC/Goodhart parallel on S1-01, "obvious
fix" on S1-02, "09 then 05", and an endorsement of assertion counting.

So the blind human control is spent, and this is **a joint ranking after
negotiation.** The comparison against the treatment therefore answers a narrower
and harder question:

> Does an outside prioritization method reorder a list two informed people
> already argued about?

Narrower than "does it beat a cold list." Closer to how prioritization is
actually used. Recorded as a trade — a control was spent to buy a decision, and
that was the right trade for real work.

---

## Scope: three, plus one

Triaged from 37 candidates to the items argued hardest for.

| Rank | ID | Item | Effort | Deadline |
|---|---|---|---|---|
| 1 | S1-01 | Scope the coverage denominator — `--cov=src`, not `--cov=.` | **S** | **Freeze** |
| 2 | S1-09a | Clearance default is wrong: new citizens are born RED, should be INFRARED | **S** | Freeze-adjacent |
| 3 | S1-02 | `ruff check --isolated` — the citizen must not choose which rules count | **S** | **Freeze** |
| 4 | NEW-01 | Count assertions per test, as an additive signal | **M** | None — additive |

### Why this order, stated so it can be wrong

**The ranking is by deadline, not by value.** `PRD.md` §8 freezes the measurement
set for cohort 1 because changing a measurement resets every baseline. S1-01,
S1-02 and S1-03 are therefore **free today and impossible in a month** — after
the first real submission, fixing them means invalidating every student's
history, the one thing this product cannot do.

S1-01 first because coverage carries weight 2.0, the largest term, and the defect
makes it *directly gameable*: a citizen raises velocity by adding a test file
that asserts nothing. It is the LOC-as-a-metric failure with a different unit.

S1-09a above S1-02 because a wrong default is silently wrong rather than silently
absent, and every citizen created before it is fixed carries it.

NEW-01 last **because it is the only one with no deadline.** CLAUDE.md's freeze
rule is "adding a new signal is fine; changing or removing one is not."
Assertion counting is additive and can land mid-cohort. The other three cannot.

### Deliberately excluded

- **S1-09b — the clearance promotion mechanic** (repo + channel creation as the
  exit ticket to RED). Split out from S1-09 because it is an **L**, not an S, and
  it needs the channel model settled first. The *default* is a one-line fix; the
  *ladder* is a feature.
- **S1-05** (`first_test_bonus` unpinned) — ranked second by the owner, deferred
  here because it is a guard against a future mistake rather than a live defect,
  and it is not freeze-bound. Flagged as the most likely place this ranking is
  wrong.

---

## Hypothesis

Pre-registering a falsifiable claim, so commit A is a prediction rather than a
timestamped list.

1. **The treatment will not change the top three.** They were selected by a
   *deadline* (the freeze), and a prioritization method that does not know the
   freeze exists cannot rediscover that constraint from value and effort alone.
2. **It will reorder the tail**, and most likely promote S1-05 or S1-12
   (`METRICS.md` has no producer — the only instructor-facing MVP deliverable).
3. **It will surface at least one dependency we missed.** The `Depends on:` field
   was filled by surveyors who each saw one scope.
4. **Effort calibration: at least one of the three S items will turn out M.**
   S1-01 is my candidate — "scope the denominator" is one flag, but it changes
   the recorded coverage figure, which touches the ledger.

If 1 is wrong, the method is doing something we cannot, and that is the finding.

---

## Contamination register

Noted, not panicked over. Post-analysis judges whether any of it mattered.

| What | When | Assessment |
|---|---|---|
| Repo name, tagline, update date of `the_algorithm` seen in a `gh repo list` | before survey | Trivial. Zero was never available. |
| Product owner gave priority input during triage | before commit A | **Material.** Spends the blind human control; see relabel above. |
| Owner's "three most recent" control sample never collected | — | Superseded by the above. |
| Survey scoped by me to exclude PR #53, `EARLY_RUNS` defects, oracle divergence | before survey | Recorded in `01-candidates.md`. |
| `.claude/agents/`, `shodann-architecture-prototype/`, pilot dashboard figures went unswept | during survey | Gaps I created. Listed by the critic unprompted. |
| `PRD.md` §8 found reverted in the working tree; restored before branching | before survey | Would have pre-registered against an un-decided PRD. |

---

## Inferences I am acting on without confirmation

Stated so they are correctable rather than buried.

- **"The three I argued hardest for"** — read as S1-01, S1-09, S1-02, with
  assertion counting as the fourth. S1-05 was ranked explicitly ("09 then 05")
  but is deferred here on deadline grounds. If the intended three were different,
  this ranking is wrong at the root.
- **Students start at INFRARED and earn RED** by creating their user repository
  and a channel. Read from "they do start at RED essentially, creating their user
  repo and channel repo are their exit ticket to RED."
- **"Channel" = a tracked repository.** SHODANN watches GitHub as humans watch
  YouTube; she is liked and subscribed. This is the model
  [#51](https://github.com/norrisaftcc/algorithm-shodann/issues/51) was reaching
  for without vocabulary — a citizen has a different velocity per channel,
  because it is a different show.

## Unparsed

- **"one last ngn"** — could not resolve. Scoped as one additional item beyond
  the three; assertion counting occupies that slot provisionally. Correctable
  before any work begins.
