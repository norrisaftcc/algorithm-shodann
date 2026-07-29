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

## 12. The citizen could ship us their own coverage figure

**Where:** reading the analysis job while wiring the test tallies into it, 2026-07-29. Then reproduced in a scratch repository before a line was changed, because a plausible exploit and a real one are different claims.

**What was wrong:** nothing deleted the report files before the tools wrote them. `ruff check ... > ruff.json` truncates first, so ruff was safe by accident of shell syntax. Coverage was not. Its step ends in `test -f coverage.json || echo '{}' > coverage.json`, a guard for the case where pytest-cov produced nothing.

So: commit a `coverage.json` claiming 97.4%, then break your own test collection with one bad import. pytest exits on a collection error, pytest-cov writes no report, `|| true` swallows the exit code, the `test -f` guard finds the *committed* file and leaves it alone, and the upload step hands it to the privileged job as a measurement. Coverage is the 2.0-weighted term.

```
$ pytest --cov=src --cov-report=json:coverage.json -q
ERROR test_broken.py - ModuleNotFoundError: No module named 'does_not_exist_anywhere'
$ cat coverage.json
{"totals": {"percent_covered": 97.4}}
```

**Why it kept hiding:** it is the third instance of one rule — *anything feeding the score must not be choosable by the citizen being scored* — and the first two (entry 10) were both about **flags**. This one is about a **file**, so no amount of staring at `--isolated` and `--cov=src` finds it. The guard that made it exploitable was itself defensive: someone thought about pytest-cov failing and handled it, and the handler trusted the working directory.

**What changed:** `rm -f coverage.json ruff.json tests.xml` as its own step before the tools run, with a contract test that asserts both the deletion and its position relative to the invocations. On the freeze clock, like entry 10: free to fix now, impossible after cohort 1's first submission.

---

## 13. The guard that passed with the guard removed

**Where:** the same day, verifying the above by reverting each new guard against the defect it was written for.

Reading a citizen-produced `tests.xml` meant parsing XML in the job that holds the write token and the model key, so it got a check that refuses any document carrying a `<!DOCTYPE>` or `<!ENTITY>` declaration, and a test that feeds it a billion-laughs bomb and asserts the reader returns *not measured*.

**The test passed with the check deleted.** CPython's expat caps internal entity expansion on its own, so the bomb failed to parse either way and the assertion could not tell the two situations apart. Eight other probes that day failed correctly; this one had been green from the moment it was written, against nothing.

Rewritten to feed in a **valid, parseable** document — one that any reader which looked would answer `(7, 2)` for — whose only disqualifying feature is the declaration. Deleting the check now turns it red.

**The generalisation, and it is the sharper half of this file:** *a test written against a defect you have already fixed proves nothing until you put the defect back.* Entry 9's lesson was that a green suite can pass through a broken system. This one is narrower and worse — a green suite can pass through a guard that does not exist. The cost of finding out is one revert and one test run, and there is no substitute, because the failure mode is silence.

Two other things on this page were caught by the same move. The word-cap regression test at `tests/test_review.py:768` passed against the defect it was written for, because an empty temporary repository produces a comment 37 words shorter than a real one. And the first version of this session's ordering assertion passed a mutation that only *renamed* the deletion step without moving it — the probe was wrong, not the test, which is its own reminder to check what a passing probe actually proved.

---

## 14. The first time a model answered, it failed — and the run kept no record of why

**Where:** PR #60, 2026-07-29. The first review ever composed with a model key in the repository secrets. `SHODANN_LLM_*` unset, so the primary was unconfigured and the chain fell through to `claude-haiku-4-5` exactly as designed.

**What SHODANN said:**

> **Citizen**: @norrisaftcc | **Clearance**: ORANGE | **Status**: REDUCED ALLOCATION
>
> Synthesis was unavailable this cycle (**response violated the output contract twice**)

Three things worked for the first time in that comment: the ORANGE disclosure footer, the coverage reading, and `Tests: 353 passed, none in a pre-success state` — a real tally from a real `tests.xml`, which is the whole of entry 12's rung.

**What did not:** the model was reached, answered twice, and both answers were unpostable. That is a legitimate outcome and the fallback handled it correctly. The defect is what happened next: **nothing recorded which rule was broken.** `_synthesise` computes the findings twice, spends the first set on the retry instruction, and drops both. So the log said "violated the output contract twice", which names the outcome and not one thing about the cause.

**Why it hid until now:** this path had never executed. Every previous review degraded with `no model configured`, so the branch that discards the findings was unreachable in production while remaining fully covered by tests — the tests supply their own violations and never ask what the program *said* about them.

