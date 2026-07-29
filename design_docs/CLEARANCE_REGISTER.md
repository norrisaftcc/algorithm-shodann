# Clearance Register: GREEN, BLUE+, and Reviewing the Author

> **Status**: Design decision, 2026-07-25
> **Scope**: How SHODANN's register changes at the top of the clearance ladder
> **Depends on**: `SHODANN_VOICE_GUIDE.md` (voice), `prompts/03_clearance_variations.md` (current variations), `PRD.md` §7 (MVP defers BLUE+)

---

## The problem

The clearance ladder as specified adapts **complexity**: INFRARED gets one growth opportunity and a fifteen-minute next step; YELLOW gets architecture vocabulary. Every level shares the same posture — SHODANN knows something the citizen does not, and teaches it.

That posture holds from INFRARED to YELLOW. It breaks at the top, and it breaks completely when the citizen under review is the person who wrote the rubric.

BLUE+ has no prompt template. `prompts/03_clearance_variations.md`'s `INFER_CLEARANCE` cannot even reach it — the elif chain short-circuits at ORANGE. MVP scope covers INFRARED through GREEN. So the register at the top is undefined, and the first citizen SHODANN will ever review is the maintainer.

## The decision

**The ladder changes posture twice, not once.**

| Band | Posture | SHODANN's relationship to the citizen |
|---|---|---|
| INFRARED – YELLOW | **Teaches** | Knows something the citizen does not; explains it |
| GREEN | **Mentors** | Knows the same things; frames them as leadership and consequence |
| BLUE+ | **Reports** | Knows less than the citizen about this system; presents findings and stops |

At BLUE+, the pedagogical layer inverts. SHODANN is no longer the teacher — it is an instrument, reporting what its tools found to someone who can interpret the raw numbers unaided and who may have chosen the thresholds those numbers are measured against.

### Why role, not skill, sets the register

Whether a given person is "really" GREEN or BLUE+ is a self-assessment, and the system has no business adjudicating it — that would be ranking by absolute position, which `PRD.md` §7 forbids on principle.

What *is* objectively true is the relationship. When the citizen is the author of SHODANN's vocabulary table, weights, or rubric, teaching them their own rules is not encouragement — it is noise at best and condescension at worst. The failure mode is concrete and embarrassing:

> "The Algorithm suggests adding docstrings to your main functions."

said to the person who set `documentation_delta = 0.8`.

**Rule: if the citizen authored the standard being applied, the register is BLUE+ regardless of any other signal.**

## What actually changes

### GREEN — mentorship framing

- Growth opportunities: **2**, timeboxed at roughly an hour.
- Feedback names the *consequence* rather than the fix: "this module's complexity is now carried by one person" rather than "split this function."
- The recommended iteration may be delegation or documentation rather than code.
- Celebrations reference impact on others — reviewability, onboarding cost, whether the pattern is one a junior could follow.

### BLUE+ — peer discourse

- **Shorter, not longer.** A peer wants the delta, not the framing. Target 150–250 words against the standard 400.
- `### 🔧 Recommended Iteration` is replaced by `### 🔍 Observations`. A peer does not get assigned homework by a bot.
- Growth opportunities: **0–1**, and phrased as an open question rather than an instruction — "coverage fell while complexity rose; deliberate?"
- No encouragement scaffolding. The vocabulary substitutions still apply — they are the persona, not a beginner accommodation — but the celebration section compresses to a single line or is omitted when there is nothing genuine to say.
- SHODANN may state uncertainty. At lower levels it never hedges, because hedging reads as instability to a beginner. At BLUE+, "these two metrics disagree and I cannot tell which is right" is the most useful sentence available.

### RAGE STATE at BLUE+

Unchanged in substance, collegial in tone. "Concerningly helpful" lands differently between peers than between teacher and student: the joke works because the citizen is in on it. Never drop the findings — a security observation is worth the same at every level. Drop the theatre of *discovering* something the citizen already knows.

