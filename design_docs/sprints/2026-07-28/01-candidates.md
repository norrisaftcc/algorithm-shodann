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

## Closure — read this before picking anything below

The tables are left exactly as surveyed. **They carry no status, and a reader
who trusts them will re-do finished work** — the retro found this the hard way,
having written "33 other surveyed items" on a list that a dozen commits had
already shortened. Closure is tracked here instead, in one place, so the survey
stays the artifact it is and the question "is this done?" has one answer.

| Closed | Where |
|---|---|
| S1-01, S1-02 | sprint commit `8c5e0e4` |
| S1-25, S1-40 | #56 — the platform gate and the report-file deletion |
| S1-03, S1-04, S1-05, S1-37 | #58 — the measurement fixes, before the freeze |
| S1-09, S1-41 | #59 — the clearance register, the budgeted footer |
| S1-06, S1-07, S1-08 | #60 — the tallies reach the DATA layer |
| S1-15, S1-18, S1-19, S1-21, S1-22, S1-23, S1-38 | the ledger rung |
| S1-16, S1-17, S1-39 | the ledger rung — **annotated, not corrected**; the figures stand and `discontinuities` records where the seams are |
| S1-12, S1-14 | the METRICS.md rung — the producer, and the consent default it would otherwise have weaponised |
| S1-45 | the review rung — the rules behind the style count now reach the prose, which is where `read_lint_issues` always said they belonged |
| S1-28 | the review rung, commit `1191ca5` — `with_config` and `tune` swept rather than wired up |
| S1-30 | superseded by #56's platform matrix |

**S1-44 is closed on the leaderboard only.** A seamed figure is now marked and
footnoted in `METRICS.md`, so the instructor-facing surface no longer publishes
a number the record itself calls wrong. The degraded PR comment still prints a
bare `Submission {pr_count}` — same figure, different reader, no marking. Left
open rather than quietly narrowed, because a student is the harder audience to
footnote at and the answer there is probably to say less, not to annotate more.

**Declined by decision**, not left open: S1-09a (INFRARED as the default band).
#59 decided everyone starts at RED, and the reasoning is in that commit.

Everything else is open. **The survey itself is S1-01 to S1-37. Everything from
S1-38 on was filed by the rungs that closed the items above it** — 46 rows in
the tables now, nine of them post-survey. S1-42, S1-43 and S1-44 came from the
ledger rung, two by adversarially reverting that rung's own guards and one by
grepping the prompt for a claim after changing what the claim described; S1-45
came from reading a rendered review against the command this repository
documents; S1-46 from noticing that a *closure* moved the score.

**S1-46 is a record, not a task.** It is the only row in Measurement integrity
where no instrument is wrong, so there is nothing to repair; what it needs is a
decision before cohort 1 starts, after which the freeze makes the decision for
us. Do not pick it up as a fix.

**Two items were confirmed still open while writing this**, against the
temptation to assume recent work closed them: `S1-29` (`build_context`'s
docstring at `prompts.py:219` still describes the "not instrumented" phrasing
that the inline comment 37 lines below it says was tried and abandoned) and
`S1-35` (`prompts/01`'s reference table still documents the same abandoned
behaviour). `review.py:115` carries a third copy. Checked, not fixed — the
scope that closed these lines' neighbours did not include them.

---

## Measurement integrity — the score itself is wrong or gameable

