# SHODANN subscription troubleshooting

This is a quick reference for the common problems that show up when a second
repository subscribes to SHODANN through the reusable workflow
(`.github/workflows/shodann-review.yml`, called from
`templates/subscriber/shodann.yml`).

## Symptom guide

| Symptom | Likely cause | What to check |
|---|---|---|
| The run fails at checkout of the engine, or logs `engine-ref must be a full 40-character commit SHA` | The caller still has the all-zero placeholder, or `engine-ref` is a branch or tag | Both SHAs in the caller must be the same full 40-character commit |
| Every PR gets the fixed "REDUCED ALLOCATION" comment | The workflow was copied from `shodann.yml` instead of calling the reusable one, or the compose step could not start | Open the `review` job log; confirm the caller uses `uses: …/shodann-review.yml@<SHA>` |
| A real review posts, but with no model prose (facts only) | The model key or model name did not reach the compose step | Confirm `SHODANN_LLM_API_KEY` is passed under `secrets:` in the caller, and `llm-wire` and `llm-model` are set. The Anthropic wire needs both a key and a model |
| Every PR gets a four-line "MINIMAL RESPONSE" comment | `render_prompt` raised: the installed engine cannot find its templates | The pinned commit's package must include `shodann._prompts` (see `pyproject.toml`) |
| The comment posts, but the workflow run is red | The compose step exited 3 (`EXIT_DEGRADED`); the comment is posted first, then the job is made red on purpose | Read the comment content before treating the red run as the primary issue |
| The review looks plausible, but the citizen ledger never updates | Not a merge to the default branch, `record-ledger: false`, or branch protection refuses the Actions push | Confirm the merge base is `github.event.repository.default_branch`; a lost push race is a `::warning::`, not a failure |
| `METRICS.md` is never created | `leaderboard` is `false`, which is the default | Intended. Turning it on is the course owner's decision |
| Every citizen appears RED | `.shodann/clearances.json` is missing or the username key does not match the GitHub login exactly | Check the file contents and the exact login string |

## What to do first

1. Read `design_docs/ONBOARDING_A_REPOSITORY.md` for the technical explanation.
2. Confirm the target repository is using same-repo branch PRs and is not a fork.
3. Confirm the caller pins the workflow and `engine-ref` to the same full
   commit SHA.
4. Confirm the required secrets exist in the target repository, not inherited
   from `algorithm-shodann`, and that the caller passes them through `secrets:`.
5. Open a test PR and inspect the posted comment before assuming the workflow is
   healthy.
