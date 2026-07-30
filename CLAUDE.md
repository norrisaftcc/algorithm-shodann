# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**SHODANN** (Simple, Heuristically Operated, Dynamically Adversarial Neural Network) is a spec for a GitHub Actions bot that posts satirical, growth-focused code review on student PRs. Its one real idea: rank students by **learning velocity** (rate of improvement) rather than absolute skill — a student going 0% → 30% coverage outranks one holding at 90%. Parent project: AlgoCratic Futures, a satirical corporate-dystopia teaching framework.

**It runs.** As of 2026-07-26 this is a working system that reviews its own pull requests, not the documentation repo the older sections below were written against.

- `src/shodann/` — the implementation. Velocity engine, prompt assembly, output validator, groundedness probe, clearance calibration, capability declaration, citizen ledger.
- `.github/workflows/shodann.yml` — live, two jobs, posts a comment on every PR to this repo.
- `tests/` — 467 tests, including golden tests against the JS oracle, contract tests that read the workflow YAML as text, and groundedness probes that read the assembled output. One test is skipped on purpose (`reduced_allocation` is not synthesised); any other skip is a bug — see the guard rule in Landmines.
- `design_docs/sprints/2026-07-28/` — one sprint, documented end to end: `01-candidates.md` (the live backlog — 37 surveyed items plus nine filed since, and a Closure section that is the only place recording which are done), `02-prediction.md`, `03-treatment.md`, `04-retro.md`, `05-assay.md`.
- `.claude/skills/the-algorithm/` — a vendored discipline, pinned by commit. **Never edited here.** See `design_docs/addenda/the-algorithm.md`.
- `design_docs/growth-velocity.js` — the **reference oracle**, not the runtime. Kept so the port stays checkable. Do not extend it.
- `design_docs/shodann-core.yml` — the historical 5-job draft. Never deployed, unsafe as written (see Landmines 1). Read it for the literal tool invocations; do not copy it.

`README.md` is in-persona satire with no product content — never mine it for requirements.

**`design_docs/EARLY_RUNS.md` is the highest-value file in the repo for a new session.** Twenty-five defects found by running the system, every one of which the test suite was green through. Read it before trusting that a passing suite means the thing works — entry 13 is a guard whose own test passed with the guard deleted, and entry 15 is a defect that made synthesis impossible for every citizen while the fallback told a fluent story about it. **Entries 17-24 are one sequence and the closing table is the point**: fourteen reviews of one pull request, eight defect classes, and every class fixed with a *probe* held on the next run while every class fixed with *prose alone* came back. **Three of the first eleven rounds found a defect caused by the previous round's fix** - none visible in the diff - so read the output after every fix rather than after the last one. Two of those were extra numbers handed to the model beside a number it already had: never supply a second figure for a quantity the first one already covers.

**Addenda live in `design_docs/addenda/` and are linked from here.** This file has almost no slack — an assay found 161 of 190 sentences load-bearing, so a reader who skims loses instructions rather than filler. Put detail in an addendum and name it here. An unlinked addendum does not exist.

| Addendum | Read it before |
|---|---|
| `design_docs/addenda/the-algorithm.md` | writing any plan or document a later session will act on |
| `design_docs/addenda/accumulation.md` | committing a second change before reading the first one's output |

### Source precedence when documents disagree

**Executable code > `design_docs/` > `prompts/` > `design_docs/shodann-architecture-prototype/` > README.**

They disagree constantly (see Landmines). `design_docs/README.md` sets the last rule itself: files directly in `design_docs/` are current; anything under `shodann-architecture-prototype/` is historical, corroborating only. Prose restatements of the velocity formula in `PRD.md` and `SHODANN_CLAUDE.md` are all partial.

Since the port, **`src/shodann/` outranks everything**, including `growth-velocity.js`. The JS is the oracle the Python is *checked against*, not the source of truth about current behaviour — the two have deliberately diverged where the JS was wrong (Landmine 5) and where PRD invariants demanded it.

### Language: Python (decided 2026-07-25)

The open "Python vs JavaScript" issue is resolved in favor of **Python**. Rationale, so it is not re-litigated: every hard-analysis tool in the spec is Python-native (`py_compile`, `flake8`, `pytest`/`pytest-cov`, `radon`, `bandit`, `safety`); the code being graded is Python and edge-case detection greps `\.py$`; JS/TS analysis is explicitly out of scope for v1; and the maintainer is a Python implementor. Node buys only a subprocess layer around Python tools.