**A second thing the same run exposed.** The job was **green**. `.github/workflows/shodann.yml` carries a step named "Surface the fault to the maintainer", gated on `steps.compose.outcome == 'failure'`, and its own comment promises "the job still turns red at the end." It never has. `EXIT_DEGRADED` is returned only when `main` catches an exception; a review that degrades *gracefully* returns a body and exits 0. Graceful degradation and silent degradation had been the same code path since the exit code was introduced.

**What changed:** `_log_violations` writes the blocking `Violation.code` slugs for both attempts to stderr. Codes only — `message` and `evidence` quote the model's output, which is written from a citizen-authored PR title, and the rule that stops `main` echoing the body applies for the same reason.

**And on the very next run it answered the question:**

```
SHODANN attempt 1 blocked by: missing_section
SHODANN attempt 2 blocked by: missing_section
```

Haiku is omitting a required heading, twice, including on a retry that names the violation. The FORMAT layer asks for four sections in a fenced example and the spec requires the same four, so the prompt and the checker agree — this is a model that will not reliably emit an empty-feeling section, not a contract two documents disagree about.

That log line also exposed the *next* gap immediately: it said `missing_section` and could not say **which** section, which is half a finding. Now named, via a deliberately narrow allowlist — `_check_headings` builds that evidence by subtracting the headings it found from the ones the spec requires, so what survives is this program's own constants and cannot carry model output. `section_order` looks like it qualifies and does not: its message reports the order it *found*, which is the model's.

**The degradation is now announced, and the job still passes.** `::warning::` naming the reason, exit 0. Red would be the wrong instrument: under one-repo-per-student the check lands on the *student's* pull request, and a failed model call is the one thing `PRD.md` §8 insists must not reflect on their submission. A warning is visible in the Actions tab, where the maintainer is, and is not a verdict, where the student is.

**A small dividend.** Adding that call took `review` to eleven branches and tripped `C901` — the first time the complexity gate wired up two commits earlier has fired on this project's own code. It was fixed by moving the falsy check inside the callee rather than by raising the threshold, which is the whole argument for the metric, made by the metric.

---

## 15. The fence that made synthesis impossible — and the first review that worked

**Where:** PR #60, 2026-07-29, chasing entry 14's `missing_section` to ground.

Entry 14's logging said `missing_section` twice and, once it learned to name them, said this:

```
missing_section (Shipping Velocity Report, Algorithm-Approved Patterns,
Growth Opportunities, Recommended Iteration)
```

**All four.** A model omitting a section it has nothing to say in drops one. Losing the entire heading list means the checker could not see the response at all — a different failure wearing the same code, and the count was the only thing that distinguished them.

**What was wrong.** LAYER 4 says *"Generate your response using EXACTLY this structure"* and then shows the structure inside a ` ```markdown ` fence, because that is how you make an example legible. A model that complies with the **illustration** returns its review inside a fence too. `_headings` strips fenced blocks before looking for headings — and that guard is correct, and was itself paid for: a model once illustrated a fix with `# Before` / `# After` inside a fenced example and the validator invented two phantom sections out of the student's own code.

Two correct behaviours, conflicting only when the fence *is* the whole response. Reproduced locally in one line by wrapping a known-good response and getting the byte-identical violation.

**SHODANN could not synthesise a review at all while this held.** Any model, any citizen, every time. It had been true since the validator and the template were first written against each other, and it was invisible because the fallback caught it — the system had a fluent story for its own failure, in SHODANN's own voice, and the story blamed the model.

**What changed:** `unwrap_fenced_response` unwraps only a fence that is the entire response, so a review containing a code example is untouched. The prompt also now says not to wrap, which helps models nobody debugs.

### And then it worked

The first synthesised SHODANN review in the project's history, on the very next run. Every figure in it traces to an instrument, verified against the tree afterwards:

| Claim | Measured | |
|---|---|---|
| "All 363 tests pass" | 363 passed | ✓ |
| "20 style diagnostics" | 20 | ✓ |
| "Zero syntax barriers" | 0 | ✓ |
| "97.9% → 97.5%" | ledger 97.9, measured 97.5 | ✓ |
| "your 19th submission" | pr_count 18 + 1 | ✓ |

The hard/soft split held on its first real outing: the model invented no number. Three of those five figures did not exist anywhere in the system a day earlier — the tallies and the syntax count are entry 12's rung, reaching a citizen.

**Two things in the prose were still wrong**, and neither is a hallucination:

- *"your velocity score of 119.03 reflects the substantial work across 16 files and 1,302 lines added."* **`loc` is not a term in the composite.** The sentence teaches a citizen that writing more lines raises their score, which is the exact behaviour `PRD.md` §7 forbids the system from rewarding — the lines-of-code metric, taught by the machine built to refuse it, in its first sentence about itself.
- *"First tests are hardest tests — you've moved past that threshold"*, said to a citizen with 363 tests. `test_the_phrase_is_not_repeated_to_veterans` stops the *engine* doing this. The model is not bound by the engine, and a phrase reserved for one moment stops meaning anything once it is spent on any other.

**The groundedness probe cannot see either**, and says so itself: every number really was in the prompt, and neither claim contains a novel backticked identifier. Its docstring named this limit — *"it cannot catch a mislabelled figure"* — before there was an example. Now there is one, and it is the most important sentence in the review.

Both are fixed in the prompt, which is the only layer that can. The score's terms are now stated where the score is stated, with lines and files explicitly excluded.

**Status: both guards held on the next run** — the score was attributed to "tests added, docstrings written, and lint opportunities cleared", all real composite terms, and the reserved phrase did not reappear. See entry 16, which is what that same review got wrong instead.

---

## 16. Two instruments, one invented mechanism

**Where:** PR #60, the second synthesised review, minutes after entry 15's guards shipped.

Both guards held. Every figure was again exact — 365 tests, 20 style diagnostics, 0 syntax errors, 97.9% → 97.5%. And the review still contained two false claims, neither of them a fabricated *number*:

> **"Select one of those 20 style diagnostics ... this gets you back to 98%+ coverage territory."**

Style diagnostics and coverage are unrelated instruments. Cleaning lint changes coverage by exactly nothing, and 98%+ is a figure that appears nowhere — this citizen has never been above 97.9%. It sits in **Recommended Iteration**, the one section a student is told to act on, so the failure mode is a citizen doing twenty minutes of work to reach a number that cannot move.

> **"The slight dip suggests complexity may have increased faster than test coverage."**

The measured C901 delta is **0**. The DATA layer says so on the row above.

**What this run actually taught.** Entry 15's fix was instance-shaped: it named the score's terms because the score's terms were what got misused. The very next review produced two more of the same species in two different places. Patching instances loses — the class is *inventing causation between independent measurements*, and prose instructions against a class are unfalsifiable by anything except the next run.

**So this one got a mechanism.** `groundedness.py` had named this exact limit in its own docstring since it was written — *"it cannot catch a mislabelled figure"* — and the limit was drawn too narrowly. It checked backticked identifiers only. It now also checks **percentages**: any figure the response states that no tool report contains.

Blocking from the first occurrence, unlike the identifier probe. One novel identifier is a suggestion (`consider naming it user_age`) and rejecting it would reject good advice; one novel percentage is a measurement nobody took, and there is no reading of it that helps a citizen. Rounding still passes — a model writing 97% for a measured 97.5% is being readable — while 98 against 97.5 does not, which is precisely the case that mattered.

This would also have caught entry 2 ("a whopping 0.0%") and entry 6 ("from 0% to 218 complexity"). Three of the sixteen entries on this page are one missing check.

**The causal half is still prose**, and still unverifiable: the prompt now says the readings are separate instruments and may not be connected, that a delta of 0 means nothing moved, and that no figure may be predicted. Being unable to test that is the honest state of it — but the figure probe now catches every *consequence* of the causal error that carries a number, which is most of them.

**The third review, minutes later, was clean.** No invented figure, no target, no predicted percentage — and it said outright *"This isn't about reaching a target."* Every number exact again: 371 tests, 19 style diagnostics, 0 syntax errors, 97.9% → 97.4%.

### The one thing left, and it was ours

That review said *"Your iteration streak of **18 commits**"*. `save_citizen_history` increments `iteration_streak` once per submission that scored above zero — consecutive **submissions**, never commits. The number was right and the unit was wrong.

The model did not invent it. `prompts/01_base_shodann_prompt.md` line 66 read:

```
| **Iteration Streak** | {{ PREV_STREAK }} commits |
```

It was quoting us, faithfully, and it had no way to know better — the prompt is the only description of that field it will ever see.

**This is the finding, not the label.** Three reviews in a row were audited by comparing every figure against the tools, and this one passed that audit: the number *was* 18. What it failed was a check nobody was running — whether the **unit** attached to a real number is the unit the field actually counts. A mislabelled figure and a fabricated one look identical from outside; the entire difference is whose text the label came from, and the reflex is to file it against the model.

