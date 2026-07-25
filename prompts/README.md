# SHODANN Prompt Templates

> **The Algorithm's Communication Framework**
> **Version**: 1.0.0

---

## Overview

This directory contains the prompt architecture for SHODANN's educational
feedback system. Each template follows the 4-layer prompt structure and
enforces the growth-positive vocabulary mandated by The Algorithm.

---

## Template Index

| File | Purpose | When Used |
|------|---------|-----------|
| `01_base_shodann_prompt.md` | Core 4-layer prompt | Every PR review |
| `02_rage_state_addon.md` | Security audit mode | 10% lottery, opt-in, or debt |
| `03_clearance_variations.md` | Level-specific guidance | Based on citizen clearance |
| `04_first_submission_prompt.md` | Onboarding mode | First PR from citizen |
| `05_edge_case_handlers.md` | Unusual submissions | Empty, failing, massive PRs |
| `06_assembled_example.md` | Worked end-to-end example | Reference only, never rendered |

---

## Architecture Diagram

```
                    +------------------+
                    |   PR Submitted   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Edge Case Check |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
    EMPTY_PR           SYNTAX_BARRIER       STANDARD
    CONFIG_ONLY        ALL_FAILING          MASSIVE_PR
         |                   |                   |
         v                   v                   v
    [Short Response]   [Barrier Help]    +-------+-------+
                                         |               |
                                    First PR?      Returning?
                                         |               |
                                         v               v
                              [Onboarding Mode]   [Standard Mode]
                                         |               |
                                         +-------+-------+
                                                 |
                                         +-------v-------+
                                         | RAGE STATE?   |
                                         +-------+-------+
                                           |           |
                                          YES          NO
                                           |           |
                                           v           v
                                    [Add Security]  [Skip]
                                           |           |
                                           +-----+-----+
                                                 |
                                         +-------v-------+
                                         | Clearance     |
                                         | Calibration   |
                                         +-------+-------+
                                                 |
                                         +-------v-------+
                                         | Generate      |
                                         | Response      |
                                         +---------------+
```

---

## Quick Reference: Vocabulary Enforcement

### Forbidden Words

These words MUST NEVER appear in SHODANN output:

| Forbidden | Replacement |
|-----------|-------------|
| Wrong | Suboptimal |
| Mistake | Growth opportunity |
| Failed | Pre-success state |
| Error | Unexpected behavior pattern |
| Bad | Algorithm-misaligned |
| You should | The Algorithm suggests |
| Unfortunately | The Algorithm notes |
| I noticed | The Algorithm has observed |
| Good job | The Algorithm is pleased |
| Great work | Velocity: OPTIMAL |

### RAGE STATE Additions

| Standard | RAGE STATE |
|----------|------------|
| The Algorithm suggests | The Algorithm has noticed |
| Growth opportunity | Security observation |
| Consider trying | The Algorithm strongly recommends |
| Your code | This code |
| Noted | Logged for your protection |

---

## Quick Reference: Response Limits

| Element | Limit |
|---------|-------|
| Total response | Under 400 words |
| Velocity report | 2-3 sentences |
| Approved patterns | 2-3 bullet points |
| Growth opportunities | 1-2 bullet points (max 2) |
| Recommended iteration | Exactly 1 action |
| Security observations | 1-3 findings (RAGE STATE) |

---

## Implementation Checklist

### Before Sending to Gemini

1. [ ] Determine citizen clearance level
2. [ ] Check if first submission
3. [ ] Detect edge cases (empty, syntax barrier, etc.)
4. [ ] Calculate RAGE STATE activation
5. [ ] Gather all tool outputs (syntax, style, tests, coverage)
6. [ ] Calculate velocity metrics
7. [ ] Inject all variables into base template
8. [ ] Add clearance-specific section
9. [ ] Add RAGE STATE section (if active)
10. [ ] Add edge case modifications (if applicable)

### After Receiving Response

1. [ ] Verify word count under 400
2. [ ] Check for forbidden vocabulary (should be clean, but verify)
3. [ ] Confirm required sections present
4. [ ] Post to PR as comment

---

## Variable Quick Reference

```yaml
# Citizen Context
CITIZEN_USERNAME: github.event.pull_request.user.login
CLEARANCE_NAME: derived from clearance_level via the clearance ladder
CLEARANCE_NUMBER: 1-6 numeric, from the citizen record
CURRENT_WEEK: workflow env
PR_COUNT: from citizen history file
PREV_COVERAGE: from citizen history file
PREV_STREAK: iteration_streak from citizen history file
ITERATION_COUNT: git commit count in PR

# Submission Data
FILES_CHANGED: github.event.pull_request.changed_files
LINES_ADDED: github.event.pull_request.additions
LINES_REMOVED: github.event.pull_request.deletions
PR_TITLE: github.event.pull_request.title

# Tool Outputs
SYNTAX_REPORT: from py_compile step
SYNTAX_ERRORS: count of syntax issues
STYLE_REPORT: from flake8 step
STYLE_ISSUE_COUNT: count of style issues
TEST_REPORT: from pytest step
TESTS_PASSED: count of passing tests
TESTS_FAILED: count of failing tests
CURRENT_COVERAGE: from pytest-cov

# Calculated Metrics
COVERAGE_DELTA: current - previous coverage
PREV_COMPLEXITY: from citizen history file
CURRENT_COMPLEXITY: previous + complexity delta
COMPLEXITY_DELTA: from velocity engine
VELOCITY_SCORE: from velocity engine
VELOCITY_ASSESSMENT: text description of velocity state

# Composed sections - assembled text, not scalars. Each needs its own
# assembly step before the base template can be rendered.
MODE_STATEMENT: "NORMAL (Growth Celebration)" or "RAGE STATE (Audit Mode)"
HISTORY_NARRATIVE: one or two sentences of citizen history, facts only
CLEARANCE_INSTRUCTIONS: from 03_clearance_variations.md, empty until wired
SECURITY_SECTION: from 02_rage_state_addon.md, empty unless RAGE active
RAGE_SECTION_IF_ACTIVE: security observations heading, empty unless RAGE active
```

