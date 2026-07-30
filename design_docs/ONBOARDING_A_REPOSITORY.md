# Onboarding a repository to SHODANN

**When to use this document**: you maintain a repository other than
`algorithm-shodann` and want SHODANN to review its pull requests — the actual
question this file answers, not "how do I read SHODANN's own PRs" (it already
does that; see `.github/workflows/shodann.yml`).

## Status: not possible today

**Do not attempt this by copying `.github/workflows/shodann.yml` into another
repository as written.** It will run, and it will post a comment on every pull
request, but every comment will be the same content-free fault notice, no
velocity will ever be computed, and no citizen ledger will ever be written.

The run does *not* stay green, and the distinction matters for who finds out.
`review()` raising makes `main()` return `EXIT_DEGRADED`, the compose step's
outcome becomes `failure`, and "Surface the fault to the maintainer"
(`.github/workflows/shodann.yml:312-316`) emits `::error::` and exits 1. So the
**maintainer** sees red on every run. What is silent is the half a maintainer
does not watch: the *citizen* receives a plausible comment on every pull
request, and the ledger their whole history lives in is never written even on
merge, because `save_citizen_history` is only reached from inside the `review()`
call that raised.

**The single blocking reason**: SHODANN's prompt templates live in `prompts/`
at the root of the `algorithm-shodann` repository, and the code that reads
them resolves that path against the process's current working directory —
which, in any workflow run, is wherever `actions/checkout` just put the
repository being reviewed. For every review to date that has been
`algorithm-shodann` reviewing itself, so the citizen's repository and
SHODANN's own template library have always been the same checkout. They stop
being the same checkout the moment a second repository is involved, and
nothing today gives that second repository a copy of `prompts/` or tells
SHODANN to look for it anywhere else.

### The same defect, in its dangerous direction

Everything above describes what happens when the citizen's repository has **no**
`prompts/` directory. The more important case is when it has one.

`review()` calls `render_prompt(context)` with no `prompts_dir`
(`src/shodann/review.py:644`), so the argument defaults to
`PROMPTS_DIR = Path("prompts")` — resolved against the citizen's checkout. A
citizen who commits `prompts/01_base_shodann_prompt.md` therefore supplies
SHODANN's entire instruction set: the identity layer, the data layer, the
pedagogical rules, the output contract, and every groundedness prohibition added
since. Nothing validates that the templates found are SHODANN's own.

Reproduced, not inferred. A copy of template 01 with one sentence prepended,
placed in a scratch repository, and rendered from that directory:

```
citizen text reached the assembled prompt: True
```

This runs in the `review` job, which holds `contents: write`,
`pull-requests: write` and the model key. It is `CLAUDE.md` Landmine 1's class —
citizen-controlled text reaching a privileged surface — in a place that landmine
does not name, and it is not defended by the `analyse`/`review` split, because
the split protects against running citizen *code* and this is citizen *text*
being used as instructions.

**It is latent, not live.** SHODANN reviews only its own repository today, so the
citizen's checkout and SHODANN's template library are the same directory and the
templates found are the real ones. It becomes live on the first external
repository — which means the packaging change #51 needs is a *security*
prerequisite for onboarding, not only a functional one, and onboarding must not
ship before it.

The minimum fix is that the prompt library must be located from the installed
package and never from the working directory, and a missing library must raise
rather than fall back to whatever `./prompts` happens to contain.

This is tracked as **issue #51** and named explicitly in the code, not
inferred by this document:

> ```
> # Note the asymmetry: `root` is the citizen's repository, but the
> # prompt library is SHODANN's own and is read relative to the working
> # directory. Rung 1 reviews this repository, so they coincide. They
> # will not once SHODANN reviews someone else's repo, and at that point
> # the templates need to ship as package data.
> ```
> — `src/shodann/review.py:639-643`

and

> ```python
> PROMPTS_DIR = Path("prompts")
> ```
> — `src/shodann/prompts.py:56`, a bare relative path, resolved by
> `render_prompt` (`src/shodann/prompts.py:451-470`) with no reference back to
> wherever the `shodann` package itself was installed from.