Fixed in the prompt. The general form is worth carrying: **before blaming a model for a claim, grep the prompt for it.**

## 17-22. Eight reviews of one pull request, six classes, and what separated the fixes that held

**Where:** PR #61, the ledger and METRICS.md rungs. SHODANN reviewed its own pull request eight times as commits landed. Every review was audited against the tools; every figure was exact in all eight. Six defect classes came out, none of them visible to a suite that went 372 → 433 green throughout.

Recorded as one entry because the individual defects matter less than what the sequence showed about fixing them.

**17. The score's composition, invented — twice in one comment, incompatibly.** Of twenty style diagnostics: *"would further increase your velocity score's **coverage** component"*, and three paragraphs later, of the same action, *"raise your velocity score's **lint** component"*. Style feeds the lint term and does not touch coverage.

This is entry 16's fabrication **with the number removed**, which is why nothing caught it. Entry 16 built the percentage probe against *"gets you back to 98%+ coverage territory"* — the identical style-to-coverage mechanism — and that probe fires on the `98`. Verified against the posted text: `ungrounded_tokens` returned `[]`, `ungrounded_percentages` returned `[]`. Entry 16's own closing sentence predicted it: the figure probe catches every consequence of the causal error *that carries a number*.

Fixed with a third probe, and the useful part is that it is **grounded in an absence**: no template names a component, term, weight, factor or multiplier of the composite — grep finds zero — so any such claim is ungrounded by construction and the check needs no model of the formula.

**18. Two aliased counters presented as two facts.** *"your 20th submission"* and *"This is your 19th consecutive submission recorded"*, one paragraph apart, both faithful to the prompt. `review()` increments `pr_count` before `build_context`, so `PR_COUNT` is the current submission's number while `PREV_STREAK` is stored and prior — and S1-23, in the same pull request, had just made both counters count the same events. Took three attempts; see the closing note below, which is the real content of this entry.

**19. Contents invented for a file that has none.** *"examining whether your new **functions in METRICS.md** have narrative explanations."* METRICS.md is a generated markdown leaderboard.

The model had less to work from than that implies: template 01 supplies `FILES_CHANGED` as a *count* and no file list at all, so the name can only have come from `PR_TITLE`. A filename in a title became a file with contents, then a file whose functions could be reviewed. And **nothing anywhere told the model it had not read the submission** — the groundedness block forbade inventing figures and causes and said nothing about inventing contents. Not a rule being broken; a rule that did not exist.

Again the shape this file had already named — *"it cannot catch a mislabelled figure... a number that really was in the prompt, under the wrong name"* — with a **filename** in that role, so the identifier probe saw a grounded token and passed.

**20. A measured zero reported as a missing reading.** *"Zero complexity metrics recorded"*, followed by advice to go and understand where complexity lives. The reading was 0 and it was measured: a `C901` count of zero means no function exceeded the branch threshold, which is the best available result.

**Every absent-versus-zero guard in this repository protects the other direction.** Nothing was watching this one. The row was labelled `**Complexity**` with a bare integer, and its unit had changed underneath in #58 from a count of `def ` to a count of threshold violations. The row now names what it counts, and the prompt states the rule the other branches already implement structurally: a reading that was not taken has no row at all, so a number you can see is never a missing one. That generalised on the next run — the model reported "zero compilation barriers" as the measurement it is.

**21. A promotion mechanism, invented.** *"This is how citizens scale from ORANGE to higher clearance bands"*, and in an earlier review *"a skill that compounds as your clearance rises"*. The prompt supplies a band and instructs the model to calibrate to it, and says nowhere how a band is obtained.

Not cosmetic. #59 *declined* `prompts/03`'s `INFER_CLEARANCE` rather than leaving it unimplemented, because a band inferred from readings is a second score and this product rests on improvement outranking position. A citizen told that iterating well raises their band has been handed exactly that second score, by the one voice they cannot check it against — and it contradicts the disclosure footer three paragraphs below.

**22. A trend across nineteen submissions, from two data points.** *"you've sustained 97%+ coverage across 19 consecutive submissions."* The prompt carries one previous coverage figure and one current one, never a series. Removed by taking the streak figure out of the prompt (entry 18) — with nothing to attach it to, the claim has no material.

---

**What separated the fixes that held from the fixes that came back.** This is the entry.

