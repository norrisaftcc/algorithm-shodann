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

## 6. "from 0% to 218 complexity" — the prompt's defect, not the model's

**Where:** a controlled trial, same prompt and context through `llama3.2:3b` and `llama3.1:8b`, run three times as the fix was corrected.

**The question:** entry 2 left it open whether the fabrication was a size problem or a structural one.

**Round one — coverage sent as `0.0`.** Both models celebrated it. The 8B: *"a coverage delta of 0.0% to 0.0%!"* The 3B invented `df` and `dataFrame` as variable names it had never seen. Both were behaving correctly given what they were told: the prompt handed over a coverage reading of zero, a delta of zero, and an instruction to celebrate deltas. **A zero handed to a model is a measurement, and it will be read as one.**

**Round two — cells filled with the words `not instrumented`.** The 8B stopped celebrating and correctly recommended *"instrumenting their test coverage to accurately measure progress"* — but narrated *"improving their test coverage from not instrumented to not instrumented"*. A table row with Previous and Current columns implies a progression whatever you put in it. The 3B got worse: *"a delta of 217 points"*, plus five invented identifiers.

**Round three — the rows dropped entirely**, replaced by a plain statement that no coverage tool ran and no figure exists. The 8B: clean. Zero contract violations, zero invented tokens, and a grounded suggestion to add automated testing. **A row that is not there cannot be narrated.**

**What the 3B did in round three, and why it is the important half:** it passed every structural check — zero violations, would have posted as-is — while claiming the citizen had *"rapidly improved their test coverage from 0% to 218 complexity"*. It took the complexity figure and called it coverage. It also invented `test_result`, `commit_hash` and `README.md`.

**A contract-clean lie is worse than a contract violation**, because nothing stops it. The validator checks structure, vocabulary and length. It has no view of truth, and cannot acquire one by being made stricter.

**Conclusions, all three worth keeping:**

1. **The absent-versus-zero defect was structural.** No model size fixes it, and the fix is in the prompt: do not send an unmeasured quantity as a number.
2. **Local inference is viable at 8B and not at 3B.** The floor is not contract compliance — the 3B clears that — it is the ability to track which number means what. That is the honest answer to "can this run on a laptop with no key in a safe": yes, at about eight billion parameters.
3. **A groundedness probe is cheap and the validator should probably have one.** The trial harness flagged every fabrication automatically by extracting backticked tokens from the response and checking whether they appear anywhere in the prompt. Three lines of regex caught what a purpose-built validator could not.

**Guarded by:** `test_uninstrumented_coverage_says_so_rather_than_reporting_zero` and `test_instrumented_coverage_still_reports_normally`.

---

## 7. SHODANN blocked its own pull requests

**Where:** merging four PRs in a row. The first went in; the second and third reported conflicts; the fourth needed three attempts and lost a race twice.

**What conflicted:** exactly one file, every time - `.shodann/citizens/norrisaftcc.json`. SHODANN's own ledger.

**Why:** the review job wrote the ledger to the *pull request branch* on every run. Two open PRs meant two divergent ledgers, and the second merge conflicted by construction. Worse, each push triggered a fresh review, which pushed a fresh ledger commit, which invalidated the merge that was about to happen - a loop that resolves only by winning a race against your own bot.

`PRD.md` section 8 anticipated half of this: *"per-citizen files reduce merge conflicts"*. True across citizens, useless for one citizen with two branches. In a classroom each student has their own repository, so student-versus-student never collides - but any student with two open pull requests hits this on their second merge, and has no idea why.

**The deeper problem the conflict exposed:** a review is not a merge. Recording velocity for work that may never land makes `pr_count` measure pull-request-*opening* rather than shipping, and a citizen who opens and closes five PRs accrues five submissions for nothing.

**What changed:** the review runs on every push and writes no state at all (`--dry-run`). The ledger is written once, on `pull_request: closed` with `merged == true`, against the base branch. Velocity now records what landed.

**What this cost before it was found:** four merges, two conflict resolutions, one lost race, and roughly twenty minutes of a maintainer fighting a bot for control of a JSON file.

---

## 8. The workflow was the one file no test could read

**Where:** the first merge with coverage instrumentation. The ledger recorded `coverage: 0.0` after a run whose analysis job measured 98.6% and uploaded it.

**The wrong diagnosis, and it was mine:** the analysis job was skipped on the `closed` event, so the merge that wrote the ledger had no readings to write. That was true, it was fixed, and the symptom survived it. Asserting a cause and merging a fix is not the same as confirming one.

**The actual cause:** `--reports` was never passed to the CLI. A string replacement in the edit script that added the flag had failed silently, so the workflow uploaded the artifact, downloaded the artifact, and then invoked a review that had no idea it existed. Two green pipelines, correct artifact handoff, readings discarded at the last step.

**The pattern this completes:** the third defect of the same shape, after a `--dry-run` flag added to the wrong entry point and a checkout asking for a branch that merge had deleted. All three were contracts *between the workflow and the program*, and the workflow was the only code in the repository no test could see.

**What changed:** `tests/test_workflow_contract.py` reads the workflow as text and asserts crudely — both invocations pass `--reports`, the review still passes `--dry-run`, `analyse` declares `contents: read` and names no secret, `review` invokes neither `pytest` nor `ruff`, and no citizen-authored field reaches a shell. Those last two were previously guaranteed by a comment explaining the intent. A YAML-aware version would have been more elegant and would have caught none of this: the failure was a missing string in a `run:` block.

---

## 9. The comment contradicted itself about coverage

**Where:** rendering the degraded review by hand, after the ledger finally held a real coverage figure. The tests were green.