`pyproject.toml` confirms the templates have no other way to travel with the
code: `[tool.setuptools.packages.find] where = ["src"]` (`pyproject.toml:39-40`)
discovers only `src/shodann`. `prompts/` is a sibling directory at the repo
root — `git ls-files prompts/` lists seven files, none of them under `src/` —
and there is no `[tool.setuptools.package-data]` table, no `MANIFEST.in`, and
no `include-package-data` setting anywhere in the project. `pip install .`
against `algorithm-shodann` — or `pip install git+https://…/algorithm-shodann`
from anywhere — builds a wheel containing the `shodann` Python package and
nothing from `prompts/`. There is no installation of SHODANN, from any source,
that carries its own templates with it today.

### What actually happens if you try it anyway

Two independent defects compound, and both were traced by reading the code
rather than by running it against a second repository (out of scope for this
task — see the top of this document). In the order a run would hit them:

1. **The `review` job's install step is repository-specific and silently
   wrong once copied.** `.github/workflows/shodann.yml:232-233`:

   ```yaml
   - name: Install SHODANN
     run: pip install --quiet .
   ```

   `.` is whatever `actions/checkout` (the step just above) put in the working
   directory. In the shipped workflow that is always `algorithm-shodann`
   itself, because the workflow only runs on this repository — so `.` and "the
   SHODANN package" have always meant the same thing. Copy this file verbatim
   into another repository and the checkout step at the top of the same job
   checks out *that* repository, so `pip install --quiet .` tries to install
   the citizen's repository as a Python package. Most student/course
   repositories have no installable `pyproject.toml` or `setup.py` at all, so
   the step fails outright — and it has no `continue-on-error:`, unlike the
   "Compose the review" step three steps later, so the job stops there.
   `shodann.review` is never invoked.

   A failed step with no `continue-on-error:` still lets a later step run if
   that step's own condition is `if: failure()` — which is exactly the
   "Announce the fault" step's condition (`.github/workflows/shodann.yml:285-286`).
   So the citizen does get a comment: the fixed "REDUCED ALLOCATION / Resource
   Advisory" heredoc (`.github/workflows/shodann.yml:290-309`), with no
   metrics, no velocity, nothing citizen-specific — on every single pull
   request, indistinguishable from a real outage. The "Record the citizen
   ledger" step never runs either, because it comes later in a job that has
   already failed and its own condition does not include `always()`. Nothing
   is ever recorded.

2. **Suppose that install line is fixed first** — say, changed to install
   SHODANN from its own source (`pip install "shodann @
   git+https://github.com/<org>/algorithm-shodann.git@<ref>"`, addressing
   defect 1 in isolation). The job now gets as far as invoking
   `python -m shodann.review`. `render_prompt` still resolves
   `PROMPTS_DIR = Path("prompts")` against the checked-out citizen repository,
   which has no `prompts/` directory — **unless the citizen supplies one.** See
   the hazard section below; that case does not degrade, it succeeds.

   `extract_template` (`src/shodann/prompts.py:130-136`) raises
   `FileNotFoundError` reading a path that does not exist. That exception is
   not one of the two `review()` catches internally
   (`_AlreadyResolved`, `LLMUnavailable` — `src/shodann/review.py:646-650`), so
   it propagates out of `review()` entirely. `main()`'s outer
   `except Exception` (`src/shodann/review.py:696-703`) does catch it, so the
   process does not crash outright — it falls to `emergency_comment()`
   (`src/shodann/review.py:366-388`), a four-line "MINIMAL RESPONSE" comment
   with no metrics, and exits `EXIT_DEGRADED` (`3`). Because the exception is
   raised before `review()` ever reaches its `if write_state:` block
   (`src/shodann/review.py:656-664`), **`save_citizen_history` is never called
   — not on ordinary pushes (expected; `--dry-run` already suppresses this)
   and not on merge either**, where `--dry-run` is *not* passed
   (`.github/workflows/shodann.yml:354-358`). The ledger is permanently empty:
   `pr_count`, `velocity_history`, `iteration_streak` never move, because the
   one call that would populate them never runs. Every citizen looks, forever,
   like someone who has never submitted anything — the exact "absent is not
   zero" failure mode `CLAUDE.md`'s Landmines section already names for a
   different cause, reached here by a different path.

   The step itself exits 3 (non-zero), so — same as defect 1 — the "Surface
   the fault to the maintainer" step at the bottom of the job fires
   (`.github/workflows/shodann.yml:312-316`), turning the Actions run red on
   every PR while the citizen keeps receiving a content-free comment that
   looks, superficially, like the system is working.

