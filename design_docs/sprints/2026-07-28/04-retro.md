# Retro — 2026-07-28

Written in STE, per the Language lock the sprint documents violated. One
instruction per line. At most 20 words. Active voice.

---

## What shipped

- Scope the coverage denominator. `--cov=src`, with a fallback for flat layouts.
- Isolate the linter. `ruff check --isolated`.
- Add two workflow contract tests. Both defects are now asserted, not commented.

249 tests pass. Ruff is clean.

## What did not ship

- Clearance default, INFRARED not RED. Ranked 2. Not started.
- Assertion counting. Ranked 4. Not started.
- 33 other surveyed items. Filed or deferred.

---

## The experiment failed, and the failure is the result

**Prediction:** the outside method will not change the top three.

**Outcome:** unfalsifiable. `the_algorithm` has no ranking operation. It holds
two operations on documents, PROVIDE and ASSAY. Neither orders a backlog.

The experiment tested a method that does not do the thing tested.

### Root cause

I read "proposed workflows... involving requirements and prioritization" and
assumed a prioritization method. I then built a barrier, a timestamped
pre-registration, and a contamination register around that assumption.

**The assumption was never checked, because checking it required reading the
repository, which the barrier forbade.**

The control was airtight. It protected the wrong variable.

### Cost of the error

- One survey: 732,567 tokens, 182 tool calls, 6 agents.
- Four rounds of gate negotiation.
- One pre-registration, one hypothesis, one contamination register.
- The survey's 37 items are sound and were worth the spend.
- The experimental apparatus around them was not.

---

## Calibration

Predicted effort against actual, in buckets.

| Item | Predicted | Actual | Result |
|---|---|---|---|
| S1-01 coverage scope | S | S | Correct |
| S1-02 ruff isolated | S | S | Correct |
| S1-A commit A | M | M | Correct |

**Sample of three. No signal.** Commit A said 12 items would be too few for a
slope. Three is not a curve.

One prediction was right for the wrong reason. I forecast S1-01 might be an M
because it touches the ledger. It stayed an S. The ledger effect is real but
lands on the next run, not in the edit.

---

## Findings the method produced

### 1. `ste100` was an instruction

ASD-STE100 is Simplified Technical English. The peer asked for the plan in it.

I called the token unparseable, guessed it meant "write for an outside reader",
and produced 900 words of prose.

The specification was vendored in the repository I was about to receive.

### 2. The method ran the session

The gate is `the_algorithm`. Four rounds of "no go but close" are its
"no completion assist" clause. "Pretend you're the product owner" is its Seats
section. I was inside the protocol while building an experiment to test it.

### 3. Commit A is below its own floor

ASSAY on the pre-registration returned 45 words of residue from 1400.
Compression ratio 31:1.

The operative sentence — three items expire after the first cohort submission —
sits in sentence 4 of 6, in a subsection, under a table.

**A document about a deadline contained no urgent sentence.**

### 4. Over-compression destroys meaning

The peer typed `ngn`. It carried no meaning. It cost two rounds.

Their own doctrine states it: short is not minimal. A prompt below the floor
comes back longer.

Both failure directions appeared in one session, from both parties.

---

## What to keep

- **The survey.** Five blind leaves and one critic found 37 real items. The
  critic's cross-scope findings were unreachable from any single scope.
- **The template.** Leaves filled it well and needed no context about the sprint.
- **S/M/L buckets.** A mixed human and agent team shares no clock.
- **The `taking_on_faith` field.** The critic listed three gaps I created.
- **The dashboard.** It found a live defect in four minutes.

## What to drop

- **Pre-registration for a method you have not read.** Read first. Then decide
  if a control is possible.
- **Contamination registers that log the wrong axis.** Mine recorded a repo
  name. It did not record that the method was already running the conversation.

---

## Open

- Clearance default. INFRARED, not RED. Freeze-adjacent.
- Assertion counting. Additive, so the freeze permits it any time.
- The channel model. `#51` is subscriptions. A citizen has one velocity per channel.
- 33 surveyed items in `01-candidates.md`.

## Unswept

The critic listed these. They remain unswept.

- `.claude/agents/` — 13 definitions. Excluded by my instruction, never read.
- `design_docs/shodann-architecture-prototype/` — 7 files.
- `design_docs/pilot/session-one-ledger.html` — figures never verified.
