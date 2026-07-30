# Addendum — Accumulation

Linked from `CLAUDE.md`. **This document states a problem and proposes nothing.**
If you are looking for what to do about it, there is nothing here; see the closing
section for why that is deliberate.

Read it if you are picking this repository up cold, or fast, or under pressure.
It is short on purpose.

## The problem

**Work accumulates faster than its consequences are observed, and every
instrument this repository trusts stays green throughout.**

A change lands. It is correct, tested, reviewed, and it alters the conditions the
next change is made under. If the next change lands before the previous one's
effect has been *read*, the second is made against a state nobody has seen. Repeat
that and the codebase fills with correct changes whose interactions no one has
looked at.

Nothing in the toolchain detects this. The suite passes because each change is
individually sound. The linter passes. Coverage rises. Review approves, because a
reviewer reads a diff and this is not visible in a diff. The condition is a
property of the *sequence*, and every instrument here inspects a *state*.

## How to recognise it

Four signatures, in rough order of how early they appear.

**1. The interval between changes falls below the time it takes to observe one.**
This is the leading indicator and the only one that appears before damage. It is
computable from git history and review timestamps with no new instrumentation.

**2. A fix causes the next defect.** Not a regression — the fix is correct — but
new material arriving in the fix becomes the input to the next mistake. It is
never visible in the diff that introduced it, because the diff is right.

**3. A loop.** A defect fixed two or three times is not persistence, it is a
boundary nobody restated. A loop implicates the floor — **Audience, Scope, Format,
Path** (`the-algorithm.md`) — and *always* implicates **Scope**, because Audience,
Format and Path errors produce one wrong artifact, while only a wrong boundary
produces another pass. A `Path` failure does not loop at all; by the addendum it
reopens the contract, which is a different event.

**4. A term with two meanings, built on.** Something changed meaning without
changing name, one meaning was picked, work proceeded, and the other was
discovered later. `CitizenRecord.discontinuities` exists to mark these in a
citizen ledger; the same thing happens to vocabulary, and nothing marks that.

## The evidence

PR #61, measured after the fact rather than noticed during it. Fourteen review
rounds, eight defect classes, suite green from 372 tests to 467 throughout.

**Interval between commits, in order:**

```
 #2   78m     #11  333m     #16   3m
 #4   99m     #12    3m     #17   3m
 #10 157m     #13    4m     #18   3m
              #14    3m     #19   4m
              #15    3m     #20   4m
                            #21   4m
```

Eleven consecutive commits at three to four minutes, after intervals in hours.
(The 721-minute gap is a session break. The 0-minute entries are bot ledger
commits and one batched push. The clean run is 11–21.)

**Lag from a fix to the defect it caused, in the order the seeding fixes landed:**

| Seeding fix | Landed | Surfaced | Lag |
|---|---|---|---|
| streak fix | round 4 | round 7 | 3 |
| complexity rename | round 4 | round 9 | 5 |
| style-breakdown fix | round 10 | round 11 | 1 |
| prose rule | round 10 | round 11 | 1 |

Rate of change up roughly 25×; time to observe a consequence down 4×. One of
those defects was a prohibition shipped in the same commit as the material that
made it violable.

**Signature 3, four for four on that pull request:** the streak figure took three
passes, the clearance rule two, one term is still open, and one backlog item was
deferred five times on a judgement made once and never re-checked.

**Signature 4, twice:** `complexity` changed from a count of `def` to a count of
C901 violations under the same name. And a word was used across an artifact and
five exchanges for "a load-bearing ambiguity" before an outside reader said it
meant nothing to them either — it had come from a diagram's visual density, so the
*shape* had been named instead of the phenomenon.

Every commit in that sequence was individually verified: each guard reverted
against the defect it named, suite green, ruff clean. **No amount of care would
have prevented it.** That is the finding. At three minutes per fix the previous
fix's output had not been read yet.

## What it costs

Measured on the same pull request: **6,769 insertions against 332 deletions**, a
20:1 ratio on work substantially about fixing things. Documented token spend on
two prior exercises in this repository: 455,373 and 732,567.

The durable cost is not tokens. It is that four of the checks added during that
sequence are open-vocabulary — word lists that grow after every review, 94 terms
across seven lists — and one of them was measured rejecting 2 of 9 sentences a
*correct* review would contain. Accumulation produces mechanisms, and mechanisms
are permanent. **A closed-vocabulary check is cheap forever; an open-vocabulary
check is a department that has to be staffed.**

## What it is not

- **Not carelessness.** Every change in the evidence above was verified, and
  care does not raise the rate at which results can be read.
- **Not technical debt** in the usual sense. Debt is a known shortcut taken
  deliberately. This is correct work whose interactions are unobserved.
- **Not a test-coverage problem.** Coverage rose throughout. The suite is
  structurally unable to see a property of the sequence.
- **Not slowness.** The condition is a *ratio*. Working slowly does not fix it if
  observation is slower still, and working fast is fine when results are read.
- **Not solved by review.** A reviewer reads a state. This lives between states.

## Why there is no fix in this document

Because a proposed fix ages faster than the problem, and the residue then gets
read in place of the scene. Issue #63 proposed a mechanism for this and is closed
as declined with a `priority: 2` tombstone; the reasoning survives there and does
not need re-deriving, but it is a *proposal*, and a proposal read cold by someone
in a hurry is worse than no proposal, because it looks like a decision.

`the-algorithm.md` states the same rule for ASSAY: acting on findings is a new
PROVIDE, starting from the scene rather than from the residue. This document is the
scene.

One thing is worth carrying and is not a fix: **the leading signature is
computable from data the repository already keeps.** Nobody has to build an
instrument to find out whether this is happening right now.