Neither failure mode is loud in the one place a course maintainer is likely to
look first — the PR itself shows a posted comment, just an empty one — and
both were reachable purely by reading the code paths the shipped workflow
actually exercises. That is the reason this document does not proceed to a
numbered recipe: a recipe implies the missing step is procedural (a secret, a
file, a permission), and it is not. It is a code change.

## The smallest fix

Two changes, matched to the two things the review.py comment says are
missing ("the templates need to ship as package data") and the thing the
workflow additionally needs once they do:

1. **Ship `prompts/` as installable package data**, so it travels with `pip
   install shodann` regardless of what else is checked out in the working
   directory — for example, move or mirror the seven files under
   `src/shodann/prompts/` and add them via
   `[tool.setuptools.package-data]` (or `include-package-data = true` plus a
   `MANIFEST.in`), keeping the top-level `prompts/` directory as the
   human-readable source used by `prompts/README.md`'s worked examples if
   duplication is undesired, or retiring it in favor of the packaged copy.
2. **Make `render_prompt` resolve templates against where `shodann` is
   installed, not against the process's working directory** — e.g.
   `importlib.resources.files("shodann") / "prompts"` in place of the bare
   `PROMPTS_DIR = Path("prompts")` at `src/shodann/prompts.py:56`, with the
   existing `prompts_dir` parameter on `render_prompt`
   (`src/shodann/prompts.py:451-456`) kept as the test-time override it
   already is.
