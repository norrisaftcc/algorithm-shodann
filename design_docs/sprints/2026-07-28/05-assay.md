# ASSAY — the SHODANN corpus

Instrument: `the_algorithm` v2, vendored at `cbb6800`. Eight blind readers, one
document each. Each got the ASSAY protocol and one file path. None knew what
SHODANN is, that a sprint was running, or that seven other readers existed.

Read-only. No document was rewritten. 455,373 tokens, 8 agents, 2 minutes.

---

## Ranking

Floor verdict first, then load-bearing ratio. They measure different things: the
floor asks whether Audience, Scope, Format and Path are present; the ratio asks
how much of the document carries load.

| Document | Floor | Load-bearing | Operative sentence, position |
|---|---|---|---|
| `README.md` **(control)** | **below** | 2 of 7 | "We must build her." — 3 of 7, main |
| `design_docs/SHODANN_CLAUDE.md` | **below** | 58 of 165 | "It's okay to break character" — 115 of 165, **subordinate** |
| `prompts/01_base_shodann_prompt.md` | **below** | 48 of 90 | "Do not report, infer, or celebrate a coverage number." — 20 of 90, main |
| `design_docs/SHODANN_VOICE_GUIDE.md` | above | **18 of 190** | "The satire serves learning. When it doesn't, set it aside." — **157 of 160** |
| `design_docs/RAGE_STATE.md` | above | 25 of 113 | "RAGE STATE is NEVER punitive." — 8 of 113, main |
| `PRD.md` | above | 76 of 195 | "frozen before the first cohort and must not change mid-course" — 172 of 195, main |
| `02-prediction.md` | above | 38 of 51 | "the blind human control is spent" — 7 of 51, main |
| `CLAUDE.md` | above | 161 of 190 | "resolved in favor of Python" — 14 of 190, main |

## The control fired

`README.md` returned below floor at 2 of 7 with nine flags. It is in-persona
satire and was included to test the instrument. Had it come back clean, every
other result here would be void.

---

## Findings that change something

### 1. The voice guide is not the false positive we assumed

We agreed in advance to discount it: a document that prescribes smoothness will
assay as smooth. **It came back above floor.** The instrument did not confuse
deliberate persona with manufactured agreeableness.

What it found instead is worse and useful. **18 of 190 sentences carry load —
the lowest ratio in the corpus.** The document expands where it is fun (easter
eggs, milestone flourishes, escalation gags) and stays thin where it constrains.

And the sentence that governs the entire document —

> "The satire serves learning. When it doesn't, set it aside."

— is **sentence 157 of 160**. The override that outranks every rule above it sits
in the last two percent of the file. No precedence rule, no failure case.

The acknowledged false positive was a real finding wearing a different shape.

### 2. `SHODANN_CLAUDE.md` fails Path and Scope, and buries its safety rule

Worst real document: below floor, 58 of 165, nine flags.

- **Path fails.** Every file is a bare filename. All five Common Task recipes
  open with an unresolvable reference. A receiver cannot find the file to edit.
- **The operative sentence is "It's okay to break character" — at 115 of 165, in
  a subordinate clause.** The rule that governs student distress, academic
  integrity, and accessibility is the most consequential sentence in the file and
  it is buried.
- **Missing rough edge.** The subject is measurement and ranking of students.
  The document names no failure mode of velocity scoring, no consent, no opt-out,
  and no procedure for a model stating a metric wrongly to a student.
- `"Grade integration through metrics export"` appears once, as a fourth bullet,
  never returned to. The highest-consequence claim carries the least weight.

### 3. The PRD has a seam, and the instrument found it

`PRD.md` is above floor. Its flag is the sharpest result of the eight:

> **smoothness-confined-to-a-graft.** Sections 1–7 — the original 2025 document —
> contain no sentence anyone could object to. Every cut is pre-justified, every
> problem pre-solved. That body alone would be flagged outright. The roughness is
> grafted on: the §8 Decisions block, added 2026-07-25, holds the only sentences
> with cost. **The original is a manufacturing signature; the appendix is not.**

A blind reader, given no dates and no history, located the boundary between the
generated document and the argued one — and it is exactly where the 18-month gap
falls.

### 4. RAGE_STATE reassures where it should disclose

Above floor, and the erosion note is the finding:

> The document defines an adversarial mode that scans student code without
> per-instance consent, selects 10 percent of submissions at random, and
> maintains a debt ledger — and every mechanism is followed by a statement of why
> no one should mind it.

The mechanisms may be fine. The pattern of following each one with its own
reassurance is what got flagged.

### 5. `CLAUDE.md` has the opposite problem

161 of 190 load-bearing — the highest ratio, and the reader refused to call it a
compliment:

> "The document has no slack, so a receiver who skims loses instructions rather
> than filler."

Its erosion runs **toward foreclosure**, not toward the agreeable. And every
settled decision is passive and agentless — "is resolved", "decided 2026-07-25",
"convention adopted". **No decider is ever named. The dates substitute for a
signature.**

### 6. The pre-registration performs rigor

`02-prediction.md`, assayed blind:

> "Toward methodological virtue. The smooth here is not corporate politeness but
> visible rigor — the register in which no reader objects is *I recorded my own
> contamination, I stated my inferences, I pre-registered a falsifiable claim*."

My own hand-assay of the same document called it 31:1 and flagged the buried
deadline. The blind reader found something I could not: **the self-criticism was
itself the smoothness.** A contamination register is unobjectionable by
construction. That is what made it comfortable to write.

---

## What ASSAY caught that the survey did not

The 37-item survey read code and found defects. ASSAY read documents and found
structure. **The overlap is near zero.**

The survey could not have found a buried override, a missing consent discussion,
an agentless decision record, or an 18-month seam in a document's register. None
of those is a defect in any file. All of them change what a reader does next.

Two instruments, two failure classes. Neither substitutes.

---

## Not done

Per contract: no assayed document was rewritten. ASSAY never redrafts. Acting on
these findings is a new PROVIDE, with the peer in the customer seat, starting
from the scene rather than from the residue.

This is a finding, not a draft.