`growth-velocity.js` becomes the **reference oracle**, not the runtime: port it, and keep golden tests comparing Python output against the JS output on fixture metrics. Porting gotcha — JS `Math.round(x*100)/100` is half-up, Python's `round()` is banker's rounding; use `math.floor(x*100+0.5)/100` or `Decimal` if the golden tests must match exactly.

### Toolchain: frozen for cohort 1 (decided 2026-07-25)

**`ruff` + `pytest`/`pytest-cov` + `bandit` + `pip-audit`**, plus `python -m py_compile`. The specs were authored in early 2025 and their tool list is superseded — `PRD.md` §8 Decisions is now the authority.

- **ruff replaces flake8 *and* radon**, `line-length = 100`, version pinned (pre-1.0, weekly cadence). SHODANN names the flake8 rule equivalent alongside ruff's in feedback so students recognize both; that mapping belongs in the DATA layer, not improvised by the model.
- **Maintainability Index is dropped** and radon with it. "This function has 12 branches" is actionable; "your MI is 64" reads as a grade, which §7 forbids. Cyclomatic complexity comes from ruff `C901`.
- **`safety` is broken, not merely dated** — `safety scan` now requires account creation, its free DB updates monthly, and that DB is not licensed for commercial use. **`pip-audit`** replaces it (PyPA-official, first-party `pypa/gh-action-pip-audit`).
- **`bandit` stays** for the RAGE STATE deep pass; ruff's `S` rules are a ported subset, fast inline feedback only.
- **The freeze is the point.** Ruff's `C901` and radon's numbers differ. Anything feeding the velocity score must not change mid-cohort or every baseline resets. Adding a new signal is fine; changing or removing one is not.
- **`run-gemini-cli` is maintained but the wrong shape** — it drives an agentic CLI that decides what to do, while SHODANN has a fixed prompt and a fixed output format. Call the Gemini API directly from Python (`google-genai`); cheaper, testable offline, no agent loop. `gemini-2.5-flash-lite` / `gemini-3.5-flash-lite` is the tier for a <400-word review.
- **Do not build on GitHub Models** — fully retired 2026-07-30.
- **Two model wire formats, and only one is a config change.** `src/shodann/llm.py` speaks OpenAI-compatible `/chat/completions` (Gemini, Ollama, vLLM) and, as a fallback when the configured model cannot be reached, Anthropic's Messages API through the official `anthropic` SDK — a different body, response shape and auth header, so it is a port, not a base-URL edit. `ANTHROPIC_API_KEY` alone enables it; `claude-haiku-4-5` is the default tier. The wire is set explicitly, never sniffed from the URL.
- **Use Jinja2** rather than the hand-rolled `{{ IF }}`/`{{ FOR EACH }}` shell substitution. The existing `{{ PLACEHOLDER }}` syntax is already Jinja-compatible, and `{% include %}` is exactly the layered-fragment assembly `prompts/` wants.
- **CI runtime:** `uv` + `astral-sh/setup-uv` (`uvx ruff check`, `uvx pip-audit` — no install step). Note `actions/setup-python` v7 removed the `pip-install` input; artifact/cache actions v1–v3 are long dead.
- Worth reading before rebuilding comment plumbing: `qodo-ai/pr-agent`. Avoid `villesau/ai-codereviewer` (dead since 2023).

## Commands

Every command below is the same string on Windows, Linux, macOS and a Codespace. `scripts/dev.py` runs on the system interpreter and builds `.venv/` if it is absent, so a fresh clone needs no setup step.

```bash
python scripts/dev.py test     # pytest -q
python scripts/dev.py check    # ruff check .
python scripts/dev.py all      # both; both must be clean before a PR
```

One test: `python scripts/dev.py test tests/test_review.py::test_name` — trailing arguments pass through. **Never put a venv-relative interpreter path back into this section.** Naming only `.venv/Scripts/python.exe` made every non-Windows session start from a command that cannot work, for months, unnoticed. `.github/workflows/tests.yml` now gates the suite on Linux *and* Windows across 3.11–3.13, which is what makes the promise above checkable rather than asserted.

**Rendering a review is a distinct check from testing one, and it has found what tests could not.** Two of the entries in `EARLY_RUNS.md` came from printing the comment and reading it — including a comment whose two sections contradicted each other about coverage while 243 tests passed.

```bash
python scripts/dev.py render
```

