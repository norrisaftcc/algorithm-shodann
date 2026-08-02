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

## Where to read more

- `design_docs/ONBOARDING_A_REPOSITORY.md` — the detailed, technical version of
  the same plan, including the current blocker and the exact prerequisites.
- `design_docs/SHODANN_SUBSCRIPTION_TROUBLESHOOTING.md` — a shorter list of
  symptoms and likely causes.