3. **Separately, once (1) and (2) land**: the workflow's `Install SHODANN`
   step (`.github/workflows/shodann.yml:232-233`) has to stop assuming `.` is
   SHODANN's own source. The template a copied workflow should carry is
   something like `pip install --quiet
   "shodann @ git+https://github.com/<org>/algorithm-shodann.git@<pinned-ref>"`
   — pinned, because the toolchain-freeze rationale in `CLAUDE.md` ("Anything
   feeding the score must not change mid-cohort") applies to the reviewer's
   own version exactly as it applies to `ruff==0.16.0` and
   `pytest-cov==7.1.0`; an unpinned `main` would let the prompt library (and
   therefore the review's shape) drift under a citizen without any change to
   their own repository at all.

None of these three are large, but they are code changes to `algorithm-shodann`
itself, not configuration in the repository being onboarded — which is why
this document cannot hand a course maintainer a self-service recipe yet.

## Prerequisites for onboarding, once the blocker above is fixed

Written now so the recipe exists the moment the blocker clears, and so the
constraints are visible while anyone is scoping the fix above — several of
them shape what "package data" and "install step" even need to do.

1. **Repository topology must match `PRD.md`'s decision, not a fork.**
   "Repository topology: org-owned public repos, one per student, branch PRs —
   not forks" (`PRD.md:444`). A fork PR withholds secrets and issues a
   read-only token, which silently disables the model call, the comment, and
   ledger persistence all at once — not a partial degradation, a total one,
   because `GITHUB_TOKEN` on a fork PR cannot write a comment either. The
   onboarded repository must be org-owned (or otherwise a same-repo-branch-PR
   setup) with the workflow triggered by plain `pull_request`, never
   `pull_request_target`.
2. **The `analyse` / `review` job split must be preserved exactly.** The
   `analyse` job holds `contents: read` and no secrets
   (`.github/workflows/shodann.yml:64-65`); it is the only job that executes
   citizen code (student tests, via `pytest --cov`) and it is the only job
   with nothing worth stealing. The `review` job holds `contents: write`,
   `pull-requests: write`, and the model key, and it never runs anything the
   citizen wrote — it only reads the JSON artifact the first job produced.
   Merging these jobs, or adding a step to `review` that executes checked-out
   code, defeats the reason coverage measurement is possible here at all (see
   `.github/workflows/shodann.yml:40-51`'s header comment) and is asserted
   against by `tests/test_workflow_contract.py`.
3. **Repository secrets and variables**, set in the onboarded repository (not
   inherited from `algorithm-shodann` — GitHub secrets do not cross
   repositories):
   - `secrets.SHODANN_LLM_API_KEY` — the primary model key, read by
     `LLMConfig.from_env` (`src/shodann/llm.py:97-104`). Without it,
     `LLMConfig.configured` is false and every review takes the "REDUCED
     ALLOCATION" facts-only path — not an error, the documented degradation.
   - `vars.SHODANN_LLM_BASE_URL`, `vars.SHODANN_LLM_MODEL` — which
     OpenAI-compatible endpoint and model to call.
   - `secrets.ANTHROPIC_API_KEY` (optional) — enables the fallback wire when
     the primary model is unreachable (`fallback_from_env`,
     `src/shodann/llm.py:127-148`). Keyed on presence alone; there is no
     separate opt-in flag, by design (`src/shodann/llm.py:127-130`), so do not
     set it unless the fallback is actually wanted.
   - `vars.SHODANN_FALLBACK_MODEL` (optional) — defaults to
     `DEFAULT_FALLBACK_MODEL` (`claude-haiku-4-5` per `CLAUDE.md`) if
     `ANTHROPIC_API_KEY` is set and this is left blank.
   - No GitHub Models integration — retired 2026-07-30 per `CLAUDE.md`, and
     never wired into `llm.py` regardless.
4. **`.shodann/clearances.json` must exist in the onboarded repository before
   the first PR**, or every citizen defaults to `DEFAULT_CLEARANCE = 2` (RED)
   — harmless, but worth setting deliberately if the course wants band
   variation from day one. It is a flat, string-or-int map,
   `{"username": "3"}` (`src/shodann/state.py:418-444`); `algorithm-shodann`'s
   own file is a one-line worked example:
   ```json
   {
     "norrisaftcc": "3"
   }
   ```
   (`/home/user/algorithm-shodann/.shodann/clearances.json`, checked in). It
   is the instructor's file to hand-edit — SHODANN never infers a band from
   readings (`src/shodann/state.py:84-92`).
5. **`.shodann/citizens/` needs no manual setup.** `save_citizen_history`
   creates it on first write (`src/shodann/state.py:589-590`); there is
   nothing to pre-populate.
6. **Know that the ledger writes only on merge to the default branch, never
   per-push.** `.github/workflows/shodann.yml:340-344`'s condition —
   `action == 'closed' && merged == true && base.ref ==
   repository.default_branch` — plus the `--dry-run` flag on every other run
   (`.github/workflows/shodann.yml:263-269`). A course maintainer expecting
   velocity to move on every pushed commit will be surprised; that is
   intentional (`.github/workflows/shodann.yml:26` and the surrounding
   comment) and was learned the hard way — writing state per-push made
   SHODANN conflict with its own open PRs.
7. **Leaderboard aggregation across repositories is separately blocked by the
   same issue #51.** `PRD.md:446` describes a scheduled job in a course repo
   reading across every student repo to rebuild a shared `METRICS.md`. That is
   a different artifact from the per-repository `METRICS.md` the `review` job
   already regenerates on merge (`.github/workflows/shodann.yml:378-379`,
   read `design_docs/LEADERBOARD.md` for the partition rules), and it needs
   the same fix as this document's blocker before it can exist — a
   cross-repository reader has the identical "whose `prompts/` is this"
   problem. Do not scope it as part of onboarding one repository.

## Onboarding steps (once the blocking defect is fixed)

1. Confirm the four topology prerequisites above (org-owned, branch PRs,
   plain `pull_request`, job split intact).
2. Copy `.github/workflows/shodann.yml` into the target repository at the
   same path, with the `Install SHODANN` step changed to install from
   SHODANN's own pinned source rather than `pip install --quiet .` (see "The
   smallest fix," item 3, above). Leave the `analyse` job's tool-install step
   untouched — it installs `ruff`, `pytest-cov`, and `pytest` for analysing
   the *citizen's* code, and has never depended on where SHODANN itself lives.
3. Set the secrets and variables listed in prerequisite 3, in the target
   repository's own Settings → Secrets and variables.
4. Add `.shodann/clearances.json` to the target repository, or accept that
   every citizen starts at RED.
5. Open a same-repo branch pull request against the target repository and
   confirm a comment posts within 120 seconds of the "review" job completing,
   carrying real velocity figures rather than a "REDUCED ALLOCATION" or
   "MINIMAL RESPONSE" notice.
6. Merge that pull request and confirm `.shodann/citizens/<username>.json` and
   `METRICS.md` were both created (or updated) by a commit from
   `shodann[bot]` on the target repository's default branch.

## Verification

- `python scripts/dev.py render` (run from an `algorithm-shodann` checkout,
  not the onboarded repository) renders a review offline and read-only — no
  model configured, so it takes the REDUCED ALLOCATION path and never writes
  the ledger (`scripts/dev.py:136-152`). It is a check on `algorithm-shodann`
  itself, useful for confirming a template/code change did not break
  self-review, not a way to test an external repository's setup — there is no
  equivalent dry run for a second repository until the blocker is fixed and a
  path like `--root <other-repo>` is exercised end to end.
- Once the fix lands, the equivalent local check for a second repository is
  `python -m shodann.review --event <path> --out out.md --root <checkout of
  the other repo> --reports <dir> --dry-run` run from wherever `shodann` is
  installed — confirm `out.md` contains real section headers (`### 🚀
  Shipping Velocity Report`, etc.) and not the four-line MINIMAL RESPONSE
  shape from `emergency_comment`.
- After a real PR, read the posted comment for internal consistency (two
  sections should not disagree about the same number) — `CLAUDE.md` records
  this as a check that has caught defects tests did not, twice.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Every PR gets the "🔒 Resource Advisory / REDUCED ALLOCATION" fixed heredoc, no velocity ever | The `Install SHODANN` step is running `pip install --quiet .` against the target repository instead of against SHODANN's own source (defect 1 above) |
| Every PR gets a four-line "MINIMAL RESPONSE" comment with `Clearance: PENDING`, `Status: MINIMAL RESPONSE`, no metrics | `render_prompt` cannot find `prompts/` in the checked-out working directory — the packaging half of the blocker is not fixed, or the onboarded repository lacks the fixed install step entirely (defect 2 above) |
| Comment posts, but with content that looks like it came from the citizen's own repository's `prompts/` directory | The citizen repository happens to contain a top-level `prompts/` directory of its own, and the CWD-relative resolution picked it up silently — flagged as a hazard above, not yet guarded against in code |
| Actions run is red even though a comment posted | Expected under both defects above (`exit 1` / `EXIT_DEGRADED`) — check whether the comment carries real metrics before treating the red run as the primary symptom |
| Ledger never updates even after a clean merge | Confirm the merge landed on `github.event.repository.default_branch` — merges into any other branch are deliberately not recorded (`.github/workflows/shodann.yml:318-333`, the stacked-PR lesson) |
| Every citizen shows RED regardless of ability | `.shodann/clearances.json` is missing or the username key does not match the GitHub login exactly — `read_clearance` returns `None` on any parse failure and the caller then uses `DEFAULT_CLEARANCE` (`src/shodann/state.py:418-444`) |
| A citizen who opted out still appears named on the leaderboard, or vice versa | Check `display.visibility` in that citizen's own ledger file — new records default to `anonymous` (`src/shodann/state.py:224`, changed 2026-07-29), but records that predate the change round-trip whatever they already had |

## Explicitly out of scope for "onboarding one repository"

- RAGE STATE's label trigger, TA dispatch UI, and graduated debt escalation —
  deferred to v1.1 regardless of topology (`PRD.md` §7, `CLAUDE.md`'s RAGE
  STATE section).
- Cross-repository leaderboard aggregation (`PRD.md:446`) — blocked by the
  same root cause as this document's headline blocker; see prerequisite 7.
- Any change to the frozen toolchain (`ruff==0.16.0`, `pytest-cov==7.1.0`) —
  onboarding a repository must not become an occasion to also bump a
  score-feeding tool version; that is a separate, cohort-boundary decision
  per `CLAUDE.md`'s toolchain-freeze section.