| Class | First fix | Held? |
|---|---|---|
| 17 score composition | probe | yes, rounds 2-8 |
| 19 invented contents | prose **and** probe | yes, rounds 4-8 |
| 21 clearance as earned | prose | **no** — recurred the next run |
| 21 clearance as earned | probe | yes |
| 20 measured zero | prose + a renamed row | yes, rounds 6-8 |
| 18 two counters | template edit ×3 | **no, twice** |

**Every class that got a probe held on the next run. Every class that got only prose came back.** Entry 16 stated this as a conclusion — *"prose instructions against a class are unfalsifiable by anything except the next run"* — and entry 21 is it happening to someone who had just read that sentence and cited it. `clearance.NOT_EARNED` was added at every band, verified present in the rendered prompt, and the very next review made the claim anyway.

Prose is not useless — 19 and 20 held with it, and it is still the right thing to tell a model. It is that **prose is not a fix you can believe until a run has tested it**, and a probe is.

Two more that cost more than they should have:

**A guard scoped to your fix will pass while the defect runs.** Entry 18 took three attempts. The first relabelled the two rows. The second replaced the duplicate figure with *"This is Submission Number minus one, not a second figure to report"* — which handed the model a subtraction instead of a number, **and it did the subtraction**. The third found that the figure had never been only in that row: `describe_history` composed `Iteration streak: 19` separately into `HISTORY_NARRATIVE`, a sentence nobody had looked at. Both earlier guards were green while the defect was live, because both asserted on the row that had already been fixed. The guard now greps the **assembled prompt** for the number. One answer in two places, in the file whose own comments name that failure repeatedly.

**A rule stated in the negative cannot be enforced by asking whether its words appear.** The attribution probe (17) checks its finding against the prompt, deliberately, so that supplying the score's composition would retire the rule by itself. Copying that design into the clearance probe would have **permanently disabled** it: the prompt now contains *"will raise their clearance"* in order to forbid it, so a prompt-relative check reads its own prohibition as a licence. That probe is unconditional, and there is a test pinning the reason.

**What is still open after eight runs: S1-45.** Every reading handed to the model as a bare total gets its missing context invented. Twenty style diagnostics with no categories produced guessed categories (*"likely spacing or naming conventions"* — they are mostly `C408`), then a guessed fixable count (*"clear the 20 in one pass"* — ruff reports 11 of 20 as fixable), and the advice remains unfollowable because the count itself is not reproducible: the analyse job measures with `ruff check . --isolated --extend-select C90` and `python scripts/dev.py check` reports zero. The invention stopped once entry 19's rule landed; the unfollowability did not. Passing through *what produced* a reading rather than only its total is the structural answer, and it is plumbing rather than wording.

**The eighth review was clean.** All four probes returned empty against it, all six classes stayed fixed, and it is the first of the eight with no finding. That is what the loop going dry looks like, and it took eight runs rather than the two the first clean-looking round suggested.


Every defect on this page needed the system to *run*. None was found by reading code, and the test suite was green through all of them — 136 passing tests while SHODANN told a citizen they had written twice as many tests as they had; 243 while it told one their coverage jumped 98.6 points and, in the same comment, that there was nothing to compare against.

**Three** of them were found by *rendering the output and reading it*, which is neither testing nor code review and appears in no methodology. It is the only technique on this page that catches a comment disagreeing with itself — and it caught one again on the day entry 12 was written. Wiring the real test tallies in put a truthful line reading *"0 passed, 11 in a pre-success state"* directly above a section that said *"Nothing in these readings raised one."* Both sentences were true of their own inputs, because the velocity engine has never been shown a pass/fail count. The pair was nonsense, no assertion could see it, and one read of the rendered comment could not miss it.

Entry 13 adds a fourth technique, and it is the cheapest one here: **put the defect back.** A guard is a claim that something would otherwise break, and the claim is untested until you break it. One revert and one test run per guard, and the reward is finding the assertions that have been green since birth against nothing at all.

Two of them needed a different move again: **reading with something withheld.** Entry 10 came from five surveyors who each saw one scope and could not see the others, plus a critic asked only what falls between them. Entry 11 came from readers who were given a document and denied any knowledge of what it was for. Every technique on this page works by removing context from the reader — running the system removes the author's knowledge of what it *should* do, and a blind read removes the reader's ability to supply what the document failed to say. A reviewer who knows the intent will unconsciously fill the gap and report that there wasn't one.

The two agents caught different things and neither caught these: `oracle-warden` verifies what is checkable mechanically, `clive-prompt-warden` verifies what is consistent across documents. Neither can see what only appears when a real event payload meets a real runner.

Which is the argument for rung 1 existing at all. The walking skeleton was not a way to build the system faster. It was the only way to find out what the system does.
