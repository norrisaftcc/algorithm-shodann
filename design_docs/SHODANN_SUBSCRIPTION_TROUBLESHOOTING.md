# SHODANN subscription troubleshooting

This is a quick reference for the common problems that show up when a second
repository tries to subscribe to SHODANN.

## Symptom guide

| Symptom | Likely cause | What to check |
|---|---|---|
| Every PR gets the fixed "REDUCED ALLOCATION" comment | The workflow is installing the target repository as the package instead of SHODANN's own source | Confirm the install step points at SHODANN's pinned source, not `.` |
| Every PR gets a four-line "MINIMAL RESPONSE" comment | SHODANN cannot find its prompt templates in the runtime environment | Check the packaging fix and the install step together |
| The comment posts, but the workflow run is red | The review path degraded before it reached the normal success path | Read the comment content before treating the red run as the primary issue |
| The review looks plausible, but the citizen ledger never updates | The merge path did not complete, or the review never reached the state-writing branch | Confirm the merge was on the default branch and the workflow reached the state-writing step |
| Every citizen appears RED | `.shodann/clearances.json` is missing or the username key does not match the GitHub login exactly | Check the file contents and the exact login string |
| The repository has a `prompts/` directory of its own and SHODANN seems to read that instead | The runtime is resolving templates from the checkout's working directory | Treat this as a packaging problem, not a repository-configuration problem |

## What to do first

1. Read `design_docs/ONBOARDING_A_REPOSITORY.md` for the technical explanation.
2. Confirm the target repository is using same-repo branch PRs and is not a fork.
3. Confirm the install step installs SHODANN from its own pinned source.
4. Confirm the required secrets and variables exist in the target repository, not
   inherited from `algorithm-shodann`.
5. Open a test PR and inspect the posted comment before assuming the workflow is
   healthy.