Offline and read-only by construction: no model is configured, so it takes the REDUCED ALLOCATION path, and it never writes the ledger. `--event`, `--mode` and `--reports` are passed through.

Watching a live run: web and container sessions have no `gh` and use the GitHub MCP tools. On the maintainer's Windows box `gh` is not on PATH either — it is `"/c/Program Files/GitHub CLI/gh.exe"`.

Tool commands in the specs run against the *student's* repo, not this one: `python -m py_compile`, `pytest --cov=. --cov-report=json`, `ruff check . --output-format=json`, and `bandit -r . -ll` (RAGE STATE only). `flake8` and `radon` appear throughout the specs and are superseded — see the toolchain freeze above.

## Architecture: what ships, and the 5-job design it came from

**Shipped** (`.github/workflows/shodann.yml`), two jobs on `opened`/`synchronize`/`reopened`/`closed`:

| Job | Holds | Does |
|---|---|---|
| `analyse` | `contents: read`, **no secrets** | runs the citizen's pytest and ruff, uploads `coverage.json` + `ruff.json` as an artifact |
| `review` | `contents: write`, `pull-requests: write`, the model key | downloads the artifact, composes the comment, posts it; writes the ledger **on merge only** |

**That split is the security property**, and it is why coverage waited until season two: measuring coverage means running untrusted code, and running untrusted code must not happen next to a write token. Do not merge these jobs, and do not add a step that executes citizen code to `review`. `tests/test_workflow_contract.py` fails if you do.

Two other rules the workflow encodes, both learned the hard way (`EARLY_RUNS.md` 7, 8):
- A review runs on every push and **writes no state** (`--dry-run`). The ledger is written once, on merge, against the base branch. Writing it per-push made SHODANN conflict with its own PRs.
- Checkout takes `head.ref` normally and `base.ref` on close, because the head branch is usually already deleted by the time the closed event arrives.

**Design, never deployed** — `shodann-core.yml`: `shodann-initialize` → `shodann-hard-analysis` → `shodann-velocity` → `shodann-synthesis` → `shodann-metrics` (only the last has `if: always()`).

| Job | Reads | Emits |
|---|---|---|
| 1 INITIALIZE | `.shodann/clearances.json`, `.shodann/security_debt.json`, citizen history | clearance level, `RAGE_ACTIVE` + `RAGE_REASON`, prior metrics |
| 2 HARD ANALYSIS | the PR's source | syntax / style / tests / coverage / complexity, + bandit **only if RAGE** |
| 3 VELOCITY | job 1 + job 2 outputs | `velocity_score`, `coverage_delta`, `iteration_count`, report text |
| 4 SYNTHESIS | everything above | assembled prompt → Gemini → PR comment |
| 5 PERSISTENCE | job 3/4 output | citizen JSON, `METRICS.md`, security debt |

**The hard/soft split is the load-bearing design decision.** Hard tools produce facts and cannot hallucinate; the LLM only *reframes* them pedagogically and must never invent a metric. Grasping this means reading `design_docs/SHODANN_CLAUDE.md` (rationale) against `growth-velocity.js` (what job 3 computes) and `shodann-core.yml` (what job 2 shells out to). The JS engine's richer outputs — `celebrations[]` / `opportunities[]` — have no counterpart in the YAML job of the same name.

Degradation is always graceful: any failure still posts *some* feedback (rules in `PRD.md` §8).

Deployment contract, from `shodann-core.yml`'s own SETUP REQUIRED header: `GEMINI_API_KEY` in repo secrets; file copied to `.github/workflows/shodann.yml`; `.shodann/` created for state; clearance configured in repo variables. Its `env:` block (`COURSE_NAME`, `CURRENT_WEEK`, `DEFAULT_CLEARANCE "2"`, `CELEBRATION_LEVEL "startup"`, `GROWTH_FOCUS`, two `RAGE_*` knobs) and `permissions:` block (`contents: write`, `pull-requests: write`, `issues: read`) travel with it.

## Velocity scoring

`calculateVelocity(current, previous, iterations)` is canonical. The composite score, **with its guards** — they are load-bearing:

```
  coverage*2.0 + testCount*1.5 + log2(iters+1)*0.5*iters + docstrings*0.8
+ (complexityΔ > 0 ? (testCountΔ > 0 ? complexityΔ*0.3 : complexityΔ*0.09) : 0)
+ (lintIssuesΔ > 0 ? sqrt(lintIssuesΔ)*0.5 : 0)
```

