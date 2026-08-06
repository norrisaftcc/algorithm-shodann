# Provenance

Vendored, not authored here. Do not edit these files in this repository.

- **Source:** `algocratic/the-algorithm-lite`
- **Commit:** `c4b7c771dc852a4d6a64684a35b60337761837e9`
- **Committed:** 2026-08-03T23:58:14Z
- **Vendored:** 2026-08-06, under #68

## Files

| Local | Upstream | Bytes |
|---|---|---|
| `SKILL.md` | `SKILL-mini.md` | 10,809 |
| `HOUSE-STYLE.md` | `HOUSE-STYLE.md` | 6,564 |

**`SKILL.md` here is upstream's `SKILL-mini.md`, not its `SKILL.md`.** That is
deliberate and it is the whole point of the swap. Upstream's own
`.claude/skills/the-algorithm/SKILL.md` is 18,567 bytes — within 2% of the
full v2 this replaced, and it saves nothing. `SKILL-mini.md` is the artifact
the repository's tagline is about.

Not taken: `ASSAY.md` (18,100 bytes). The `A` protocol is inside `SKILL.md`
already; the long form is reference and would cost more than the swap saved.
Fetch it from upstream when a full assay needs the worked detail.

## What changed, 2026-08-06

Previous source was `norrisaftcc/the-algorithm@cbb6800`, 18,875 bytes.
**Now 10,809 — a 43% reduction in what loads on every session that invokes it.**

Compression is certified upstream by a **frozen** amendment,
`registry/amendments/frozen/SKILL-mini-equivalence.md`: `PASS` by manual clause
mapping across 24 doctrine clauses. Verified locally after the swap:

- All six fixed strings present verbatim, including `Freeze this contract and
  execute, or keep negotiating?` and `This is a finding, not a draft.`
- All seven Gate integrity clauses present, including the one this repository
  most depends on — `ok`/`sure`/`sounds good`/silence count as negotiation, and
  only `freeze`/`execute`/`run it` open the gate.

**Two things to know before trusting it blindly.**

1. **Equivalence was established by manual mapping, not mechanically.** It is a
   careful human claim, not a diff. If a clause you rely on is missing, that is
   a finding worth sending upstream rather than patching here.
2. **`SKILL-mini.md` is not only compressed — it adds a `Clearance C` section**
   the full v2 did not carry: RED default, and ORANGE/YELLOW/GREEN requiring
   live human notice with the `Customer` seat reserved. New doctrine arrived
   with the token saving. Do not confuse it with SHODANN's own clearance
   ladder; they are different ladders, as `CLAUDE.md` already warns about
   PRISM.

It also writes in glyph shorthand (`門` gate, `床` floor, `席` seat). Upstream
states the rule that makes this safe: **undefined glyphs have no authority.**

## Rules

- Amend upstream, through the gate, then re-vendor. Never patch a copy.
- An unrecorded change to Invariants is a defect, whoever made it.
- Re-vendoring updates the commit above. A vendored copy with no recorded
  commit is unverifiable.

## Why it is here

`ASSAY` is used against this repository's own documents. `SKILL.md` is the
instrument; keeping it local makes the reading reproducible after the source
repository moves — which it already did once, from `norrisaftcc/the_algorithm`
to `algocratic/the-algorithm-lite`.