**What it said**, in one comment, three sections apart: *"Your previous submission was not measured, so this one starts the comparison"* under Instrument Readings, and *"Coverage jumped 98.6%! Significant testing investment"* under Algorithm-Approved Patterns. Also *"First tests are hardest tests"* — to a citizen who may have had 98.6% coverage all along.

**Why:** `collect_metrics` has to hand the velocity engine a float, so an absent reading arrives as `0.0`. The engine cannot tell that zero from a measured one. The readout had just learned the difference; nothing downstream had. So the display refused to claim a gain while the score, the celebrations, and the opportunities all claimed it loudly.

The same defect ran the other way and was worse: a citizen at 91.2% whose analysis job died scored **−405**, a 182-point punishment for a tool crashing. A punitive branch caused by infrastructure, which the behavioural contract forbids outright.

**What changed:** `reconcile_coverage` holds coverage still unless *both* sides of the comparison were measured, and the ledger gained a `coverage_instrumented` flag so "nobody looked" and "no lines covered" stop sharing a representation. A measured zero is untouched — 0 to 30 is US-1.3's flagship case and must keep scoring as the gain it is.

**How it was found:** by printing all seven branches and reading them. The assertion that would have caught it did not exist, because it never occurred to me that two sections of the same comment could disagree.

---

## 10. The citizen could raise their own velocity

**Where:** a five-agent survey of the repository, 2026-07-28. Neither defect is in any Python file; both are two lines of workflow that no scope had reason to read together.

**What was wrong:** the analysis job ran `pytest --cov=.` with no coverage configuration, so the *citizen's own test files* entered the coverage denominator. Test modules execute end to end, so they join the average at roughly 100%. Coverage is the 2.0-weighted term, the largest in the score. **A student raised their velocity by adding a test file that asserts nothing.**

The same job ran `ruff check .` without `--isolated`, so ruff resolved configuration from the repository being analysed. The lint delta feeds the score through the `sqrt` term, which makes rule selection a score input rather than a style preference — and made lint counts incomparable between citizens.

**Why it matters more than it reads:** this is the lines-of-code metric wearing a different unit. Measure LOC, get verbose code. Measure coverage without scoping it, get empty test files. A *rate* metric is easier to game than a position metric, because a citizen only has to move, not to be good — holding 90% honestly is work, adding one assertion-free file is thirty seconds.

**The clock:** `PRD.md` §8 freezes the measurement set for cohort 1, because changing a measurement resets every baseline. Both were **free to fix that day and impossible a month later** — after the first real submission, correcting them means invalidating every student's history.

**What changed:** `--cov=src` with a fallback for flat layouts, `ruff check --isolated`, and both asserted in `tests/test_workflow_contract.py`. The coverage test failed on its first run against the comment explaining why `--cov=.` is wrong — correct behaviour from a crude string check, and the reason the assertion now reads only executable lines.

---

## 11. Two documents buried the sentence that protects a student in distress

**Where:** eight blind readers ran an external floor test — ASSAY, from the vendored `the-algorithm` skill — against one document each. None knew what SHODANN is or that the others existed.

**What they found**, independently, in the two documents that carry the rule:

- `SHODANN_CLAUDE.md` — *"It's okay to break character"*, sentence **115 of 165**, in a **subordinate clause**.
- `SHODANN_VOICE_GUIDE.md` — *"The satire serves learning. When it doesn't, set it aside."*, sentence **157 of 160**.

That rule governs student distress, academic-integrity concerns, and accessibility accommodation. It is the highest-consequence sentence in the corpus, and both documents that carry it place it last and place it down. A model assembling a prompt reads roughly 150 lines of persona enthusiasm before reaching the clause that says stop performing.

**The control that makes this trustworthy:** `README.md` was included deliberately as in-persona satire with no product content. It returned below floor at 2 of 7 sentences. Had it come back clean, every other result would have been void.

**The finding nobody predicted:** we agreed in advance to discount `SHODANN_VOICE_GUIDE.md` as a false positive, on the grounds that a document prescribing smoothness will read as smooth. **It came back above floor** — the instrument did not confuse deliberate persona with manufactured agreeableness. What it found instead was that 18 of 190 sentences carry load, the lowest ratio in the corpus: the document expands where it is fun and stays thin where it constrains.

**And on `PRD.md`**, a reader given no dates flagged `smoothness-confined-to-a-graft`: sections 1–7 contain no sentence anyone could object to, while the §8 block added eighteen months later holds *"the only sentences with cost."* It located the seam between the generated document and the argued one without being told either existed.

**Status: unfixed.** Recorded because ASSAY never redrafts — acting on it is separate work.

---

## What the pattern says

Every defect on this page needed the system to *run*. None was found by reading code, and the test suite was green through all of them — 136 passing tests while SHODANN told a citizen they had written twice as many tests as they had; 243 while it told one their coverage jumped 98.6 points and, in the same comment, that there was nothing to compare against.

Two of them were found by *rendering the output and reading it*, which is neither testing nor code review and appears in no methodology. It is the only technique on this page that caught a comment disagreeing with itself.

The last two needed a different move again: **reading with something withheld.** Entry 10 came from five surveyors who each saw one scope and could not see the others, plus a critic asked only what falls between them. Entry 11 came from readers who were given a document and denied any knowledge of what it was for. Every technique on this page works by removing context from the reader — running the system removes the author's knowledge of what it *should* do, and a blind read removes the reader's ability to supply what the document failed to say. A reviewer who knows the intent will unconsciously fill the gap and report that there wasn't one.

The two agents caught different things and neither caught these: `oracle-warden` verifies what is checkable mechanically, `clive-prompt-warden` verifies what is consistent across documents. Neither can see what only appears when a real event payload meets a real runner.

Which is the argument for rung 1 existing at all. The walking skeleton was not a way to build the system faster. It was the only way to find out what the system does.