Drop either guard and you get a penalty for reducing complexity, or `sqrt(negative)` = NaN on any submission that *adds* lint issues — which is most first submissions.

- `deltas.lintIssues` is **inverted** (`prev - current`, positive = fewer issues); every other delta is `current - prev`.
- Thresholds: `exceptional 10`, `positive 3`, `baseline 0`. Iteration celebration at `3`, exceptional at `7`.
- First submission does not short-circuit: `createBaselineMetrics()` is all zeros, so the first coverage delta equals absolute coverage.
- `celebrations` is guaranteed non-empty; `opportunities` can emit **three** items while every output contract caps Growth Opportunities at two — job 4 or the engine must truncate.
- No branch is punitive: a negative score still yields "🔄 Refactoring phase detected".
- `velocityHistory` keeps 10 `{score, date}` entries newest-first; `calculateTrend` averages the newest 3.

**Weights, thresholds, and curve shape are explicitly tunable** — the owner expects them to change as real submissions come in. What is *not* negotiable is the behavioral contract: iteration can never subtract, no branch is punitive, and improvement outranks position.

**US-1.3 shipped** — a first test (0→n%) does outweigh an equal later gain (50→50+n%). `_coverage_multiplier` (`velocity.py:131`) scales the coverage term by remaining headroom, `FIRST_TESTS_PHRASE` (`:34`) carries the wording the PRD requires, and `ORACLE_CONFIG` sets `first_test_bonus` to 0 so the golden tests still reproduce the JS's flat curve. No test pinned the bonus until S1-05; changing it silently flattens the curve into every baseline.

**One PRD invariant the code still does not satisfy**, an open design question rather than transcription work: "coverage delta > 0 ⇒ score increases" cannot hold, because the function never reads the previous score and a coverage gain paired with a test-count drop scores lower.

**A property of the coverage term, recorded and not fixed** (`S1-46`, `EARLY_RUNS.md` 25): coverage is a ratio, so *deleting* untested code raises it exactly as testing it would — and coverage is the 2.0-weighted term. Nothing computes a wrong number; every honest correction changes what coverage means, which §8's freeze forbids after cohort 1's first submission. Decide it before the cohort or it stands for the cohort.

## Prompt assembly

Assembly order (`prompts/README.md`, `prompts/06_assembled_example.md`): **edge-case check → first-PR vs returning → RAGE conditional → clearance calibration → generate.** Edge-case handlers short-circuit on first match. Whether *first-submission* replaces or augments the base prompt is contested: `06` says the onboarding template is used "instead", while `04` says "INJECT first_submission_additions" and replaces only the format block. Resolve before implementing.

Despite the universal "4-layer" label, `01_base_shodann_prompt.md` has five banners: LAYER 0 IDENTITY, 1 CONTEXT, 2 DATA, 3 PEDAGOGICAL, 4 FORMAT. It carries ~31 placeholders; `prompts/README.md` §Variable Quick Reference maps most to their source. Six are *composed sections*, not scalars, and need their own assembly step: `{{ MODE_STATEMENT }}`, `{{ HISTORY_NARRATIVE }}`, `{{ VELOCITY_ASSESSMENT }}`, `{{ SECURITY_SECTION }}`, `{{ CLEARANCE_INSTRUCTIONS }}`, `{{ RAGE_SECTION_IF_ACTIVE }}`.

Placeholders are `{{ UPPER_SNAKE }}` **with inner spaces**, and templates `04`/`05` also embed control flow an assembler must *interpret*, not substitute: `{{ IF … }}`/`{{ ELSE }}`/`{{ ENDIF }}`, `{{ FOR EACH x IN y }}`/`{{ END FOR }}`, and expressions like `{{ TESTS_PASSED + TESTS_FAILED }}`. This is why the `envsubst` loop documented in `prompts/README.md` cannot work (it expands `$VAR` only) — a real template engine is a hidden dependency of job 4.

Edge-case detection (`05_edge_case_handlers.md`): `EMPTY_PR` = `files_changed == 0 OR python_files == 0`; `ALL_FAILING` = passed==0 && failed>0; `MASSIVE_PR` = added>500 || files>15; `SYNTAX_BARRIER` = syntax_errors>0; `CONFIG_ONLY` = all changed files are md/json/yml/yaml/toml/txt/cfg/ini. RAGE is skipped for EMPTY_PR, SYNTAX_BARRIER, CONFIG_ONLY. Two known defects there: the selection logic routes zero-`.py` PRs to `CONFIG_ONLY` before EMPTY_PR's second clause can fire, and the detection matrix lists a sixth handler, `HANDLER_DOCS_ONLY`, that has no template and is never emitted. **Adding an edge case means extending `05` + its selection logic + the workflow detection step**, per `prompts/README.md` §Extending the Templates — not creating a new numbered file.

