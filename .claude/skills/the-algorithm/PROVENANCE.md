# Provenance

Vendored, not authored here. Do not edit these files in this repository.

- **Source:** `norrisaftcc/the_algorithm`
- **Commit:** `cbb6800ae08cf67f9b95903fd094238676c1c2a5`
- **Committed:** 2026-07-28T15:06:33-04:00
- **Vendored:** 2026-07-28, under the frozen contract in `design_docs/sprints/2026-07-28/`

## Files

- `SKILL.md` — canonical doctrine, The Algorithm v2. Invariants are amendment-only.
- `HOUSE-STYLE.md` — controlled-language subset. DRAFT upstream; advisory until its amendment freezes.

## Rules

- Amend upstream, through the gate, then re-vendor. Never patch a copy.
- An unrecorded change to Invariants is a defect, whoever made it.
- Re-vendoring updates the commit above. A vendored copy with no recorded commit is unverifiable.

## Why it is here

`ASSAY` is used against this repository's own documents. `SKILL.md` is the
instrument; keeping it local makes the reading reproducible after the source
repository moves.
