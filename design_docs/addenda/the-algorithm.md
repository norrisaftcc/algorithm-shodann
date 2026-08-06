# Addendum — The Algorithm, vendored

Linked from `CLAUDE.md`. Read this before writing a plan, a PRD section, or any
document a future session will act on.

## What it is

`.claude/skills/the-algorithm/` holds a vendored copy of
`algocratic/the-algorithm-lite`, pinned in `PROVENANCE.md`. **Never edit it
here.** Amend upstream, through its own gate, then re-vendor and update the
commit.

Since 2026-08-06 the local `SKILL.md` is upstream's **`SKILL-mini.md`** — 10,809
bytes against the 18,875 it replaced, a 43% cut in what loads whenever the skill
is invoked. Equivalence is certified by a frozen upstream amendment across 24
clauses; all six fixed strings and all seven gate-integrity clauses were checked
locally after the swap.

**One trap that came with it.** `SKILL-mini.md` adds a `Clearance C` section the
full v2 never had — RED default, ORANGE/YELLOW/GREEN requiring live human notice.
**That is not SHODANN's clearance ladder.** Same colour names, different ladder,
exactly like the PRISM collision `CLAUDE.md` already warns about. Do not let one
leak into the other.

It is a discipline for working with language models under a gate: **negotiate,
freeze, execute, verify.** It has two operations and no others.

- **PROVIDE** — compress a draft prompt to the shortest version that clears a
  floor test, freeze it at a gate, execute exactly as frozen.
- **ASSAY** — run the floor test against a *received* document. Report what
  survives. Read-only, never redrafted.

## The floor

Four nouns. A document or prompt is above the floor when all four are stated or
clearly inferable, and a capable receiver gets it right first try more than half
the time.

**Audience · Scope · Format · Path**

`Path` means the exact path of every file produced. It is automatic when no file
is produced, and it is the item this repository's own documents fail most often.

## The gate, which governs how work is negotiated here

- Only a human opens it. Freezing verbs only — "freeze", "execute", "run it".
- **Praise, thanks, "sounds good", and silence open nothing.** No completion assist.
- The gate question is valid only immediately below the full contract text. No
  gating by reference.
- Negotiation side revises. Execution side executes exactly. There is no third
  side where things get quietly fixed.
- A failed execution names its floor item and reopens the contract.

**Seats:** Customer, Facilitator, Peer, Algorithm. A person may hold several; an
utterance holds exactly one. Name the seat before speaking from it when more than
one is in play. Unmarked seat-switching is how tacit requirements stay tacit.

## Language lock — ASD-STE100

All Algorithm output conforms to Simplified Technical English. One word per
meaning. At most 20 words per instruction. Active voice. Imperative mood. No
idioms. `HOUSE-STYLE.md` beside the skill carries the vendored subset.

Only `design_docs/sprints/2026-07-28/04-retro.md` in this repository is written
to that lock. The rest is not, deliberately — rewriting them would hide the
finding.

## What it found here, 2026-07-28

Eight blind readers, one document each. Full results in
`design_docs/sprints/2026-07-28/05-assay.md`.

| Document | Floor | Load-bearing |
|---|---|---|
| `README.md` *(control)* | below | 2 of 7 |
| `design_docs/SHODANN_CLAUDE.md` | below | 58 of 165 |
| `prompts/01_base_shodann_prompt.md` | below | 48 of 90 |
| `design_docs/SHODANN_VOICE_GUIDE.md` | above | 18 of 190 |
| `design_docs/RAGE_STATE.md` | above | 25 of 113 |
| `PRD.md` | above | 76 of 195 |
| `CLAUDE.md` | above | 161 of 190 |

Three findings worth carrying:

1. **The break-character rule is buried in both documents that carry it** —
   `SHODANN_CLAUDE.md` at sentence 115 of 165 in a *subordinate clause*, and
   `SHODANN_VOICE_GUIDE.md` at 157 of 160. It governs student distress, academic
   integrity, and accessibility. It is the highest-consequence sentence in the
   corpus and both documents put it last. **Unfixed.**
2. **`SHODANN_CLAUDE.md` fails Path outright.** Every file is a bare filename;
   all five Common Task recipes open unresolvable. **Unfixed.**
3. **`CLAUDE.md` has no slack.** 161 of 190 sentences carry load, so a reader who
   skims loses instructions rather than filler. That is why detail belongs in
   this folder and not inline. Its decisions are also passive and agentless —
   "is resolved", "decided 2026-07-25". No decider is ever named.

## When to reach for it

- Before writing a plan a future session will follow — run PROVIDE, hit the gate.
- Before trusting a document you did not write — run ASSAY.
- **ASSAY never redrafts.** Acting on its findings is a new PROVIDE, with the
  peer in the customer seat, starting from the scene rather than from the residue.