## Output contract and voice

These rules govern **generated PR-comment output only** — not your replies to the user, commit messages, or issue text. Do not speak in the SHODANN persona while working on the repo.

Standard path, exact headings in order:

```
## 🤖 SHODANN Analysis Complete
**Citizen**: @user | **Clearance**: LEVEL | **Velocity**: SCORE
### 🚀 Shipping Velocity Report      (2-3 sentences)
### ✅ Algorithm-Approved Patterns   (2-3 bullets)
### 📈 Growth Opportunities          (max 2 bullets)
### 🔧 Recommended Iteration         (exactly 1 action, <30 min)
### 🔒 Security Observations         (RAGE only, 1-3 findings)
*The Algorithm sees your growth. The Algorithm is pleased.*
```

Under **400 words**, posted within 120 seconds. Emoji in headers only; 📈/📉 for deltas are the sole in-paragraph exception. Edge-case handlers and first-submission mode each define their own headings, header fields (`Status: PENDING` / `PRE-EXECUTION`, `Velocity: N/A`), closer, and word cap — `prompts/05` sets ~200 words for EMPTY_PR. Do not impose the standard contract on them. Clearance also overrides the base layer: INFRARED gets 1 growth opportunity and a <15-minute next step, not 2 and 30.

Mandatory substitutions — `design_docs/SHODANN_VOICE_GUIDE.md` wins wherever the templates disagree:

| Never | Always |
|---|---|
| Wrong | Suboptimal |
| Mistake | Growth opportunity |
| Failed | Pre-success state |
| Error | Unexpected behavior pattern |
| Bad code | Algorithm-misaligned implementation |
| You should | The Algorithm suggests |
| You need to | The Algorithm recommends |
| Good job | The Algorithm is pleased |
| Great work | Velocity: OPTIMAL |
| I noticed | The Algorithm has observed |
| Unfortunately | The Algorithm notes an opportunity |

Forbidden outright: "This is wrong", "You failed", "This is a common mistake", "Unfortunately…", and any character break ("As an AI…"). Never suggest fewer commits — iteration is a positive term in the score. **Break character** only for genuine student distress, academic-integrity concerns, accessibility accommodations, or direct instructor communication. SHODANN is benevolent while *performing* mild menace: unsettlingly helpful, never hostile.

## RAGE STATE

**Reinterpretation deferred, and the name is reserved.** The mode is specified as a cybersecurity audit and is entirely unimplemented - no `RAGE`, `security_debt` or `lottery` anywhere in the shipped workflow, and only two dead stubs in `src/` (`rage_state_encounters`, never incremented or read; a `rage_section` parameter no call site passes). An audit found roughly two-thirds of the spec **subject-neutral**: the `SD-NNN` mint plus `Resolves:` close-by-reference loop, the ledger schema field for field, the safeguards, the caps and the escalation ladder all work for any carried item, while the bandit/pip-audit stack and `SECURITY_PATTERNS` are the security-specific remainder. So the mode may later be turned from *"special interest in your hard work"* to **"preventing your attempt at a singularity"** - a compaction pass over accumulated unresolved work, triggered by the measured condition in `EARLY_RUNS.md` 25 rather than by a lottery. **Deferred, not declined**; the reasoning is on closed issue #63 and must not be re-derived. The spec below stands as written.


An **additional** `### 🔒 Security Observations` section, not a replacement mode. Five triggers are documented in `design_docs/RAGE_STATE.md`, but MVP is **lottery + PR-body keyword only** — `PRD.md` §7 defers the `shodann:rage-state` label trigger (a stub comment in the YAML), the TA dispatch UI, and graduated debt escalation to v1.1. The coded checks run in sequence and each unconditionally overwrites `RAGE_REASON`, so the lottery and security-debt checks clobber a student's explicit "audit me"; precedence is undefined and must be decided. Keyword matching is also broken as written (`tr ',' ' '` splits `challenge mode` into two words, so any PR body containing "mode" or "review" trips RAGE).