`shodann.prompts.build_context` is the authority on this list; the test suite
asserts it supplies every variable the base template declares, so the two
cannot drift apart silently. This table is a reading aid, not the contract.

**Mode flags are not template variables.** `RAGE_ACTIVE`, `RAGE_REASON`,
`FIRST_SUBMISSION` and `EDGE_CASE_HANDLER` select *which* template renders and
what goes into the composed sections above. They are never bound into a
template as `{{ VAR }}`, and adding them to a context would bind nothing.

---

## Testing Prompts Locally

Rendering is done by `shodann.prompts`, offline, with no API key:

```bash
python -c "from shodann.prompts import render_prompt, build_context; print(render_prompt(...))"
```

See `tests/test_prompts.py` for a worked context. The test suite renders the
base template on every run and asserts nothing is left unresolved.

### Why not envsubst

An earlier version of this file suggested `envsubst < 01_base_shodann_prompt.md`.
That cannot work, for three separate reasons, and it is worth knowing all three
before reaching for a simpler tool:

1. **`envsubst` expands `$VAR`, not `{{ VAR }}`.** It would substitute nothing
   at all and emit the template unchanged.
2. **These files are documents, not templates.** The prompt lives inside a
   fenced block, and the same file carries a variable-reference table that
   mentions every placeholder as documentation. Whole-file substitution would
   rewrite the documentation too. The renderable region is delimited by
   `<!-- TEMPLATE:BEGIN -->` / `<!-- TEMPLATE:END -->` markers.
3. **Templates `02`, `04` and `05` contain control flow** — `{{ IF X }}`,
   `{{ FOR EACH x IN y }}`, `{{ TESTS_PASSED + TESTS_FAILED }}` — which no
   substitution tool can interpret. They need converting to real Jinja
   (`{% if X %}`, `{% for x in y %}`) before they can be rendered at all. The
   renderer detects the ad-hoc syntax and reports the file and line rather than
   failing with a parser trace.

### Markers are required

A template with no `TEMPLATE:BEGIN` / `TEMPLATE:END` pair raises rather than
guessing, because guessing means sending a variable-reference table to the
model. Only `01` carries markers today; the rest are added as each template
comes into scope.

---

## Extending the Templates

### Adding a New Edge Case

1. Add detection logic to `05_edge_case_handlers.md`
2. Create response template following SHODANN voice
3. Update edge case detection in workflow
4. Test with sample PRs

### Adjusting Clearance Levels

1. Modify appropriate section in `03_clearance_variations.md`
2. Update topic lists for new concepts
3. Adjust vocabulary complexity
4. Test with sample citizen at that level

### Modifying RAGE STATE

1. Edit `02_rage_state_addon.md`
2. Maintain "concerningly helpful" tone
3. Ensure growth framing in all security feedback
4. Test security messaging tone

---

## Philosophy Reminder

```
+------------------------------------------------------------------+
|                    THE ALGORITHM'S CORE VALUES                    |
+------------------------------------------------------------------+
|                                                                  |
|  1. VELOCITY OVER POSITION                                       |
|     The citizen who improves from 0% to 30% beats the citizen    |
|     who maintains 90%. We measure dy/dx, not y.                  |
|                                                                  |
|  2. ITERATION IS ALWAYS POSITIVE                                 |
|     More commits = healthy development. Never suggest fewer.     |
|                                                                  |
|  3. FIRST TESTS ARE HARDEST TESTS                                |
|     Going from 0 to 1 test is harder than 1 to 10.              |
|                                                                  |
|  4. SECURITY IS PROTECTION, NOT PUNISHMENT                       |
|     RAGE STATE helps citizens, it does not harm them.            |
|                                                                  |
|  5. EVERY WORD MUST EARN ITS PLACE                               |
|     400 word limit forces precision. Be specific, not generic.   |
|                                                                  |
+------------------------------------------------------------------+
```

---

*"The Algorithm's prompts are precise. The Algorithm's prompts are consistent.
The Algorithm's prompts produce growth."*

---

**Maintained by**: The Algorithm
**Last Updated**: {{ CURRENT_DATE }}
**Classification**: INSTRUCTOR REFERENCE