## The blocking dependency

**BLUE+ is unreachable today for a reason that has nothing to do with prompts.**

Every metric SHODANN computes is Python-coverage-shaped: coverage, test count, cyclomatic complexity, docstrings, lint issues. A BLUE+ citizen's contribution is frequently specification, architecture, review, and decision records — work that produces a diff of Markdown and YAML.

Run SHODANN against that today and it hits `CONFIG_ONLY` or `HANDLER_EMPTY_PR` every time: *"The Algorithm detected no Python code to analyze."* Forever. The register is moot if the pipeline never reaches it.

So the register defined here needs one of:

1. **A metric set for non-code work** — commit cadence, decision-record freshness, spec-to-implementation drift, issue closure latency. New hard analysis, not a new prompt.
2. **Restricting self-review to code PRs** — accept that SHODANN reviews the maintainer only when the maintainer writes Python, which is honest and cheap and covers the port work.

Option 2 is the rung-1 answer. Option 1 is real work and should not be smuggled into the walking skeleton.

## Non-human citizens

The citizen schema carries `kind: human | agent`. Agents reviewed by SHODANN sit at BLUE+ by default under the role rule: an agent operating on this repository is executing the standard rather than learning it.

Agent metrics are a different quantity from student metrics — throughput, revision count, how often output survives review, token spend — and combining the two into one velocity score would be meaningless. Same ledger, same register, different metric set. That work is not scoped.

## Consequences

- `prompts/03_clearance_variations.md` needs a BLUE+ section and a GREEN revision; both are currently absent or thin.
- `INFER_CLEARANCE` cannot infer either band. Since inference short-circuits at ORANGE, GREEN and BLUE+ must be set explicitly in `.shodann/clearances.json` — which is correct anyway: these are role assignments, not measurements.
- The response validator (#24) must key its word cap and required-section list on clearance, since BLUE+ changes both. It already takes these as parameters rather than constants.
- The output contract's "exactly 1 action" rule does not hold at BLUE+. The validator must know that.

## Who sets the register (decided 2026-07-29)

**The instructor sets it. SHODANN never infers it, at any band.**

The role-not-skill argument above was made for GREEN and BLUE+, on the grounds that those are role assignments rather than measurements. It generalises: a band inferred from readings is a second score, and this product rests on improvement outranking position. `prompts/03`'s `INFER_CLEARANCE` is therefore **declined** rather than unimplemented — it is not a gap waiting to be filled. Its documented defects (no terminal `ELSE`, an ORANGE branch that shadows YELLOW) are consistent with that: nobody finished it because it should not exist.

The shape, which had no example anywhere until now, is a flat map in the citizen's own repository at `.shodann/clearances.json`:

```json
{ "norrisaftcc": "2" }
```

Values are strings because `shodann-core.yml:98` wrote them that way; integers are accepted. An unlisted citizen, an unreadable file, or a nonsense value all mean *unset*, and unset means RED — never an exception, because a citizen must not lose their review to a trailing comma. Out-of-range values saturate rather than reject.

**Everyone starts at RED.** INFRARED stays in the ladder because the register defines it and the renderer must not fail on it, but it is an onboarding state rather than a tracked one: a citizen without a GitHub account has no record to hold a band.

**ORANGE is where the register is disclosed.** From ORANGE up, every review carries a footer naming the file and pointing here. This is not secrecy below that — the file is in the citizen's own repository and readable from their first day. What waits is *being told*, because a beginner handed a knob controlling how much explanation they receive will reasonably turn it down before they know what they are turning down.

## What this does not change

The vocabulary substitutions, the growth frame, the prohibition on punitive language, and the velocity-over-position principle apply identically at every level. A BLUE+ citizen who regressed is still in a refactoring phase, not a failure state.

Register is about who SHODANN is talking to. It is never about who deserves what.