Knobs: `RAGE_LOTTERY_PERCENTAGE "10"`, `RAGE_TRIGGER_KEYWORDS`, `RAGE_FULL_SCAN_CLEARANCE "3"`, `RAGE_MAX_FINDINGS "5"`, `RAGE_STATE_ENABLED` kill switch. Security debt is a ledger: findings mint `SD-NNN` ids, students clear them with `Resolves: SD-001` in a later PR body. `RAGE_STATE.md` holds `SECURITY_PATTERNS`, safety limits, the `security_debt.json` schema, and `.shodann/exemptions.json`; the per-finding escalation ladder ("The Gentle Escalation") is in the voice guide. RAGE must never be punitive.

## Landmines — read before writing implementation code

These were written against the specs, before the port. **3, 5, 6, 7 and 9 are resolved in `src/shodann/` and the shipped workflow** — they are kept because `design_docs/` still carries the defective versions and a fresh reading of those files will re-derive them. 1, 2, 4, 8 and 10 still bite.

Four more, learned from running it:

- **A green suite proves very little here.** Twenty-five defects in `EARLY_RUNS.md`, all found by running the system, all with the suite passing — including three that were contracts *between the workflow YAML and the program*, which no test could see until `tests/test_workflow_contract.py` started reading the YAML as text. **Revert every new guard against the defect it was written for before believing it.** Nine probes were run that way on 2026-07-29 and one guard had been green since birth against nothing. Reverting is necessary and not sufficient: a guard **scoped to the thing you changed** passes its own revert and still misses the defect. Entry 18 took three attempts because two guards asserted on the prompt row that had already been fixed, while the figure was arriving from `describe_history` all along. Assert on the assembled output, not on your edit. And a guard that never runs is worse than one scoped too narrowly: entry 25 found a test parametrised over three files that skipped all three for its whole life, so `sss` read as a pass. **Check that a new test executes at all** - a skip and a pass are one character apart in a summary line.
- **A loop is evidence that a boundary is wrong.** The floor is Audience, Scope, Format, Path (`design_docs/addenda/the-algorithm.md`); an unterminating loop implicates one or more and *always* implicates **Scope**, because the other three produce one wrong artifact while only a wrong boundary produces another pass. Four for four on PR #61 (entry 25). So count the passes: three attempts at one defect is not persistence, it is a scope you have not restated. And measure the rate, not just the count - **commit interval below time-to-observe-consequence** means you are landing changes on top of unobserved change, which is the one condition the suite cannot see because the suite stays green throughout it.
- **Anything feeding the score must not be choosable by the citizen being scored.** `--cov=.` counted a student's own test files in the coverage denominator, and `ruff check` without `--isolated` let their `pyproject.toml` decide which rules were counted. Both were live; both are now asserted in `tests/test_workflow_contract.py`. **The third instance was a file, not a flag**: nothing deleted the report files first, so a citizen could commit a `coverage.json` claiming 97% and break their own test collection to make it survive (`EARLY_RUNS.md` 12). Reading the flags again would never have found it. This is the lines-of-code metric in a new unit — check any new signal against it before adding one, and ask what the citizen could *put in the checkout*, not only what they could configure.
- **The freeze is a deadline, not a preference.** `PRD.md` §8 freezes the measurement set for cohort 1, so a defect in a *measurement* is free to fix today and impossible after the first real submission — fixing it later invalidates every student's history. Adding a signal stays legal mid-cohort; changing or removing one does not. Sort measurement work by that clock, not by value.
- **The break-character rule is buried in both documents that carry it** — `design_docs/SHODANN_CLAUDE.md` at sentence 115 of 165 in a subordinate clause, `design_docs/SHODANN_VOICE_GUIDE.md` at 157 of 160. It governs student distress, academic integrity and accessibility, and a model assembling a prompt reads 150 lines of persona enthusiasm before reaching it. **Unfixed**; see `design_docs/addenda/the-algorithm.md`.
- **Absent is not zero, everywhere.** An unmeasured coverage reading and a measured 0% are different facts, and collapsing them produced both a fabricated 98-point celebration and a −405 score for a citizen whose analysis job merely died. `AnalysisReports.coverage`, `CitizenRecord.coverage_instrumented` and `reconcile_coverage` exist to keep them apart; a delta is only claimed when both sides were measured. A *measured* zero is untouched — 0 → 30 is US-1.3's flagship case. The same rule now governs the test tallies, the syntax count and the style count: `AnalysisReports` carries `None` for each, `tests_instrumented` is the companion to `coverage_instrumented`, and template 01 drops the rows and forbids the claim rather than printing a zero. **`build_context` takes one `AnalysisReports`, never loose numbers** — it used to take six, defaulting to zeros that `review()` never overrode, so every review told the model that nothing failed and nothing was checked.

