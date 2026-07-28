# Candidate items — survey output, unranked

Produced 2026-07-28 by five blind surveyors over disjoint scopes plus a
completeness critic. **Unranked on purpose.** Ranking is commit A; this file is
the raw material both ranking methods will be given.

Surveyors were told only their scope and the item template. None knew a sprint
was running, that a control was being protected, or that a second method exists.

Cost: 6 agents, 732,567 tokens, 182 tool calls, 11 minutes wall clock.

**Excluded by instruction** (recorded so the exclusion is auditable, not silent):
content already covered by open PR #53, the nine defects in `EARLY_RUNS.md`, and
divergence in `growth-velocity.js` / `shodann-core.yml`, which is deliberate.

---

## Measurement integrity — the score itself is wrong or gameable

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-01 | `pytest --cov=.` has no coverage config, so **citizen test files land in the coverage denominator**. Coverage is the 2.0-weighted term — the largest. A citizen raises velocity by adding a test file that asserts nothing. | `shodann.yml:103` | ledger | S |
| S1-02 | `ruff check .` runs with no `--isolated`, so **the citizen's own `pyproject.toml` decides which rules are counted**. Lint delta feeds the sqrt term. Counts are not comparable between citizens. | `shodann.yml:96` | ledger | S |
| S1-03 | `collect_metrics` sets `complexity = functions`. The stored "cyclomatic complexity" is a count of `def `. Nothing ever reads a `C901` diagnostic, so the frozen ruff pin protects a number that is not computed. | `review.py:126` | ledger | M |
| S1-04 | `pytest-cov` is unpinned and absent from dev extras, while ruff beside it is pinned exactly *because* it feeds the score. Coverage is the heavier input. | `shodann.yml:85`, `pyproject.toml:14` | ledger | S |
| S1-05 | **No test pins `first_test_bonus`.** Surveyor changed it 1.0 → 0.05 and all 247 tests passed. US-1.3's curve can be flattened silently, and the damage bakes into every baseline. | `test_velocity_contracts.py:89` | ledger | S |

## The model is being fed zeros as if they were measurements

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-06 | `SYNTAX_ERRORS`, `tests_passed`, `tests_failed`, `style_issue_count` are **hardcoded zeros never passed by `review()`**, while the real values sit in `AnalysisReports` one call away. A citizen with a fully red suite is told nothing failed. | `prompts.py:273`, `review.py:434` | hygiene | S |
| S1-07 | The analysis job runs the suite but **discards pass/fail** — only `coverage.json` is uploaded, and coverage.py never writes the tally keys `AnalysisReports` reads. | `shodann.yml:103` | hygiene | S |
| S1-08 | No test asserts the tallies reach the DATA layer, so the zeros pass a presence-only check. | `test_prompts.py:88` | hygiene | M |

## Whole features implemented and unreachable

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-09 | **Nothing reads `.shodann/clearances.json`** — it does not exist. `clearance_level` only round-trips the ledger, so every citizen is permanently RED. INFRARED and BLUE+ branches are built, tested, and dead. The only citizen is the author, being taught his own vocabulary table. | `state.py:87`, `validator.py:249` | ledger | M |
| S1-10 | `--mode` accepts all eight specs but `render_prompt` only renders the base template, so **seven modes are guaranteed to fail validation twice** and fall to REDUCED ALLOCATION — two wasted model calls, indistinguishable from an outage. | `review.py:482` | hygiene | S |
| S1-11 | `test_every_mode_agrees_with_its_own_spec` passes for seven modes that cannot work. It checks last heading and word cap only. | `test_clearance.py:64` | hygiene | M |
| S1-12 | **Nothing produces `METRICS.md`.** `leaderboard.py` is complete and well tested; its only caller prints to stdout and no workflow invokes it. The single instructor-facing MVP deliverable has no producer. | `.github/workflows/` | ledger | M |
| S1-13 | Four of five edge-case templates in `prompts/05` **fail their own ResponseSpec** — two emit the forbidden word "error", two exceed their opportunity caps. | `05:153,244,345,415` | hygiene | S |

## Consent and record integrity

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-14 | `display.visibility` **defaults to `named`**, so a citizen who never chose appears on a public leaderboard under their GitHub username. PRD:448 says opt-in; the docstring says "never by default"; `from_dict` fills in `named`. Opting out means hand-editing JSON. | `state.py:72,122` | ledger | M |
| S1-15 | An unparseable ledger is treated as a **new citizen and then overwritten** — one git conflict marker permanently erases a growth record, silently, with no notice. | `state.py:182` | ledger | M |
| S1-16 | The live ledger is **contaminated by the pre-`--dry-run` push-era regime**: `pr_count` 13 and `iteration_streak` 13 count pushes, not merges. Two history entries sit 58 seconds apart. Every trend and delta is measured from this. | `norrisaftcc.json:12` | ledger | S |
| S1-17 | The `410.0` velocity entry is residue of the absent-vs-zero defect. It drags `compute_trend` to `descending` (35.0 vs avg 148.5) when the same three without it read `ascending` (35.0 vs 23.2). | `norrisaftcc.json:32` | ledger | S |
| S1-18 | Ledger push is bare `git push` with no fetch/rebase/retry, and concurrency is keyed per PR — **two close merges race**, and the loser posts nothing and retries nothing. | `shodann.yml:247` | ledger | S |
| S1-19 | `to_dict` emits a fixed key list and `from_dict` discards unknowns, with no `schema_version` — cross-repo schema drift becomes invisible data loss. | `state.py:140` | ledger | S |
| S1-20 | `rage_state_encounters` is written to every record, never incremented, never read. Reads as a real counter saying RAGE never fired. | `state.py:93` | ledger | S |

