# Subscribing a repository to SHODANN

Use this if you want SHODANN to review pull requests in a repository other than
`algorithm-shodann`.

## Short version

SHODANN is not yet a drop-in, one-click integration for a second repository.
The current blocker is packaging: the prompt templates live in this repository's
`prompts/` directory, and the review path still resolves them from the checkout's
working directory. That means a copied workflow can look plausible while still
posting empty or degraded comments.

If you are planning the integration anyway, the practical checklist is:

1. Use a repository topology that matches the product decision:
   - org-owned or otherwise same-repo-branch PRs
   - plain `pull_request`, not `pull_request_target`
   - the `analyse` / `review` split intact
2. Copy `.github/workflows/shodann.yml` into the target repository, but install
   SHODANN from its own pinned source rather than `pip install --quiet .`.
3. Add the required secrets and variables in the target repository:
   - `secrets.SHODANN_LLM_API_KEY`
   - `vars.SHODANN_LLM_BASE_URL`
   - `vars.SHODANN_LLM_MODEL`
   - `secrets.ANTHROPIC_API_KEY` (optional fallback)
   - `vars.SHODANN_FALLBACK_MODEL` (optional)
4. Add `.shodann/clearances.json` before the first PR if you want non-default
   clearance bands from day one.
5. Open a branch PR in the target repository and confirm that the review comment
   contains real sections and metrics rather than a reduced-allocation or minimal
   response notice.

## What can go wrong

The most common failure modes are:

- the workflow installs the target repository as though it were SHODANN itself
- the review job cannot find SHODANN's prompt templates and falls back to a
  minimal response
- the review comment posts, but the run still exits in a degraded state
- the citizen ledger never updates because the merge path is not reached
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
3. Merge the PR and confirm that the repository's `.shodann/citizens/` state and
   `METRICS.md` update on the target repository's default branch.
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
  install step, the prompt package, or the required secrets).

## Where to read more

- `design_docs/ONBOARDING_A_REPOSITORY.md` — the detailed, technical version of
  the same plan, including the current blocker and the exact prerequisites.
- `design_docs/SHODANN_SUBSCRIPTION_TROUBLESHOOTING.md` — a shorter list of
  symptoms and likely causes.
