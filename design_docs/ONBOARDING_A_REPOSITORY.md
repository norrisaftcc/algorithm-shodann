# Onboarding a repository to SHODANN

**When to use this document**: you maintain a repository other than
`algorithm-shodann` and want SHODANN to review its pull requests — the actual
question this file answers, not "how do I read SHODANN's own PRs" (it already
does that; see `.github/workflows/shodann.yml`).

## Status: possible, through the reusable workflow

**Do not copy `.github/workflows/shodann.yml` into another repository.** That
file is the self-review workflow. Its `review` job runs `pip install .`, which
is correct only while the repository under review *is* SHODANN. In any other
repository it installs the citizen's package into the one job that holds
`contents: write` and the model key. Copying it is unsupported and is not
described anywhere below.

A subscribing repository instead **calls**
`.github/workflows/shodann-review.yml` (`on: workflow_call`) from a short caller
file. The caller is `templates/subscriber/shodann.yml`. It pins the workflow and
the engine it installs to one full commit SHA of `algorithm-shodann`.

Four blockers stopped this until the branch `feat/haiku-primary-and-reusable-review`.
All four are fixed there. The reasoning that found them is kept, marked
superseded, in "History" at the end of this file.

| Blocker as first written | State now | Where it is fixed |
|---|---|---|
| Templates are resolved from the process working directory, so a citizen who commits `prompts/` supplies SHODANN's instructions | **Fixed.** `PROMPTS_DIR` is anchored on `__file__` (#66), and `default_prompts_dir()` never consults the working directory. | `src/shodann/prompts.py`; `tests/test_prompt_packaging.py` |
| The templates are not package data; a wheel holds 0 of the 7 `.md` files | **Fixed.** `prompts/` is mapped into the wheel as `shodann._prompts`. A source checkout wins; the installed package is the fallback; neither present raises `FileNotFoundError`. | `pyproject.toml`, `src/shodann/prompts.py` |
| The `review` job installs whatever repository was checked out | **Fixed for subscribers.** The reusable workflow checks the citizen out into `citizen/`, checks the pinned engine out into `engine/`, and runs `pip install ./engine` (non-editable). Nothing installs `citizen/`. | `.github/workflows/shodann-review.yml`; `tests/test_reusable_workflow_contract.py` |
| The reviewer's own version is not pinned | **Fixed.** `engine-ref` must be a full 40-character commit SHA, and that commit must be an ancestor of `main` in `norrisaftcc/algorithm-shodann`; the workflow refuses a branch, a tag, and a SHA that was never merged. **It does not check that `engine-ref` equals the `@` ref in `uses:`:** a called workflow cannot read the ref it was called at, so that equality is the caller's responsibility. | same |

`.github/workflows/shodann.yml` (self-review) is unchanged except for the
environment mappings its compose step gained. Converting it into a caller of
the reusable workflow is a follow-up, not part of this change.

### What is still true after the fix

These are constraints, not defects. Read them before you subscribe a course.

1. **A subscriber's secrets are readable by every collaborator with write
   access.** A `pull_request` run uses the workflow file as it stands on the
   pull request's own branch, so anyone who can push a branch can edit the
   caller to print a repository secret. The SHA pin protects the *engine*; it
   does not protect the *key*. Topology is where this lives: org-owned
   repositories, one per student, with the student holding write access. Use a
   dedicated Anthropic workspace key with a low monthly spend limit, one you can
   afford to lose and revoke. Do not reuse a key that pays for anything else.
2. **The leaderboard is off by default.** `leaderboard` defaults to `false` in
   the reusable workflow and is `false` in the template. With it off, the ledger
   commit adds `.shodann/` only; `METRICS.md` is not regenerated and not
   committed. A ranking of students is a course-governance decision, and the
   workflow does not make it by omission.
3. **Cross-repository aggregation stays blocked.** `PRD.md:446` describes a
   scheduled job in a course repository that reads every student repository and
   rebuilds one shared `METRICS.md`. Nothing here builds that. The per-repository
   `METRICS.md` that the `leaderboard: true` option regenerates is a different
   artifact. See prerequisite 7 below.