1. **`shodann-core.yml` is unsafe to copy as-is.** Line 131 interpolates `PR_BODY="${{ github.event.pull_request.body }}"` straight into a `run:` block, and the PR title goes into the Gemini prompt at line 511. A student-authored body containing `$(…)` or backticks executes shell on a runner holding `contents: write`, `pull-requests: write`, and `GEMINI_API_KEY`. Move every student-controlled field into an `env:` mapping and reference it as `"$PR_BODY"`.
2. **Never accept a fork PR into this design** (resolved 2026-07-25 — topology is org-owned public repos, one per student, branch PRs, plain `pull_request` trigger). Forks withhold secrets and issue a read-only token, which disables the LLM call, the comment, and persistence simultaneously. Because same-repo branch PRs are the shape, `pull_request_target` is never needed — which also keeps us clear of the `actions/checkout` v7 restriction on fork heads (enforced 2026-07-20; the opt-out is named `allow-unsafe-pr-checkout`). Persistence still checks out the *base* repo only and takes analysis results as artifacts. Public repos add free CodeQL/Dependabot/secret scanning as a Security-tab signal — never as a data source for the comment.
3. **Cross-job transport is unsolved.** Reports cross job boundaries through `$GITHUB_OUTPUT` heredocs; any flake8/pytest/bandit output containing a bare `EOF` line terminates the delimiter early, and job outputs are size-capped. Use `actions/upload-artifact` or collapse jobs.
4. **Citizen-state schema is settled** (2026-07-25) — snake_case, unquoted numbers, extended from the `prompts/04` shape, plus `kind` (`human`|`agent`) and a `display` block for opt-in leaderboard naming. Canonical example is in the closed schema issue and `PRD.md` §8. **Storage is local truth + central mirror**: the authoritative record is `.shodann/citizens/{username}.json` in the student's *own* repo, written by the run that produced it; a scheduled job in the course repo aggregates into `METRICS.md`. The mirror is derived — if it disagrees, the student's file wins. The camelCase shape in `growth-velocity.js` and the mixed-quoting shape in `shodann-core.yml` are both **historical**; do not resurrect either.
5. **The JS state file does not round-trip.** `saveCitizenHistory` reuses `loadCitizenHistory`'s return object, so it persists `streak` and a dead `previous` key, while `loadCitizenHistory` reads `data.iterationStreak` — a name that is never written. Streaks silently reset to 0 every run. Fix before porting.
6. **Two velocity formulas.** `shodann-core.yml` computes a flat `(coverage_delta * 2) + (iterations * 0.5)` with thresholds `>5`/`>0`; the JS computes the six-term composite with `>=10`/`>=3`. Same field name, different numbers.
7. **Two leaderboards.** The YAML orders by `ls -t` file mtime (not velocity at all, Clearance hardcoded `TBD`); the JS sorts by `lastVelocity` and caps at 20 with emoji trends. `PRD.md` US-3.2 requires velocity sort, six columns, the enum `ascending|descending|stable|new`, and that *all* citizens appear.
8. **`.shodann/clearances.json` exists** - this landmine's original claim that no example existed was true until 2026-07-28 and is now false; the file has shipped since #56 and `state.read_clearance` reads it on every review (`src/shodann/review.py`). Kept because its *second* clause still bites. Its shape is only inferable from `shodann-core.yml:98`: a flat `{username: "N"}` map, default `"2"` (RED). Clearance numerics are 1=INFRARED … 6=BLUE+; MVP covers INFRARED–GREEN. `prompts/03`'s `INFER_CLEARANCE` fallback has no terminal ELSE, defaults new citizens to RED, and its ORANGE branch shadows YELLOW, so tests+docstrings can never infer above ORANGE.
9. **There is no defined home for implementation code** — no `src/`, and `design_docs/` is declared to be design, not runtime. Decide with the user whether the port lands in a new top-level package, and whether `shodann-core.yml` stays as spec with a derived copy in `.github/workflows/`. Creating `.github/workflows/` converts this from a docs repo into one that executes on every PR — confirm before doing it.
10. **`SHODANN_CLAUDE.md` paths are wrong.** It cites `growth-velocity.js`, `shodann-core.yml`, `RAGE_STATE.md` as bare filenames; all live under `design_docs/`. It also references parent-project AlgoCratic files that do not exist here.

