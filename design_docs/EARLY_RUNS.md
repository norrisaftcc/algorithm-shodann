# Early Runs: What SHODANN Actually Said

> A field record of the system's first live outputs, kept deliberately.
> Started 2026-07-25, the day rung 1 shipped.

Every entry here is a real thing SHODANN said to a real citizen, followed by why it said it and what changed. Nothing is reconstructed or cleaned up.

Three reasons this file exists:

1. **It is teaching material.** A course that tells students their work improves through iteration should be able to show its own instrument being wrong and getting better. This is the course's own velocity, in prose.
2. **It is a regression corpus.** Every entry names the test that now guards it. A bug with a story attached is much harder to reintroduce than a bug with only an assertion.
3. **Calibration is invisible in hindsight.** Once a system works, the reasons for its guards look like paranoia. This is the record of which ones were paid for.

---

## 1. "106 new test(s) added" — the spurious baseline

**Where:** PR #35, the first review SHODANN ever posted. 21 seconds, `pull_request` synchronize.

**What it said:**

> 🚀 EXCEPTIONAL GROWTH DETECTED - The Algorithm is deeply pleased.
> - 106 new test(s) added. The Algorithm approves.
>
> **Velocity**: 401.28

**What was true:** the tree held 53 test functions and 2,783 lines of Python. The recorded reading was 106 and 5,419 — almost exactly double.

**Why:** the workflow runs `pip install .` before it reviews, which leaves a copy of every module under `build/lib/shodann/`. `collect_metrics` walked it and counted the whole codebase twice.

**Why it mattered more than a wrong number:** that reading became the first citizen's baseline. The *next* honest submission would have read as a large regression — a negative velocity earned by nothing the citizen did. For a system whose entire premise is the derivative of a metric, a corrupted baseline is worse than no baseline.

**What changed:** `collect_metrics` excludes `build/`, `dist/`, `*.egg-info`, `site-packages`. The spurious record was **deleted rather than corrected** — editing metrics in a ledger to what they should have been is precisely the move `oracle-warden` calls the most damaging edit available in this repository.

**Guarded by:** `test_build_artifacts_are_not_counted_twice`.

---

## 2. "a whopping 0.0%" — what a 3B model invents

**Where:** a local Ollama trial, `llama3.2:3b`, Q4_K_M, on the maintainer's laptop. 202 words in 9 seconds.

**What it said:**

> The Algorithm is thrilled to see @norrisaftcc's coverage jump from 0% to a whopping 0.0%!
>
> - @norrisaftcc has demonstrated excellent use of file names to clearly convey purpose.
>
> **Suboptimal variable naming**: The citizen could benefit from using more descriptive variable names. For example, instead of `x`, consider `user_age`.

**What was true:** it had never been shown any file names, any variable named `x`, or any code at all beyond the metrics in its prompt.

**What it got right, and this is the important half:** the structure was near-perfect. All four required sections, correct order, header line intact, under the word cap, growth-positive framing, and it correctly reached for the mandated vocabulary — "Suboptimal" is the required substitution for a word it was told never to use.

**What this proves:** a small local model can hold the *shape* of the contract cheaply and fast. It cannot be trusted with the *content*. The validator caught two advisory violations and nothing else — correctly, because it checks the contract, not the truth.

**A response can honour every rule and still be entirely invented.** That is the strongest argument in this repository for the hard/soft split: facts come from tools, the model reframes them, and the model's job stays narrow enough that fabrication has nowhere to enter.

**What changed:** nothing in the code. This is a standing finding about model tier, kept because it is the evidence behind a design decision that would otherwise look like superstition.

---

## 3. "Consider adding one test this iteration" — to a citizen with 110 tests

**Where:** every review SHODANN posted, from the first one onward.

**What it said:**

> **Growth Opportunities**
> - First test = first step to confidence. Consider adding one test this iteration.

**What was true:** the citizen had 110 test functions.

**Why:** the suggestion keyed on `current.coverage == 0`. Rung 1 instruments no coverage, so every reading is `0.0` — and a zero coverage reading means one of two very different things. Nobody wrote a test, or nobody measured. The engine could not tell them apart.

**Why it mattered:** telling someone who has written a hundred tests to write their first is not merely inaccurate. It signals that the system is not actually reading their work, which is corrosive to every other thing it says.

**What changed:** the suggestion keys on `test_count == 0`, which is what it always meant. Modelling *absent* versus *zero* properly across the whole metric set is a schema change, and waits for the analysis job that will populate coverage.

**Guarded by:** `test_a_citizen_with_tests_is_not_told_to_write_their_first`.

---

## 4. Two sections that were a student's own code

**Where:** the same Ollama trial, in the validator rather than the model.

**What happened:** the model illustrated a naming fix with a fenced example containing `# Before` and `# After`. The validator reported two unexpected sections.

**Why:** a Python comment is a markdown heading to a regex. Heading extraction ran over the raw text, fences and all.

**Why it mattered:** the validator invented a structural violation out of a student's own code — and every code example a student is shown carries comments.

**What changed:** headings are extracted after fences are stripped.

**Guarded by:** `test_comments_in_a_code_fence_are_not_sections`.

---

## 5. The bot pushed a merge commit to a citizen's branch

**Where:** PR #38, visible only because a force-push was refused as stale.

**What happened:** the branch acquired a commit reading *"Merge 0b4a5d6 into 5e730d3"*, authored by the workflow, on top of the citizen's own commit.

**Why:** `actions/checkout` on `pull_request` checks out the *merge ref* by default — a synthetic merge of head into base, with HEAD detached at a commit that exists on no branch. The persistence step then ran `git push origin HEAD:$GITHUB_HEAD_REF` and pushed that synthetic merge onto the citizen's branch. Every run.

**Why it mattered:** SHODANN rewriting the shape of a citizen's branch is well outside what it is allowed to do. A student would have found merge commits they did not make, attributed to a bot, in their own history — in the record that *is* their competency evidence at INFRARED and RED.

**What changed:** checkout takes `ref: github.event.pull_request.head.ref`, so HEAD is a real branch tip and the push carries only the ledger commit.

---

## What the pattern says

Every defect on this page needed the system to *run*. None was found by reading code, and the test suite was green through all of them — 136 passing tests while SHODANN told a citizen they had written twice as many tests as they had.

The two agents caught different things and neither caught these: `oracle-warden` verifies what is checkable mechanically, `clive-prompt-warden` verifies what is consistent across documents. Neither can see what only appears when a real event payload meets a real runner.

Which is the argument for rung 1 existing at all. The walking skeleton was not a way to build the system faster. It was the only way to find out what the system does.