4. **Who may turn SHODANN on for a given course is not decided here.**
   For CTS-285 specifically, the course's own rules on in-character online
   material, leaderboards and streaks are owned by the course's instructional
   lead. `design_docs/SUBSCRIBING_A_CTS285_REPOSITORY.md` carries that gate. This
   document describes how the mechanism works. It is not an authorisation.

## Prerequisites for onboarding

1. **Repository topology must match `PRD.md`'s decision, not a fork.**
   "Repository topology: org-owned public repos, one per student, branch PRs —
   not forks" (`PRD.md:444`). A fork PR withholds secrets and issues a
   read-only token, which silently disables the model call, the comment, and
   ledger persistence all at once — not a partial degradation, a total one,
   because `GITHUB_TOKEN` on a fork PR cannot write a comment either. The
   onboarded repository must be org-owned (or otherwise a same-repo-branch-PR
   setup) with the workflow triggered by plain `pull_request`, never
   `pull_request_target`. The caller template already does this.
2. **The `analyse` / `review` job split is inside the reusable workflow, and
   you do not edit it.** The `analyse` job holds `contents: read` and no
   secrets; it is the only job that executes citizen code (student tests, via
   `pytest --cov`). The `review` job holds the write token and the model key,
   and it never runs anything the citizen wrote. Its Python calls all use
   `python -I`, because `python -m shodann.review` otherwise puts the working
   directory first on `sys.path`, and the ledger steps run with
   `working-directory: citizen`; a citizen who commits a `shodann/` directory
   would have it imported in place of the installed engine. The split in both workflows is asserted by
   `tests/test_workflow_contract.py` and
   `tests/test_reusable_workflow_contract.py`.
3. **The engine must be reachable by the calling repository.** The caller uses
   `norrisaftcc/algorithm-shodann/.github/workflows/shodann-review.yml@<SHA>`,
   and the workflow checks the engine out from the same repository. That works
   while `algorithm-shodann` is public. If it ever goes private, Actions access
   from the subscribing repositories must be granted in its settings first.
4. **Secrets and inputs**, set in the onboarded repository (not inherited from
   `algorithm-shodann` — GitHub secrets do not cross repositories). Model
   settings are **inputs on the caller**, not repository variables, so nothing
   depends on how `vars` resolves in a called workflow. Keys are **secrets**,
   and the caller must pass them explicitly.

   | Name | Kind | Meaning |
   |---|---|---|
   | `SHODANN_LLM_API_KEY` | secret | The primary model key. On the Anthropic wire it is the Anthropic key. Without it `LLMConfig.configured` is false and every review takes the REDUCED ALLOCATION path. |
   | `ANTHROPIC_API_KEY` | secret, optional | Enables the fallback wire when the primary is unreachable (`fallback_from_env`). Keyed on presence alone; do not set it unless the fallback is wanted. |
   | `engine-ref` | input, required | 40-character commit SHA of the engine, and an ancestor of `main`. The caller must keep it equal to the SHA after `@` in `uses:`; the workflow cannot check that. |
   | `llm-wire` | input | `openai` or `anthropic`. Blank means `openai`. Any other value raises `ValueError` naming `SHODANN_LLM_WIRE`. |
   | `llm-model`, `llm-effort`, `llm-max-tokens`, `llm-temperature`, `llm-timeout`, `llm-base-url` | inputs | Primary model. On the Anthropic wire there is no base URL, and temperature is omitted unless set (then sent in `extra_body`; Haiku 5.5 answers a non-default value with a 400). `llm-effort` is `low`, `medium`, `high`, `xhigh` or `max`; blank sends nothing. |
   | `fallback-model`, `fallback-temperature`, `fallback-effort`, `fallback-max-tokens` | inputs | Fallback model. The default fallback model is `DEFAULT_FALLBACK_MODEL`, `claude-haiku-4-5`. No temperature is sent by default for any fallback model. A value set in `fallback-temperature` goes out in the request's `extra_body`, because the current Anthropic SDK has no `temperature` keyword; Haiku 5.5 answers a non-default value with a 400, so leave it blank. Do not set `fallback-effort` while the fallback is Haiku 4.5: it rejects `output_config` (the program drops it for that model, but a blank input is the safe setting). `max_tokens` defaults to 2000 on the Anthropic wire. |
   | `leaderboard` | input, boolean | Default `false`. See "What is still true". |
   | `record-ledger` | input, boolean | Default `true`. Set `false` if the default branch does not allow the Actions token to push. |
   | `python-version` | input | Default `3.12`. |

   Every variable `LLMConfig.from_env` and `fallback_from_env` read is mapped
   in the compose step of both workflows. A contract test derives that list
   from `llm.py`, so a new variable that is not mapped fails CI rather than
   being silently ignored in Actions (the class `EARLY_RUNS.md` 8 recorded).
   No GitHub Models integration — retired 2026-07-30 per `CLAUDE.md`.