| ID | Item | Where | Tag | Effort |
|---|---|---|---|---|
| S1-01 | `pytest --cov=.` has no coverage config, so **citizen test files land in the coverage denominator**. Coverage is the 2.0-weighted term — the largest. A citizen raises velocity by adding a test file that asserts nothing. | `shodann.yml:103` | ledger | S |
| S1-02 | `ruff check .` runs with no `--isolated`, so **the citizen's own `pyproject.toml` decides which rules are counted**. Lint delta feeds the sqrt term. Counts are not comparable between citizens. | `shodann.yml:96` | ledger | S |
| S1-03 | `collect_metrics` sets `complexity = functions`. The stored "cyclomatic complexity" is a count of `def `. Nothing ever reads a `C901` diagnostic, so the frozen ruff pin protects a number that is not computed. | `review.py:126` | ledger | M |
| S1-04 | `pytest-cov` is unpinned and absent from dev extras, while ruff beside it is pinned exactly *because* it feeds the score. Coverage is the heavier input. | `shodann.yml:85`, `pyproject.toml:14` | ledger | S |
| S1-05 | **No test pins `first_test_bonus`.** Surveyor changed it 1.0 → 0.05 and all 247 tests passed. US-1.3's curve can be flattened silently, and the damage bakes into every baseline. | `test_velocity_contracts.py:89` | ledger | S |
| S1-47 | **The changed-file count gets welded onto the syntax reading.** Round 16 of PR #61: *"0 compilation barriers. Your code parses cleanly across all 26 files."* 26 is `FILES_CHANGED`; the syntax check is `py_compile` over Python files, and four of that PR's 26 changed files are markdown. Template 01 carries `| **Files Changed** | {{ FILES_CHANGED }} |` at `:73` and `{{ SYNTAX_ERRORS }} compilation barriers detected` at `:94`, in different sections, with no file count attached to the syntax reading — so this is `EARLY_RUNS.md` 24's class again, two figures from separate rows welded into a claim stronger than either reading. **No probe can see it**: 26 is genuinely in the prompt, so `ungrounded_tokens` passes. Needs the syntax row to carry its own denominator (the count of files actually compiled) or to state that it has none. Adding a count of compiled files is legal mid-cohort — `PRD.md` §8 permits adding a signal — but it is a second figure beside a first, which is the trap entry 24 records, so the denominator belongs *in* the syntax sentence rather than as a new row. | `prompts/01:73,94`, `analysis.py` | hygiene | S |
| S1-46 | **Deleting untested code raises coverage, so deletion scores like testing and costs less.** Coverage is a ratio and the 2.0-weighted term; removing the untested lines moves it exactly as adding tests would. Observed on this repository — the `S1-28` sweep of `with_config`/`tune` raised coverage, and the review of that push read the deletion as evidence of more testable code. Unlike every other row in this section **nothing computes a wrong number**: it is a property of the metric, not a bug in an instrument, which is why it is recorded rather than repaired. Every honest fix (weighting deletions, or passing a line count beside the ratio) changes what coverage means, and `PRD.md` §8 forbids that after cohort 1's first submission — so this is decided **before** the cohort starts or it stands for the cohort. `EARLY_RUNS.md` 23 rules out the second-figure option on its own: never hand the model another number for a quantity the first one already covers. | `velocity.py`, `shodann.yml` analyse job | ledger | M |
| S1-40 | **A citizen can ship us their own coverage figure, and it counts.** Nothing deletes the report files before the tools write them. `> ruff.json` truncates, so ruff was safe; coverage was not — the step ends in `test -f coverage.json \|\| echo '{}'`, a guard for pytest-cov writing nothing. Commit a `coverage.json` claiming 97% and break your own test collection: pytest-cov writes nothing, the guard finds the committed file and leaves it, and it rides the artifact into the 2.0-weighted term. **Reproduced end to end 2026-07-29** before the fix. Same family as S1-01 and S1-02. | `shodann.yml`, analyse job | ledger | S |

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
| S1-38 | **A stacked pull request writes the ledger twice.** The merge path fires on any merged PR, including one merged into another feature branch that never reaches `main`. Observed 2026-07-28: #58 merged into #56's branch and SHODANN recorded a cycle, taking `pr_count` and `iteration_streak` to 16 for work that landed once. Compounds S1-16. Either gate the write on `base.ref == main` or accept stacking as double-counted and stop stacking. | `shodann.yml`, closed-event job | ledger | S |
| S1-39 | `complexity` changed units on 2026-07-29 — a `def ` count before, a `C901` count after (S1-03). The live record now reads `complexity: 0, functions: 361` against a stored history of `def` counts, so any delta spanning that boundary compares two different quantities. Nothing punitive follows, because the score no longer reads the field, but a reader of the history cannot see where the unit changed. | `norrisaftcc.json`, `velocity_history` | ledger | S |
| S1-41 | **The degraded comment breaks its own cap at BLUE+.** `for_clearance` clamps the band to `min(spec.max_words, 250)`, `review()` then reserves 30 words for the disclosure footer, and the REDUCED ALLOCATION body is SHODANN's own fixed ~235-word text with nothing to shorten. `test_the_posted_comment_respects_its_cap_at_every_band` parametrises all six bands and still misses it, because it validates against the *unadjusted* spec rather than `for_clearance(REDUCED_ALLOCATION, band)`. Found while scoping the author's promotion, which is why that promotion stopped at ORANGE. Fix: exempt a fixed text from a clamp that exists to stop the *model* padding. | `validator.py:278`, `test_review.py:768` | hygiene | S |
| S1-42 | **`iteration_streak` is now an exact alias of `pr_count`.** S1-23 made the increment unconditional, and `save_citizen_history` holds the only two writes to either counter — both `+= 1`, in the same function, with no reset anywhere in `src/`. They start equal at 0 and can never diverge, so the ledger stores one number twice under two names, one of which the prompt calls a *streak*. Either the field earns a break condition that is not velocity sign (a gap in time, an unmerged close) or it is redundant and the honest move is to say so. Removing it is a schema change; deciding what it means is not. | `state.py`, `prompts/01:66` | ledger | M |
| S1-43 | **A citizen is never told their history was lost.** `CitizenRecord.unreadable_source` is set on load and read by exactly one caller — the quarantine branch of the writer. Nothing reports it. A citizen whose ledger became a git conflict marker is quarantined correctly and then told "Submission 1" and "this is your first measured reading", and neither they nor the instructor hears that a record existed. The quarantine (S1-15) makes the bytes recoverable; nothing makes the loss *visible*. Needs a channel this rung did not build. | `state.py`, `review.py` | ledger | M |
| S1-45 | **The style count SHODANN reports cannot be reproduced by the citizen it is reported to.** The analyse job measures with `ruff check . --isolated --extend-select C90`, which is correct for scoring — S1-02 exists because the citizen must not choose which rules count. But the *feedback* then names that count: SHODANN told this repository "20 style diagnostics… resolve those diagnostics", while `python scripts/dev.py check`, the command this repository documents, reports zero. The 20 are real (mostly `C408`, visible only under ruff's defaults plus C901) and a citizen has no command that shows them. Actionable-sounding advice that cannot be acted on is the `EARLY_RUNS` class exactly. Observed compounding on the next run: handed a bare count and no categories, the model guessed them - "likely spacing or naming conventions", `e.g. "inconsistent spacing in function signatures"` - where the real diagnostics are mostly `C408`. A count with no content invites invention of the content. Third run added the count itself: "Run your linter with `--fix` flags to clear the 20 style diagnostics in one pass" - ruff reports 11 of the 20 as fixable, so `--fix` clears eleven and the citizen is told it clears twenty. The reading passed through is a total with no breakdown, and every gap in it gets filled by guesswork. Fix direction: `analysis.py` records the command that produced each reading and the DATA layer passes it through, so the comment can name it — never a second copy of the command string in a template, which is the drift #56 warned about. | `shodann.yml` analyse job, `analysis.py`, `prompts/01` | hygiene | M |
| S1-44 | **The seam annotation has no consumer.** `discontinuities` (S1-16/17/39) round-trips through serialisation and is legible in the JSON, which is all its docstring claims. But the numbers it annotates are published to humans in two places that never read it — the degraded comment's `Submission {pr_count}` and the leaderboard's Submissions column. The annotation protects a reader of the file; the figure leaks to everyone else unqualified. Deliberate scope for the ledger rung, filed so the next reader does not mistake it for an oversight. | `leaderboard.py`, `review.py` | ledger | M |

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
