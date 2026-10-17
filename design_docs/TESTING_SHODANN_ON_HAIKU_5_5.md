# Testing SHODANN on Haiku 5.5 and the reusable workflow

This file tells you how to test the Anthropic primary wire and the reusable review
workflow before any student repository subscribes. Do the levels in order. A pass
at one level does not prove the next.

| Level | What it proves | Needs | Cost |
|---|---|---|---|
| 0. Suite and render | The code, the contracts and the offline comment hold | Python 3.11+ | Free |
| 1. Local review | Haiku 5.5 accepts the request and writes a valid review | An Anthropic key | Cents |
| 2. Pilot repository | The reusable workflow runs end to end on GitHub | A throwaway repo, a key | Cents |
| 3. Read the reviews | A beginner can use what SHODANN wrote | Level 2 output | Free |

**Nothing at levels 1 to 3 has run yet.** The pull request that added the wire and
the workflow (#71) was checked by tests, by reading the YAML as text, and by
offline runs against an unreachable endpoint. No review has come from Haiku 5.5,
and no other repository has called `shodann-review.yml`. `EARLY_RUNS.md` records
25 defects that a green suite did not catch. Expect this run to find more.

**Do not subscribe a CTS-285 student repository as part of this test.** That waits
on the course owner's ruling (`SUBSCRIBING_A_CTS285_REPOSITORY.md`). Use a
throwaway repository you own.

Use a key from a dedicated Anthropic Console workspace with a low spend limit.
Anyone with write access to a subscribing repository can read its secrets, so the
key must be one you can afford to revoke.

---

## Level 0: suite and offline render

```bash
python scripts/dev.py all      # pytest and ruff; both must be clean
python scripts/dev.py render   # composes a review offline; calls no model
```

**Pass:** `... passed, 1 skipped` and `All checks passed!`. The one skip is
deliberate (`reduced_allocation`). Any other skip is a failure. The render must
print a comment and must not print a traceback.

One test binds every keyword sent to `messages.create` to the installed
`anthropic` SDK's real signature. If you upgrade the SDK, run level 0 first. That
test is what caught the `temperature` keyword the current SDK no longer accepts.

---

## Level 1: one review from the real model, locally

This runs the same entry point the workflow runs, with a real key. `--dry-run`
keeps it from writing the ledger.

```bash
export SHODANN_LLM_WIRE=anthropic
export SHODANN_LLM_MODEL=claude-haiku-5-5
export SHODANN_LLM_API_KEY=sk-ant-...        # the test workspace key
export SHODANN_LLM_EFFORT=low
export SHODANN_LLM_MAX_TOKENS=2000
.venv/bin/python -I -m shodann.review \
  --event tests/fixtures/sample_event.json --root . \
  --out /tmp/shodann-review.md --dry-run
cat /tmp/shodann-review.md
```

Use `.venv\Scripts\python.exe` on Windows. `dev.py` builds `.venv` the first time
it runs.

**Pass:**

- The comment opens `## 🤖 SHODANN Analysis Complete` and carries the standard
  headings in order (`CLAUDE.md`, **Output contract and voice**).
- No `::warning::SHODANN degraded` line in the terminal.
- The comment is under 400 words, and it uses none of the words on the "Never"
  list.
- Two sections do not disagree about the same number.

**Fail, and what it means:**

| You see | Meaning |
|---|---|
| `MINIMAL RESPONSE` and "unreachable: Error code: 400" | Haiku 5.5 rejected a request field. The warning names it. Record it in `EARLY_RUNS.md`. |
| "unreachable: Error code: 401" | The key is wrong, or it is in the wrong variable |
| "hit max_tokens (2000) before finishing" | Thinking used the ceiling. Raise `SHODANN_LLM_MAX_TOKENS` or keep `effort` at `low` |
| "installed anthropic SDK rejected the request keywords" | The SDK changed its signature. Run level 0 |
| `REDUCED ALLOCATION` | No model was configured. Check the five variables |

**Fallback check.** Repeat with `SHODANN_LLM_MODEL=claude-haiku-5-5-nonexistent`
and `ANTHROPIC_API_KEY` set to the same key. The primary must fail, and the review
must still arrive from the fallback (`claude-haiku-4-5`). Then unset both.

In the Console, confirm the usage appears on the test workspace only.

---

## Level 2: a pilot repository on GitHub

### Set it up

1. **Create a throwaway repository** under the organisation that will own the
   student repositories. Give it a small Python package with a few `pytest` tests,
   so the analyse job has something to measure.
2. **Copy the caller.** Copy `templates/subscriber/shodann.yml` to
   `.github/workflows/shodann.yml` in the pilot repository.
3. **Pin it.** Replace **both** all-zero SHAs with the same full commit of this
   repository's `main`. `cb45ecda9e14b30608912eb73005860841b29d4f` (the merge of
   #71) is the first commit that has the reusable workflow. A later `main` commit
   is also fine. The workflow refuses a branch, a tag, or a commit that is not on
   `main`. It cannot check that the two values match, so check that yourself.
4. **Add the secrets** (Settings, Secrets and variables, Actions):
   `SHODANN_LLM_API_KEY` for the test workspace key. Add `ANTHROPIC_API_KEY` too,
   if you want to test the fallback.
5. **Add `.shodann/clearances.json`** with your GitHub login, for example
   `{"your-login": "2"}`.
6. **Let the Actions token push to the default branch,** or set
   `record-ledger: false` in the caller.

### Run the pilot

Follow the eight steps in `SUBSCRIBING_A_CTS285_REPOSITORY.md`, **Pilot test
plan**. In short:

| # | Do | Pass if |
|---|---|---|
| 1 | Open a branch PR that changes one `.py` file and one doc | A standard review appears within about two minutes, with real figures |
| 2 | Read the run log | The compose step shows no request error and no `degraded` warning |
| 3 | Merge it | A `shodann[bot]` commit adds `.shodann/citizens/<login>.json`; no `METRICS.md` appears |
| 4 | Open a PR that changes only Markdown or config | The config-only handler fires, with its own headings |
| 5 | Open a PR with a syntax error | The syntax-barrier handler fires |
| 6 | Push twice quickly to one branch | The older run is cancelled; one review stands |
| 7 | Search the run logs for the key | It appears nowhere; Console usage is on the test workspace only |
| 8 | Optional: open a PR from a fork | No review. This is the topology working as designed |

Then check the two guards that #71 added:

- **Engine provenance.** Change `engine-ref` to a commit that is not on `main`,
  for example a commit on an unmerged branch. The review job must stop at "Refuse an
  engine commit that is not on main". Change it back.
- **Token scope.** Delete the `permissions:` block from the caller. The review must
  still post, and the job's token must carry only `contents: write` and
  `pull-requests: write` (shown at the top of the job log). Put the block back.

Three behaviours were never seen on GitHub. Watch for them:

- The called workflow reads the caller's `pull_request` event.
- The cross-repository checkout of this repository works with the default token.
- `cancel-in-progress` together with `if: always()` may post a stale comment from
  a cancelled run.

---

## Level 3: read the reviews as a beginner

A review that passes every check can still be useless to the student it was
written for. For each review from level 2:

- Read it without opening the code. Could a first-semester student say what to do
  next?
- Check that every number in the comment appears in the run's analysis output.
  SHODANN may reframe a figure, never invent one.
- Check that the "Recommended Iteration" is one action of under 30 minutes.

The `citizen-zero` agent in this repository does this reading and reports what a
beginner would understand and believe. Its testimony is evidence, not a verdict.

---

## Record the results

`design_docs/EARLY_RUNS.md` is where a defect found by running the system goes.
Each of its entries says what was run, what the output was, why the suite missed
it, and the probe that now catches it. Add an entry for every failure at levels 1
to 3, even one you fixed at once.

If a run settles a fact this repository states as unverified, correct the
statement in the same change. The facts are: the Haiku 5.5 behaviour in `llm.py`'s
docstrings, the three unobserved GitHub behaviours above, and the cost figures in
`SUBSCRIBING_A_CTS285_REPOSITORY.md`.

To stop the pilot, delete the caller file or disable the workflow, and revoke the
key. Revoking the key alone does not stop the bot. It degrades every review to the
facts-only notice.