5. **`.shodann/clearances.json` must exist in the onboarded repository before
   the first PR**, or every citizen defaults to `DEFAULT_CLEARANCE = 2` (RED)
   — harmless, but worth setting deliberately if the course wants band
   variation from day one. It is a flat, string-or-int map,
   `{"username": "3"}` (`src/shodann/state.py`, `read_clearance`);
   `algorithm-shodann`'s own `.shodann/clearances.json` is a worked example. It
   is the instructor's file to hand-edit — SHODANN never infers a band from
   readings.
6. **`.shodann/citizens/` needs no manual setup.** `save_citizen_history`
   creates it on first write.
7. **The ledger writes only on merge to the default branch, never per push.**
   The condition is `action == 'closed' && merged == true && base.ref ==
   repository.default_branch`, plus `--dry-run` on every other run. A course
   maintainer expecting velocity to move on every pushed commit will be
   surprised; that is intentional, and was learned the hard way — writing state
   per push made SHODANN conflict with its own open PRs. The default branch
   must allow the Actions token to push, or set `record-ledger: false`.
8. **Leaderboard aggregation across repositories is separately blocked.** See
   "What is still true", item 3. Do not scope it as part of onboarding one
   repository.

## Onboarding steps

1. Confirm prerequisites 1 and 3: org-owned repository, branch PRs, plain
   `pull_request`.
2. Choose one full 40-character commit SHA of `norrisaftcc/algorithm-shodann`
   that contains `.github/workflows/shodann-review.yml`. Not a branch, not a
   tag.
3. Copy `templates/subscriber/shodann.yml` to `.github/workflows/shodann.yml`
   in the target repository. Replace **both** all-zero placeholders with that
   SHA: the one after `@` and the one in `engine-ref`. The placeholder is
   deliberately invalid, so an unedited copy fails at checkout.
4. Set the secrets in prerequisite 4 in the target repository's own Settings →
   Secrets and variables → Actions, using a dedicated, spend-limited key.
5. Add `.shodann/clearances.json`, or accept that every citizen starts at RED.
6. Open a same-repo branch pull request and confirm a comment posts within 120
   seconds of the `review` job completing, carrying real velocity figures rather
   than a REDUCED ALLOCATION or MINIMAL RESPONSE notice.
7. Merge that pull request and confirm `.shodann/citizens/<username>.json` was
   created or updated by a commit from `shodann[bot]` on the default branch.
   `METRICS.md` is created only if `leaderboard: true`.

To move to a newer engine, change both SHAs together in one commit. Moving the
engine mid-cohort can move a citizen's baseline; the same freeze that pins
`ruff` and `pytest-cov` applies to the reviewer's own version, and that is why
the engine is pinned at all.

## Verification

- `python scripts/dev.py render` (run from an `algorithm-shodann` checkout)
  renders a review offline and read-only — no model configured, so it takes the
  REDUCED ALLOCATION path and never writes the ledger. It checks
  `algorithm-shodann` itself, not a subscriber's setup.
- The local check for another repository is `python -I -m shodann.review
  --event <path> --out out.md --root <checkout of the other repo> --reports
  <dir> --dry-run`, run from wherever `shodann` is installed *non-editable*
  (`pip install ./engine`). Confirm `out.md` contains real section headers
  (`### 🚀 Shipping Velocity Report`, etc.) and not the four-line MINIMAL
  RESPONSE shape from `emergency_comment`.
- To prove the templates travel with the package, build a wheel, install it in a
  fresh virtual environment outside any checkout, change to an unrelated
  directory, and call `render_prompt`. `tests/test_prompt_packaging.py` covers
  the resolution order; the wheel build is the manual check.
