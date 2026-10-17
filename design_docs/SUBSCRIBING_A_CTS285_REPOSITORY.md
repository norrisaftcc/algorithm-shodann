# Subscribing a CTS-285 repository to SHODANN

**Status: runbook for a decision that has not been made.** This file records how
a CTS-285 student repository would subscribe, so the work is ready the day the
course owner says yes. It enables nothing.

> ## Do not enable yet
>
> **Nobody should copy the subscriber template into a CTS-285 repository until
> the course's instructional lead has ruled on three questions.** The engine,
> the reusable workflow and the template are built and tested. Turning them on
> for students is a different kind of decision, and it belongs to the person who
> owns the course, not to the person who owns this tool.
>
> CTS-285 has its own rules about material it puts in front of students. Three
> of them touch what SHODANN does:
>
> 1. **In-character material delivered online.** SHODANN's comments are written
>    in a satirical corporate persona. The course rules on in-character online
>    material require an exit for the student, and a pull-request comment has no
>    exit built into it today.
> 2. **Leaderboards.** The course refuses rankings. The template ships with
>    `leaderboard: false`, so no `METRICS.md` is written. The ledger still holds
>    each student's own velocity history (see "What the ledger records" below).
> 3. **Streaks.** The ledger carries an `iteration_streak` counter and feeds it
>    to the prompt. The course refuses streak mechanics. Whether a counter that
>    the student never sees on a leaderboard still counts as one is a ruling, and
>    this file does not make it.
>
> **Open question Q1 (owner: the course's instructional lead):** may SHODANN
> review CTS-285 student pull requests at all, and if so under which of the
> three rules above? Until Q1 has a dated answer, the correct number of CTS-285
> repositories subscribed is zero. A pilot on a throwaway repository that holds
> no student work is not a CTS-285 enablement and does not need this ruling.
> Say which one it is in the PR that sets it up.

## What this file is, and is not

It is the checklist for one subscription: prerequisites, the recommended model
profile, what it costs, and a pilot test plan. It is the CTS-285 specific layer
over three general documents, and it does not repeat them:

- `design_docs/SUBSCRIBING_TO_SHODANN.md` is the general checklist and the
  general test plan.
- `design_docs/ONBOARDING_A_REPOSITORY.md` is the technical account of why the
  old copy-the-workflow route failed and what replaced it.
- `design_docs/SHODANN_SUBSCRIPTION_TROUBLESHOOTING.md` is the symptom table.

It is not an approval, a course-governance document, or a statement about what
CTS-285 allows. It holds no CTS-285 rule of its own. The three rules above are
named so a reader knows what to ask, and the answer lives with the course.

## How a subscription works now

A subscribing repository does not copy the review logic. It copies one small
caller, `templates/subscriber/shodann.yml`, which does two things:

- `uses: norrisaftcc/algorithm-shodann/.github/workflows/shodann-review.yml@<SHA>`
  runs the review workflow from this repository at one pinned commit.
- `engine-ref: '<SHA>'` tells that workflow which commit of this repository to
  install as the engine, with `pip install ./engine`. The prompt templates ship
  inside that package, so nothing is read from the student's checkout.

**The two SHAs must be the same 40-character commit, and keeping them equal is
your job, not the workflow's.** A called workflow cannot see the ref it was
called at: `github.workflow_ref` and `github.workflow_sha` name the caller's own
file, and the called workflow's SHA exists only as a claim in an OIDC token that
the `review` job must not be given. What the workflow does enforce on
`engine-ref` is two things. It refuses anything that is not a full 40-character
commit, a branch or a tag included, because those move under every subscriber at
once. And it refuses a commit that is not an ancestor of `main` in
`norrisaftcc/algorithm-shodann`, so a SHA from a fork or an unmerged branch
cannot be installed beside the write token and the model key. The template ships
with all zeros, which is deliberately invalid: an unedited copy fails at
checkout instead of reviewing with something nobody chose.

The `analyse` job runs the student's tests with no secrets. The `review` job
holds the write token and the model key, installs only the pinned engine, and
never runs a line the student wrote. Do not weaken either property while
adapting the template. `tests/test_reusable_workflow_contract.py` checks both.

## Prerequisites

All four must hold before the first pull request. If any one fails, stop. A
missing prerequisite does not produce a clear error. It produces a plausible
comment with no content, or no comment at all.

### 1. Org-owned student repositories, with branch pull requests

Each student repository must be owned by an organisation the instructor
administers, and students must open pull requests from branches of that same
repository.

- **Not forks.** A pull request from a fork gets no secrets and a read-only
  token. The model call, the comment and the ledger then fail together.
- **Not personal repositories.** An instructor cannot set secrets on a
  repository in a student's personal account.
- The trigger is plain `pull_request`. `pull_request_target` is never needed
  and must not be used.

Whether the CTS-285 student repositories have this shape is not recorded in this
repository. Confirm with the course who owns them before anything else here
matters.

### 2. This repository must be reachable from the student's workflow

The caller uses a workflow in `norrisaftcc/algorithm-shodann`, and the review job
checks out that repository to install the engine. Both work without extra setup
only while `algorithm-shodann` is public. If it is ever made private or
internal, the owner must grant Actions access to the student organisation's
repositories (the repository's Settings, Actions, General, Access setting) or
both the `uses:` line and the engine checkout will fail.

A student organisation that differs from `norrisaftcc` changes nothing here.
Cross-organisation `uses:` of a public repository's workflow is allowed.

### 3. A dedicated Anthropic key, treated as readable by every student

**Any student with write access to their repository can read every secret that
repository holds.** They can edit `.github/workflows/*` on a branch, and a
`pull_request` run executes the branch's version of the workflow with the
repository's secrets. No setting in this repository prevents that. It follows
from the topology above.

So the key must be one you can afford to lose:

- Create a **separate Anthropic workspace** for the course, with its own API key.
  Do not reuse a key that also serves teacherbot, SHODANN's own repository, or
  anything else.
- Set a **low monthly spend limit** on that workspace. The cost section below
  gives a figure far under any sensible limit, so the limit is there for the day
  a key leaks, not for ordinary use.
- Put the key in the student repository as `SHODANN_LLM_API_KEY`. Plan to revoke
  and replace it at the end of the term.
- Leave `ANTHROPIC_API_KEY` unset unless you want the fallback. With the primary
  already on Anthropic, a second key mostly adds a second place for a secret to
  leak. If you do set it, put it in the same workspace so one limit covers both.
  The fallback model is `claude-haiku-4-5` unless the caller's `fallback-model`
  input says otherwise.

### 4. `.shodann/clearances.json`

Add `.shodann/clearances.json` to each repository before the first pull request.
It is a flat map from GitHub login to a clearance number:

```json
{
  "student-login": "2"
}
```

Without the file, or when a login does not match exactly, every student defaults
to RED (level 2). That is harmless but flattens the course's bands. The file is
the instructor's to edit by hand. SHODANN never infers a band from readings.
Clearance numbers run from 1 (INFRARED) upward. See
`design_docs/CLEARANCE_REGISTER.md` for what each band does to the review.

Also confirm the default branch lets the Actions token push, because the ledger
is committed there on merge. If it cannot, set `record-ledger: false` in the
caller. The review still posts. Nothing is recorded.

## The CTS-285 profile

The template ships with this profile. It is the recommendation, not a measured
optimum.

| Input in the caller | Value | Why |
|---|---|---|
| `llm-wire` | `anthropic` | The wire is declared, never guessed from a URL. |
| `llm-model` | `claude-haiku-5-5` | The same model the course tutor is planned to use. |
| `llm-effort` | `low` | A review under 400 words from a fixed prompt does not need more. |
| `llm-max-tokens` | `'2000'` | Room for the output with headroom. The default of 900 is tight. |
| `leaderboard` | `false` | No `METRICS.md`. A ranking is the course's decision, not this template's. |
| `record-ledger` | `true` | The per-student history is what makes velocity possible. See below. |

Temperature is not sent on the Anthropic wire. Haiku 5.5 rejects a non-default
value, and the failure would surface as a degraded comment that names no cause.
No `thinking` parameter is sent either. If you need to override a setting, use
the caller's `llm-temperature`, `llm-timeout` or `fallback-*` inputs. The full
list is in `.github/workflows/shodann-review.yml`.

### What the ledger records

With `record-ledger: true`, a merge to the default branch commits
`.shodann/citizens/<login>.json` to the student's own repository. That file holds
the student's pull-request count, up to ten recent velocity scores, the last
measured metrics that the next review compares against, their `iteration_streak`,
and a `display` block. A new record defaults to anonymous on any leaderboard, and
there is no leaderboard.

`leaderboard: false` stops the ranking. It does not stop the counters. Only
`record-ledger: false` does, and then there is no baseline to measure velocity
against, so every review reads as a first submission. That trade-off is part of
the Q1 ruling on streaks.

## Cost

These figures are an estimate from the prompt size, not a billing record. No
review has been run on this profile, and the per-token prices behind them are an
assumption that this file does not verify.

- The assembled prompt is at most 14 KB, which is about 4.6k input tokens.
- One review costs about **$0.0012**. A review that triggers the validator's one
  retry costs at most about **$0.0025**.
- At 600 reviews a month the total is about **$1.50**.

Check the first month's real usage in the Anthropic Console against these
numbers before trusting them, and set the workspace limit well above them.

## Setting it up

Do these in order, on a repository that is not yet in use by students.

1. Pick the engine commit. Use a commit of `algorithm-shodann` that contains
   `.github/workflows/shodann-review.yml` and the packaged prompt templates.
   Record the full 40-character SHA.
2. Copy `templates/subscriber/shodann.yml` to `.github/workflows/shodann.yml` in
   the target repository.
3. Replace **both** all-zero SHAs with that one SHA. Confirm the two are
   identical.
4. Add the `SHODANN_LLM_API_KEY` secret (Settings, Secrets and variables,
   Actions).
5. Add `.shodann/clearances.json`.
6. Run the pilot below.

To move to a newer engine, change both SHAs together in one pull request. Do not
do it mid-term without a reason: the measurement set is frozen for a cohort, and
the reviewer's own version is part of it.

## Pilot test plan

Run this on one repository before any other. It extends the general plan in
`design_docs/SUBSCRIBING_TO_SHODANN.md`, which still applies.

1. **Normal review.** Open a small branch pull request that changes one Python
   file and one docs file. Within about two minutes the comment should carry the
   standard headings (`### 🚀 Shipping Velocity Report` and the rest) and real
   figures. A comment that says `REDUCED ALLOCATION` or `MINIMAL RESPONSE` is a
   failure. Read it for consistency: two sections must not disagree about the
   same number.
2. **Check the model call.** In the run log, confirm the compose step ran without
   a request error. A 400 from the model degrades to a comment that names no
   cause, so a facts-only comment on this first run is the sign.
3. **Merge it.** Confirm a commit from `shodann[bot]` adds
   `.shodann/citizens/<login>.json` to the default branch, and that **no**
   `METRICS.md` appears.
4. **Config-and-docs-only pull request.** Change only Markdown or config files.
   Confirm the config-only edge-case handler fires and the comment uses its own
   headings. There is no separate docs-only handler.
5. **Syntax-breaking pull request.** Confirm the syntax-barrier handler fires.
6. **Two rapid pushes** to one branch. Confirm the older run is cancelled and only
   one review stands.
7. **Key hygiene.** Confirm the key appears nowhere in the run logs, and that the
   Anthropic Console shows usage on the dedicated workspace only.
8. **Fork check.** If you want to see the failure the topology prevents, open a
   pull request from a fork and confirm it gets no review. Do this only on a
   throwaway repository.

Nothing in this plan has been run against a real subscribing repository. The
workflow was verified by reading it as text and by contract tests, not by
executing it on GitHub.

## If something goes wrong

`design_docs/SHODANN_SUBSCRIPTION_TROUBLESHOOTING.md` has the symptom table. Two
points specific to this setup:

- **Every student shows RED.** The login in `.shodann/clearances.json` must match
  the GitHub login exactly. Check case.
- **To stop the whole thing at once,** delete `.github/workflows/shodann.yml` from
  the repository, or disable the workflow in the Actions tab, and revoke the
  workspace key. Revoking the key alone degrades every review to the facts-only
  notice. It does not silence the bot.

## Not in scope here

- Enabling SHODANN on any CTS-285 repository. That waits on Q1.
- A leaderboard across student repositories. `PRD.md` describes one, and it is
  blocked for a separate reason; see `design_docs/ONBOARDING_A_REPOSITORY.md`.
- Changing the frozen toolchain (`ruff==0.16.0`, `pytest-cov==7.1.0`). Onboarding
  a repository is not an occasion to bump a score-feeding tool.