## Where to look

| Question | File |
|---|---|
| **What broke when it ran, and why** | `design_docs/EARLY_RUNS.md` |
| **The live backlog — 46 items, and which are closed** | `design_docs/sprints/2026-07-28/01-candidates.md` |
| How this repo negotiates, and the floor test | `design_docs/addenda/the-algorithm.md` |
| Why correct changes still compound into a problem | `design_docs/addenda/accumulation.md` |
| What a second repository would need to subscribe (it cannot today) | `design_docs/ONBOARDING_A_REPOSITORY.md` |
| Which documents are below floor, and where their operative sentences sit | `design_docs/sprints/2026-07-28/05-assay.md` |
| Velocity math as shipped, guards, US-1.3 | `src/shodann/velocity.py` |
| Citizen ledger, clearance names, atomic writes | `src/shodann/state.py` |
| Output contract per mode, clearance overrides, forbidden vocabulary | `src/shodann/validator.py` |
| Orchestration, degradation, coverage reconciliation | `src/shodann/review.py` |
| Reading tool reports; why nothing here runs a tool | `src/shodann/analysis.py` |
| What a model may not say about a number it was given | `src/shodann/groundedness.py` |
| Clearance postures (teaches → mentors → reports) | `design_docs/CLEARANCE_REGISTER.md` |
| Leaderboard partition: human vs agent, ORANGE gate | `design_docs/LEADERBOARD.md` |
| The agent fleet, its three epistemic positions | `.claude/agents/README.md` |
| Scope, out-of-scope, Gherkin acceptance criteria, error handling | `PRD.md` |
| Pipeline rationale, hard/soft split, integration points | `design_docs/SHODANN_CLAUDE.md` |
| Voice: vocabulary, forbidden phrases, emoji sets, clearance buckets | `design_docs/SHODANN_VOICE_GUIDE.md` |
| RAGE triggers, `SECURITY_PATTERNS`, debt & exemption schemas | `design_docs/RAGE_STATE.md` |
| Canonical velocity math, state shape, CLI | `design_docs/growth-velocity.js` |
| Draft pipeline, literal tool invocations, clearance→flake8 mapping | `design_docs/shodann-core.yml` |
| End-to-end worked prompt + expected output | `prompts/06_assembled_example.md` |
| Detection thresholds, five handler templates | `prompts/05_edge_case_handlers.md` |

## Process

Work flows through GitHub issues; issue state is not in the repo, so **confirm priorities and blocking dependencies against live issues** rather than any list written down here or in `PRD.md`. Blocking is signalled by `design_discussion.yml`'s `decision-urgency` field. Note that **no issue template can apply `status: blocked`** — all four apply `status: needs-review` plus a type label — so "check for the blocked label" is unreliable advice.

**An open issue is a commitment** (convention adopted 2026-07-25, replacing `priority: critical|high|medium|low`). There are two states, not four: `priority: 1` means committed and being done this rung; anything not committed is **closed as declined** and tagged `priority: 2`, which exists only as a tombstone so the declined pile stays auditable (`is:closed label:"priority: 2"`). Product scope lives in `PRD.md` and `design_docs/` — the board is not a wishlist, and an issue reopens in one click when it becomes real work. Do not reintroduce intermediate levels, and do not leave an issue open to mean "someday."

One live issue per piece of work. The board previously carried two waves of the same six issues (#1–#8 re-filed as #9–#14), which is how a single undecided question propagated `status: blocked` across three dependents and froze them for seven months. If an issue is superseded, close it pointing at the replacement.

Branch → PR → review is convention only: there is no branch protection, no CODEOWNERS, and nothing enforces it. There *is* CI now — SHODANN reviews every PR to this repo, including its own. It posts a comment; it does not gate a merge. `.github/PULL_REQUEST_TEMPLATE.md` requires a 9-item pre-merge checklist plus an Educational Impact Assessment whose Pedagogical Alignment boxes encode the product invariants (growth-positive framing, clearance-appropriate, persona-consistent, velocity-over-position, no negative learning impact); non-student-facing PRs tick "Not student-facing" rather than leaving them blank.

## Permanently out of scope

Excluded on principle (`PRD.md` §7), not deferred: grade assignment, plagiarism detection, ranking by absolute skill, punitive language modes, and any surveillance students cannot see. `PRD.md` §8 sets the FERPA posture — no sensitive PII in state files, GitHub usernames only, no grades in state, API keys in GitHub Secrets.