- After a real PR, read the posted comment for internal consistency (two
  sections should not disagree about the same number) — `CLAUDE.md` records this
  as a check that has caught defects tests did not, twice.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Every PR gets the fixed "REDUCED ALLOCATION / Resource Advisory" comment, no velocity ever | The repository copied `shodann.yml` instead of calling the reusable workflow, or the compose step could not start. Open the `review` job log: a failed `pip install` means an unusable `engine-ref`; `::error::engine-ref must be a full 40-character commit SHA` means the placeholder or a branch name is still in the caller. |
| The run fails at checkout of the engine | `engine-ref` is still the all-zero placeholder, or names a commit that is not in `algorithm-shodann`. |
| `::error::engine-ref ... is not an ancestor of main` | The SHA is real but was never merged to `main` (an open pull request's commit, or a fork's). Pin a merged commit, and set the `@` ref in `uses:` to the same one. |
| The reviewed code and the engine disagree after an update | The `uses:` ref and `engine-ref` were edited separately. The workflow cannot see the first, so only a person comparing the two can catch it. |
| Every PR gets a four-line "MINIMAL RESPONSE" comment with `Clearance: PENDING`, no metrics | `render_prompt` raised. In a reusable-workflow run that means the installed engine cannot find its prompt templates, so the package was built without `shodann._prompts`. Check the pinned commit's `pyproject.toml`. |
| The comment posts, but the model never answers (facts only) | `SHODANN_LLM_API_KEY` is not passed through `secrets:` in the caller, or `llm-wire`, `llm-model` are blank. On the Anthropic wire a key and a model are both required. |
| A review degrades after the model is changed | A model that rejects a non-default sampling parameter will fail every call. Leave `llm-temperature` blank on the Anthropic wire. If the fallback model rejects a value, check `fallback-temperature`. |
| Actions run is red even though a comment posted | Expected when the compose step exits 3 (`EXIT_DEGRADED`): the comment is written and posted, then the job is made red on purpose. Check whether the comment carries real metrics before treating the red run as the primary symptom. |
| Ledger never updates even after a clean merge | Confirm the merge landed on `github.event.repository.default_branch`, that `record-ledger` is `true`, and that branch protection lets the Actions token push. A lost push race or a rebase conflict is a `::warning::`, not a failure. |
| `gh pr comment` fails with "not a git repository" | A step on this path lost `GH_REPO`. The reusable workflow sets it on both `gh` steps because the workspace root is not a repository (the citizen is in `citizen/`). |
| `METRICS.md` is not created | Correct: `leaderboard` defaults to `false`. |
| Every citizen shows RED regardless of ability | `.shodann/clearances.json` is missing or the username key does not match the GitHub login exactly — `read_clearance` returns `None` on any parse failure and the caller then uses `DEFAULT_CLEARANCE`. |
| A citizen who opted out still appears named on the leaderboard, or vice versa | Check `display.visibility` in that citizen's own ledger file — new records default to `anonymous` (changed 2026-07-29), but records that predate the change round-trip whatever they already had. |

## Explicitly out of scope for "onboarding one repository"

- RAGE STATE's label trigger, TA dispatch UI, and graduated debt escalation —
  deferred to v1.1 regardless of topology (`PRD.md` §7, `CLAUDE.md`'s RAGE
  STATE section).
- Cross-repository leaderboard aggregation (`PRD.md:446`).
- Any change to the frozen toolchain (`ruff==0.16.0`, `pytest-cov==7.1.0`) —
  onboarding a repository must not become an occasion to also bump a
  score-feeding tool version; that is a separate, cohort-boundary decision per
  `CLAUDE.md`'s toolchain-freeze section.
- Converting `shodann.yml` (self-review) into a caller of the reusable workflow.

---

## History: why onboarding was blocked (superseded)

> **Everything below is the account written before the fix, kept so the reasoning
> is not re-derived.** It describes the repository as it stood on `main` at
> `349445d`. Where it says "today", read "then". Its file and line references
> are to that commit and have since moved. Do not follow its recommendations: the
> reusable workflow above replaces its "smallest fix", and in particular its
> item 3 (a `pip install git+https://…` line pasted into a copy of
> `shodann.yml`) is not the supported route.

### The defects as found: not possible (superseded)

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

#### The same defect, in its dangerous direction

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

#### What actually happens if you try it anyway

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

### The smallest fix as first proposed (superseded)

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
