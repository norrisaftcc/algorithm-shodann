# Subscribing a repository to SHODANN

Use this if you want SHODANN to review pull requests in a repository other than
`algorithm-shodann`.

## Short version

A second repository subscribes by **calling** SHODANN's reusable workflow, not
by copying SHODANN's own workflow. The caller is one short file,
`templates/subscriber/shodann.yml`. It pins the workflow and the engine it
installs to a single commit SHA of `algorithm-shodann`, and the reusable
workflow installs only that engine. Nothing installs the repository under
review.

Do not copy `.github/workflows/shodann.yml`. It is the self-review workflow, and
its `review` job runs `pip install .`, which in any other repository installs
the student's package into the job that holds the write token and the model key.

The checklist:

1. Use a repository topology that matches the product decision:
   - org-owned, with same-repo branch PRs (not forks)
   - plain `pull_request`, never `pull_request_target`
2. Copy `templates/subscriber/shodann.yml` to `.github/workflows/shodann.yml` in
   the target repository. Replace **both** all-zero placeholders with one full
   40-character commit SHA of `norrisaftcc/algorithm-shodann` that contains
   `.github/workflows/shodann-review.yml`. A branch or a tag is refused.
3. Add the secrets to the target repository, using a **dedicated Anthropic
   workspace key with a low monthly spend limit**:
   - `SHODANN_LLM_API_KEY` (the primary model key)
   - `ANTHROPIC_API_KEY` (optional; enables the fallback model)

   Model, effort and token settings are **inputs in the caller file**, not
   repository variables.
4. Add `.shodann/clearances.json` before the first PR if you want non-default
   clearance bands from day one.
5. Open a branch PR in the target repository and confirm that the review comment
   contains real sections and metrics rather than a reduced-allocation or minimal
   response notice.

## Know before you subscribe

- **Anyone with write access to the target repository can read its secrets.** A
  `pull_request` run uses the workflow file on the PR's own branch, so a
  collaborator can edit the caller to print a secret. The SHA pin protects the
  engine, not the key. That is why the key must be dedicated and spend-limited.
- **The leaderboard is off by default** (`leaderboard: false`). With it off,
  merges write `.shodann/` only, and `METRICS.md` is not generated. Whether a
  course ranks its students is the course's decision.
- **Cross-repository aggregation is not built.** Each repository keeps its own
  ledger.
- **Turning SHODANN on for a particular course is a separate decision from
  whether it can be done.** For CTS-285, see
  `design_docs/SUBSCRIBING_A_CTS285_REPOSITORY.md`.

## What can go wrong

The most common failure modes are:

- the caller still carries the all-zero placeholder SHA, so the run fails at
  checkout (deliberate)
- the secrets were set in the repository but not passed through `secrets:` in
  the caller
- the review comment posts, but the run exits red because the compose step
  degraded (exit 3 is written, posted, then surfaced on purpose)
- the citizen ledger never updates because the merge was not to the default
  branch, `record-ledger` is `false`, or branch protection refuses the push
- the repository starts with the default RED clearance because
  `.shodann/clearances.json` is missing or misnamed

## Testing suggestions

A lightweight test plan is enough to catch the common subscription problems before
any course-wide rollout:

1. Use a small, controlled pull request that changes one Python file and one docs
   file. That gives you a normal review path without a huge diff.
2. Confirm that the posted comment contains the normal SHODANN structure (for
   example, a velocity report and growth opportunities) rather than the reduced
   allocation or minimal response fallbacks.
3. Merge the PR and confirm that the repository's `.shodann/citizens/` state
   updates on the target repository's default branch. `METRICS.md` should *not*
   appear unless you turned `leaderboard` on.
4. Repeat once with a docs-only PR and once with a syntax-breaking PR to make
   sure the edge-case handlers are reachable and that the interface stays clear.

## Interface adjustments worth considering

If the maintainer wants the experience to feel more approachable, a few
adjustments would help:

- Make the first line of the comment explicitly distinguish between a full review,
  a reduced review, and a setup failure so the maintainer does not need to read
  the whole thread to understand what happened.
- Keep the standard headings, but consider shortening the first section for
  setup-related failures so the comment is easier to scan.
- If a subscription issue is detected, surface a separate, plain-language note in
  the workflow logs or PR comment that says what is missing (for example, the
  engine pin or the required secrets).

## Where to read more

- `design_docs/ONBOARDING_A_REPOSITORY.md` — the detailed, technical version of
  the same plan: prerequisites, inputs, steps, and the history of the blockers
  that were fixed.
- `design_docs/SHODANN_SUBSCRIPTION_TROUBLESHOOTING.md` — a shorter list of
  symptoms and likely causes.
- `design_docs/SUBSCRIBING_A_CTS285_REPOSITORY.md` — the CTS-285 profile and the
  governance gate.