## Test suite gaps

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-21 | The velocity CLI writes `coverage_instrumented: false` **alongside a real measured coverage figure** — reproduced. One manual run poisons a ledger. | `cli.py:74` | ledger | S |
| S1-22 | `load_all_citizens` catches JSON/Key/Type but **not `UnicodeDecodeError` or `OSError`** — one latin-1 byte in one citizen file takes the entire leaderboard down. Sibling readers get this right. | `leaderboard.py:72` | ledger | S |
| S1-23 | Iteration streak resets to zero on any non-positive score, untested in both directions. Whether refactoring should break a streak is an **undecided product question currently answered by an untested one-liner**. | `state.py:238` | ledger | S |
| S1-24 | The oracle fixture identifies its source by **path and date only — no commit sha or content hash** — and no script regenerates it. The golden cases can silently stop describing the oracle. | `oracle_snapshot.json:3` | hygiene | S |

## Repository hygiene

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-25 | **No workflow runs this repo's own tests or ruff as a gate.** `test_workflow_contract.py` exists because the workflow was unreadable by tests — and it never runs on a PR. | `.github/workflows/` | hygiene | M |
| S1-26 | `state.__all__` omits seven names that four modules import, including `clearance_name`. | `state.py:26` | hygiene | S |
| S1-27 | `spec.headings[-1]` is assumed to be the iteration section in two modules; true only for `STANDARD`. | `clearance.py:79`, `prompts.py:239` | hygiene | S |
| S1-28 | `with_config` and `tune` are dead — no caller anywhere, not in `__all__`, on the one module that is sole authority for the maths. | `velocity.py:350` | hygiene | S |
| S1-29 | `build_context`'s docstring describes the "not instrumented" approach that was **tried and abandoned**, contradicting an inline comment twelve lines below it. | `prompts.py:223` | hygiene | S |
| S1-30 | `requires-python >= 3.11`, both jobs pin 3.12, local runs 3.13. Only one is ever tested. | `pyproject.toml:5` | hygiene | S |
| S1-31 | The PR template's Testing section predates the test suite — offers manual checkboxes only, no box for pytest or ruff. It is the only gate the project has. | `PULL_REQUEST_TEMPLATE.md:28` | hygiene | S |

## Documentation that routes a reader into a wrong result

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-32 | `prompts/03` presents itself as the source of `CLEARANCE_INSTRUCTIONS`; nothing reads it, and its BLUE+ block contradicts what `for_clearance` enforces. | `03:264-310` | hygiene | M |
| S1-33 | Every recipe in `SHODANN_CLAUDE.md` COMMON TASKS routes to a superseded file — "adjust velocity weighting: edit `growth-velocity.js`" sends a maintainer to edit the **oracle**, breaking snapshot tests and moving no production score. | `SHODANN_CLAUDE.md:395` | hygiene | S |
| S1-34 | `design_docs/README.md` says every file in the folder "represent[s] the current plan" — sweeping in the two deliberately historical artifacts, one of which carries a shell injection. | `README.md:2` | hygiene | S |
| S1-35 | `prompts/01`'s reference notes document two coverage behaviours that were tried, failed live, and replaced. | `01:274,290` | ledger | S |
| S1-36 | `RAGE_STATE.md` specifies **one central `security_debt.json` holding every citizen** — impossible under one-repo-per-student, and the exact shape that caused the merge-conflict loop. | `RAGE_STATE.md:341` | ledger | M |
| S1-37 | Nothing enforces the frozen toolchain across a reinstall except the ruff pin; see S1-04. | — | ledger | S |

---

## What the critic is taking on faith

Its own list, unprompted-for-charity:

- That the ledger's history was written by the per-push regime — inferred from timestamps, not reconstructed from workflow runs.
- That `pytest --cov=.` instruments test files on a runner — follows from coverage.py defaults, **not confirmed against a real artifact**.
- That the recorded 98.7% came from that unscoped invocation.
- That no aggregation exists outside this repository — a course repo it cannot see could hold one.
- **`design_docs/shodann-architecture-prototype/` (7 files) went unread by every surveyor.**
- **`.claude/agents/` (13 definitions) is a whole unswept file class**, excluded by my instruction without being read — so nobody knows whether those definitions encode contracts the code has since broken.
- `design_docs/pilot/session-one-ledger.html` figures were never verified, and may have been generated from the same contaminated pre-fix readings.

The last three are gaps **I created** by scoping the sweep. They belong in the retro as a cost of how the survey was run.
