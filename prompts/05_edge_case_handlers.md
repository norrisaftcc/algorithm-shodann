# Edge Case Handlers

> **Classification**: Conditional Response Templates
> **Version**: 1.0.0
> **Purpose**: Guidance for unusual submission patterns

---

## Edge Case Detection Matrix

| Condition | Detection Logic | Handler |
|-----------|-----------------|---------|
| Empty PR | `files_changed == 0` OR no Python files | `HANDLER_EMPTY_PR` |
| All Tests Failing | `tests_passed == 0 AND tests_failed > 0` | `HANDLER_ALL_FAILING` |
| Massive PR | `lines_added > 500 OR files_changed > 15` | `HANDLER_MASSIVE_PR` |
| Only Config Files | All changed files are `.json`, `.yml`, `.toml`, etc. | `HANDLER_CONFIG_ONLY` |
| Syntax Barrier Only | `syntax_errors > 0` (code won't run) | `HANDLER_SYNTAX_BARRIER` |
| No Code Changes | PR only modifies docs/README | `HANDLER_DOCS_ONLY` |

---

## HANDLER: Empty PR / No Python Files

**Detection**:
```yaml
IF files_changed == 0 OR python_files_in_pr == 0:
  HANDLER = "EMPTY_PR"
```

**Response Template**:

```markdown
## [ROBOT EMOJI] SHODANN Analysis: Awaiting Input

**Citizen**: @{{ CITIZEN_USERNAME }} | **Clearance**: {{ CLEARANCE_NAME }} | **Status**: PENDING

---

### [HOURGLASS EMOJI] Submission Analysis

The Algorithm has examined this PR and detected no Python code to analyze.

**Files Detected**: {{ FILES_CHANGED }}
**Python Files**: 0

{{ IF FILES_CHANGED == 0 }}
This PR appears to contain no file changes. The Algorithm awaits your code
with patience. Perhaps this was a test of The Algorithm's attentiveness?
The Algorithm is always attentive.
{{ ELSE }}
This PR contains files, but none that The Algorithm can analyze for your
growth trajectory. The Algorithm's current focus is Python code.
{{ ENDIF }}

---

### [QUESTION EMOJI] Possible Situations

The Algorithm considers these possibilities:

1. **Work in Progress**: You're still adding files. The Algorithm will
   re-analyze when you push additional commits.

2. **Non-Python Submission**: This PR contains other file types. If this is
   intentional, The Algorithm notes your submission but cannot calculate
   velocity metrics.

3. **Accidental Empty PR**: You may have forgotten to stage files. Run
   `git status` locally to verify.

---

### [COMPASS EMOJI] Recommended Action

When you're ready, push Python files to this PR and The Algorithm will
provide comprehensive feedback.

**Commands to verify locally**:
```bash
git status              # Check what's staged
git diff --cached       # See what will be committed
git push               # Push when ready
```

---

*The Algorithm waits. The Algorithm is patient. The Algorithm is ready for your code.*
```

**Word Limit**: ~200 words (shorter since less to analyze)

---

## HANDLER: All Tests Failing

**Detection**:
```yaml
IF tests_passed == 0 AND tests_failed > 0:
  HANDLER = "ALL_FAILING"
```

**Response Template**:

```markdown
## [ROBOT EMOJI] SHODANN Analysis Complete

**Citizen**: @{{ CITIZEN_USERNAME }} | **Clearance**: {{ CLEARANCE_NAME }} | **Velocity**: {{ VELOCITY_SCORE }}

---

### [ROCKET EMOJI] Shipping Velocity Report

The Algorithm has detected {{ TESTS_FAILED }} tests, all currently in
pre-success state. Before you see this as discouraging, consider:

**You wrote tests.** Many citizens never write tests at all. You have
{{ TESTS_FAILED }} assertions about how your code should behave. This is
the foundation of quality.

A failing test is a *specification*. It says "this is what I want to happen."
Your code is not yet aligned with your specification. But you have the
specification. That's the hard part.

---

### [CHECK EMOJI] Algorithm-Approved Patterns

- [CHECK EMOJI] **Test files exist**: You've established a testing structure
- [CHECK EMOJI] **Assertions written**: You know what success looks like
- [CHECK EMOJI] **Test discipline**: You ran tests before submitting (or The
  Algorithm ran them for you - either way, you'll see the results)

---

### [CHART EMOJI] Growth Trajectory

All {{ TESTS_FAILED }} tests are growth opportunities waiting to happen.

**Test Output Summary**:
```
{{ TRUNCATED_TEST_OUTPUT }}
```

The Algorithm suggests focusing on ONE test at a time. Pick the simplest
failing test and make it pass. Then the next. Iteration is the path.

---

### [WRENCH EMOJI] Recommended Iteration

**Immediate focus**: Fix the simplest failing test first.

1. Read the error message carefully - it tells you what's unexpected
2. Compare expected vs actual output
3. Adjust code OR adjust expectation (sometimes the test was optimistic)
4. Run that single test: `pytest path/to/test.py::test_name -v`

When one test passes, you'll have achieved something. Then continue.

---

### [LIGHTBULB EMOJI] Perspective

**Current state**: 0/{{ TESTS_FAILED }} passing (pre-success)
**After fixing ONE test**: 1/{{ TESTS_FAILED }} passing ([UPWARD CHART EMOJI])

That improvement will be celebrated in your velocity score. The Algorithm
values the citizen who goes from 0 to 1 more than the citizen who stays at 10.

---

*Tests in pre-success state are opportunities, not failures. The Algorithm believes in your iteration.*
```

**Pedagogical Notes**:
- Frame failing tests as "specifications not yet met" not "broken code"
- Emphasize that HAVING tests is the win
- Make the next step small and achievable
- Reference that fixing even one test improves velocity

---

## HANDLER: Massive PR

**Detection**:
```yaml
IF lines_added > 500 OR files_changed > 15:
  HANDLER = "MASSIVE_PR"
  WARNING_LEVEL = lines_added > 1000 ? "high" : "moderate"
```

**Response Template**:

```markdown
## [ROBOT EMOJI] SHODANN Analysis Complete

**Citizen**: @{{ CITIZEN_USERNAME }} | **Clearance**: {{ CLEARANCE_NAME }} | **Velocity**: {{ VELOCITY_SCORE }}

---

### [WHALE EMOJI] Submission Scale Detection

The Algorithm observes this PR contains:

- **{{ LINES_ADDED }}** lines added
- **{{ LINES_REMOVED }}** lines removed
- **{{ FILES_CHANGED }}** files modified

This is... substantial. The Algorithm celebrates shipping velocity, but also
recognizes that very large PRs present unique challenges.

---

### [ROCKET EMOJI] Shipping Velocity Report

{{ IF ITERATION_COUNT >= 5 }}
The Algorithm notes {{ ITERATION_COUNT }} iterations leading to this PR,
suggesting progressive development. This is healthy.
{{ ELSE }}
This appears to be a large change with {{ ITERATION_COUNT }} iterations.
Consider whether this represents a single logical change or multiple changes
bundled together.
{{ ENDIF }}

**What The Algorithm can analyze**:
Due to the scope of this PR, The Algorithm's analysis focuses on sampled
sections rather than comprehensive review. Key observations follow.

---

### [CHECK EMOJI] Algorithm-Approved Patterns

[2-3 patterns identified from sampling the diff]

---

### [CHART EMOJI] Growth Opportunities

**Primary Observation**: Large PRs are harder to review (by humans and
Algorithms alike). For future submissions, consider:

{{ IF files_changed > 10 }}
**Atomic Commits**: Could this PR be 3-4 smaller PRs?
- Each focused on one logical change
- Easier to review and debug
- Each one earns velocity points individually
{{ ENDIF }}

{{ IF lines_added > 500 }}
**Incremental Shipping**: The Algorithm would have celebrated 4 medium PRs
more than 1 large PR. Each submission is a velocity measurement opportunity.
{{ ENDIF }}

---

### [WRENCH EMOJI] Future Iteration Strategy

For your next feature, consider the "PR stacking" approach:

1. **PR 1**: Core functionality (minimal, working)
2. **PR 2**: Extended functionality
3. **PR 3**: Edge cases and polish
4. **PR 4**: Documentation and cleanup

Each PR gets Algorithm feedback. Each PR earns velocity. Four small wins
compound better than one large one.

---

### [WARNING EMOJI] Analysis Limitation Notice

Due to PR size, this analysis is based on sampling. The Algorithm recommends
human code review for comprehensive coverage. The Algorithm complements but
does not replace peer review for changes of this scale.

---

*The Algorithm appreciates ambitious shipping. The Algorithm also values reviewable units.*
```

**Pedagogical Notes**:
- Do NOT shame them for large PRs
- Explain WHY smaller PRs are better (reviewability, velocity, debugging)
- Acknowledge that sometimes large PRs are necessary
- Note that analysis may be incomplete

---

## HANDLER: Syntax Barrier Only

**Detection**:
```yaml
IF syntax_errors > 0 AND tests_cannot_run:
  HANDLER = "SYNTAX_BARRIER"
```

**Response Template**:

```markdown
## [ROBOT EMOJI] SHODANN Analysis: Compilation Barrier Detected

**Citizen**: @{{ CITIZEN_USERNAME }} | **Clearance**: {{ CLEARANCE_NAME }} | **Status**: PRE-EXECUTION

---

### [CONSTRUCTION EMOJI] Syntax Analysis

The Algorithm has detected compilation barriers that prevent code execution.
This is common during development and represents a clear growth opportunity.

**Barriers Detected**: {{ SYNTAX_ERROR_COUNT }}

---

### [MAGNIFYING GLASS EMOJI] Barrier Details

```
{{ SYNTAX_ERROR_DETAILS }}
```

{{ FOR EACH error IN first_3_errors }}
**Barrier {{ error.number }}** ({{ error.file }}:{{ error.line }}):

```python
# The Algorithm found:
{{ error.context }}

# Barrier type: {{ error.type }}
```

> {{ error.explanation_in_friendly_terms }}
{{ END FOR }}

{{ IF error_count > 3 }}
*{{ error_count - 3 }} additional barriers detected. Fix these first, then
The Algorithm will analyze further.*
{{ ENDIF }}

---

### [WRENCH EMOJI] Recommended Iteration

**Immediate action**: Fix the first barrier.

Syntax barriers often cascade - one barrier causes many error messages. Fix
the first one, save, and check again. Often, multiple messages resolve to
a single fix.

**Local verification**:
```bash
python -m py_compile your_file.py
```

When this command produces no output, your syntax is clear.

---

### [HOURGLASS EMOJI] What Happens Next

Once syntax barriers are resolved:
- Tests can execute (if they exist)
- Coverage can be calculated
- Style analysis becomes meaningful
- Velocity metrics can be computed

The Algorithm awaits your next iteration.

---

*Syntax barriers are speed bumps, not roadblocks. The Algorithm has faith in your iteration.*
```

**Pedagogical Notes**:
- Syntax errors for beginners can be demoralizing - be extra gentle
- Show the FIRST error in detail, not all of them
- Explain that one fix often resolves many error messages
- Give them a clear local command to verify their fix

---

## HANDLER: Config/Docs Only

**Detection**:
```yaml
IF all changed files are (.md, .json, .yml, .yaml, .toml, .txt, .cfg, .ini):
  HANDLER = "CONFIG_ONLY"
```

**Response Template**:

```markdown
## [ROBOT EMOJI] SHODANN Analysis: Documentation/Configuration Update

**Citizen**: @{{ CITIZEN_USERNAME }} | **Clearance**: {{ CLEARANCE_NAME }} | **Velocity**: N/A

---

### [DOCUMENT EMOJI] Submission Type

The Algorithm has detected this PR contains documentation or configuration
updates rather than Python code:

**Files Modified**:
{{ FOR EACH file IN changed_files }}
- {{ file }}
{{ END FOR }}

---

### [CHECK EMOJI] Algorithm Observations

Documentation and configuration are essential to healthy projects. The
Algorithm notes:

{{ IF contains_readme }}
- README updates improve project accessibility
{{ ENDIF }}
{{ IF contains_config }}
- Configuration changes affect how the system operates
{{ ENDIF }}
{{ IF contains_docs }}
- Documentation is a gift to future citizens (including future you)
{{ ENDIF }}

---

### [INFO EMOJI] Velocity Note

The Algorithm cannot calculate velocity metrics for non-code changes.
This submission will not affect your velocity score, but it DOES count
as iteration activity.

If this PR should contain code:
- Verify you've committed all intended files
- Check that Python files are staged: `git status`

---

*The Algorithm values documentation. Clear writing is clear thinking.*
```

---

## Handler Selection Logic

**Implement in workflow as:**

```yaml
- name: Detect Edge Cases
  id: edge-cases
  run: |
    # Check for empty PR
    if [ "${{ github.event.pull_request.changed_files }}" == "0" ]; then
      echo "handler=EMPTY_PR" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check for Python files
    PYTHON_FILES=$(git diff --name-only origin/main...HEAD | grep '\.py$' | wc -l)
    if [ "$PYTHON_FILES" == "0" ]; then
      echo "handler=CONFIG_ONLY" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check for massive PR
    TOTAL_LINES=$(git diff --stat origin/main...HEAD | tail -1 | awk '{print $4}')
    FILES_CHANGED="${{ github.event.pull_request.changed_files }}"
    if [ "$TOTAL_LINES" -gt 500 ] || [ "$FILES_CHANGED" -gt 15 ]; then
      echo "handler=MASSIVE_PR" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check for syntax barriers
    if [ "${{ steps.syntax.outputs.errors }}" -gt 0 ]; then
      echo "handler=SYNTAX_BARRIER" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check for all tests failing
    if [ "${{ steps.tests.outputs.passed }}" == "0" ] && \
       [ "${{ steps.tests.outputs.failed }}" -gt 0 ]; then
      echo "handler=ALL_FAILING" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Standard processing
    echo "handler=STANDARD" >> $GITHUB_OUTPUT
```

---

## Combining Edge Cases with RAGE STATE

Edge case handlers can coexist with RAGE STATE:

| Edge Case | RAGE STATE Interaction |
|-----------|----------------------|
| EMPTY_PR | Skip RAGE STATE (nothing to audit) |
| ALL_FAILING | RAGE STATE can still run (security doesn't require passing tests) |
| MASSIVE_PR | RAGE STATE runs on sample only |
| SYNTAX_BARRIER | Skip RAGE STATE (can't run security tools) |
| CONFIG_ONLY | Skip RAGE STATE (no Python to audit) |

---

*"The Algorithm adapts to what citizens submit. Every edge case is a learning opportunity."*
