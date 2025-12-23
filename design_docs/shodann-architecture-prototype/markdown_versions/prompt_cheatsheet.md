# Prompt Engineering Cheatsheet

> **The 4-Layer Structure for Educational AI Prompts**

---

## Overview

Effective educational prompts have four distinct layers, each serving a specific purpose. When combined, they ensure AI feedback is appropriately calibrated, grounded in facts, pedagogically sound, and consistently formatted.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROMPT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│  🎯  CONTEXT LAYER      │  WHO is the student?                 │
├─────────────────────────────────────────────────────────────────┤
│  📊  DATA LAYER         │  WHAT did tools find?                │
├─────────────────────────────────────────────────────────────────┤
│  🎓  PEDAGOGICAL LAYER  │  HOW should AI teach?                │
├─────────────────────────────────────────────────────────────────┤
│  📝  FORMAT LAYER       │  WHAT structure to use?              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: 🎯 Context Layer

### Purpose
**Helps AI calibrate feedback appropriately.**

Week 3 students shouldn't get advanced optimization suggestions. A struggling student needs different feedback than an advanced one.

### Key Elements

| Element | Example | Why It Matters |
|---------|---------|----------------|
| Student Identifier | `Student: @${{ github.event.pull_request.user.login }}` | Personalizes feedback |
| Course Information | `Course: Introductory Python Programming` | Sets expectations |
| Week/Module | `Week: 3 (focusing on loops and conditionals)` | Filters topic complexity |
| Learning Objectives | `Current topics: for loops, while loops, break/continue` | Focuses feedback scope |

### Template

```yaml
## Student Context
Student: @${{ github.event.pull_request.user.login }}
Course: [Course Name]
Week: [Number] (focusing on [current topics])
Previous PRs: [count if available]
```

### 💡 Pro Tip

> Include week number to automatically filter out concepts they haven't learned yet. Telling the AI "Week 3" is more effective than listing everything to avoid.

---

## Layer 2: 📊 Data Layer

### Purpose
**Gives AI concrete facts to base feedback on.**

Grounds the AI in reality, reducing hallucination. The AI can confidently say "Line 15 has a syntax error" because the compiler said so.

### Key Elements

| Element | Example | Why It Matters |
|---------|---------|----------------|
| Compilation Results | `Compilation: ${{ steps.syntax-check.outputs.result }}` | Binary: works or doesn't |
| Linter Output | `Style Issues: ${{ steps.style-check.outputs.issues }}` | Specific line numbers |
| Test Results | `Tests: 4 passed, 2 failed` | Objective success metrics |
| File Statistics | `Files Changed: ${{ github.event.pull_request.changed_files }}` | Scope awareness |

### Template

```yaml
## Technical Analysis
Compilation: ${{ steps.syntax-check.outputs.result }}
Style Issues: ${{ steps.style-check.outputs.issues }}
Test Results: ${{ steps.test.outputs.summary }}
Files Changed: ${{ github.event.pull_request.changed_files }}
Lines Added: ${{ github.event.pull_request.additions }}
```

### 💡 Pro Tip

> Always run real tools first—AI analysis is more accurate with concrete compiler/linter output. Never ask AI to "find syntax errors" when `python -m py_compile` can tell you definitively.

---

## Layer 3: 🎓 Pedagogical Layer

### Purpose
**Ensures AI acts as supportive teaching assistant, not harsh critic.**

This is the difference between feedback that discourages and feedback that motivates continued learning.

### Key Elements

| Element | Example | Why It Matters |
|---------|---------|----------------|
| Priority | `Priority: Learning over perfection` | Sets the value hierarchy |
| Tone | `Style: Encouraging, specific examples` | Emotional safety |
| Focus Limit | `Focus: 1-3 main concepts per review` | Prevents overwhelm |
| Level | `Level: Beginner (avoid advanced topics)` | Matches student capability |

### Template

```yaml
## Teaching Instructions
Priority: Learning over perfection
Style: Encouraging, use specific examples from their code
Focus: Address 1-3 main concepts maximum
Level: [Beginner/Intermediate/Advanced]
Avoid: [Topics they haven't learned yet]
```

### 💡 Pro Tip

> The 1-3 concept limit prevents overwhelming students with too much feedback at once. Research shows students retain more when feedback is focused rather than comprehensive.

---

## Layer 4: 📝 Format Layer

### Purpose
**Creates consistent, scannable feedback.**

Students know what to expect and how to use the feedback. Consistency builds trust and reduces cognitive load.

### Key Elements

| Element | Example | Why It Matters |
|---------|---------|----------------|
| Structure Template | `Use sections: Working Well, Learning, Fixes` | Predictable format |
| Length Guidance | `Keep total response under 300 words` | Respects attention |
| Emoji Usage | `Use emojis for section headers only` | Visual scanning |
| Code Examples | `Include corrected code snippets when helpful` | Actionable guidance |

### Template

```yaml
## Response Structure
Use this exact format:

🎉 **What's Working Well**: [specific positives]

📚 **Learning Opportunities**: [explanations with examples]

🔧 **Quick Fixes**: [actionable improvements]

Keep response under 300 words. Be specific, not generic.
```

### 💡 Pro Tip

> Consistent structure helps students quickly find the information they need. After a few reviews, they'll know exactly where to look for actionable fixes.

---

## Complete 4-Layer Prompt Example

Here's a full prompt combining all four layers:

```yaml
# =================================================================
# CONTEXT LAYER - Who is this student?
# =================================================================
## Student Context
Student: @${{ github.event.pull_request.user.login }}
Course: Introductory Python Programming  
Week: 3 (focusing on loops and conditionals)
Previous submissions: This appears to be their 2nd PR

# =================================================================
# DATA LAYER - What did our tools find?
# =================================================================
## Technical Analysis
Compilation: ${{ steps.syntax-check.outputs.result }}
Style Issues: ${{ steps.style-check.outputs.issues }}
Files Changed: ${{ github.event.pull_request.changed_files }}

# =================================================================
# PEDAGOGICAL LAYER - How should you teach?
# =================================================================
## Teaching Instructions
Priority: Learning over perfection
Style: Encouraging, specific examples from their code
Focus: Address 1-3 main concepts maximum
Level: Beginner (avoid list comprehensions, decorators)

If there are syntax errors:
- Explain each error in student-friendly terms
- Show exactly where the problem is
- Provide a working example

If code compiles:
- Praise what's working
- Focus on code style and organization
- Introduce one new concept they could try

# =================================================================
# FORMAT LAYER - Structure your response
# =================================================================
## Response Structure
Use this format:

🎉 **What's Working Well**: [specific positives from their code]

📚 **Learning Opportunities**: [1-2 concepts with examples]

🔧 **Quick Fixes**: [actionable improvements they can make now]

Keep total response under 250 words.
```

---

## Quick Reference Cards

| Layer | Icon | Key Question | Primary Purpose |
|-------|------|--------------|-----------------|
| Context | 🎯 | WHO is the student? | Calibrate difficulty |
| Data | 📊 | WHAT did tools find? | Ground in facts |
| Pedagogical | 🎓 | HOW should AI teach? | Ensure supportive tone |
| Format | 📝 | WHAT structure? | Create consistency |

---

## Common Mistakes to Avoid

### ❌ Missing Context Layer
**Problem:** AI gives advanced feedback to beginners  
**Example:** Suggesting list comprehensions to Week 1 students  
**Fix:** Always include course week and current topics

### ❌ Missing Data Layer
**Problem:** AI hallucinates errors that don't exist  
**Example:** "You have a syntax error on line 10" when code compiles fine  
**Fix:** Run real tools and include their output

### ❌ Harsh Tone Instructions
**Problem:** Students feel discouraged and stop trying  
**Example:** "Point out all mistakes" vs "Celebrate progress"  
**Fix:** Explicitly instruct encouraging, supportive tone

### ❌ No Format Template
**Problem:** Inconsistent, hard-to-read feedback  
**Example:** Sometimes bullets, sometimes prose, random length  
**Fix:** Provide exact structure with word limits

---

## Advanced Patterns

### Conditional Logic Based on Analysis

```yaml
prompt: |
  {% if steps.syntax-check.outputs.errors > 0 %}
  PRIORITY: Syntax errors detected. Focus on compilation first:
  - Explain each error in student-friendly terms
  - Show exactly where the problem is
  - Provide working example
  {% else %}
  Code compiles successfully! Focus on learning:
  - Code style and organization
  - Logic and efficiency 
  - Best practices for beginners
  {% endif %}
```

### Dynamic Difficulty Adjustment

```yaml
prompt: |
  Analyze student history and adjust difficulty:
  
  Previous PRs: {{ previous_pr_count }}
  
  {% if previous_pr_count < 3 %}
  This appears to be a new student. Focus on:
  - Building confidence with positive feedback
  - Basic concepts only
  - Encouraging experimentation
  
  {% elif previous_pr_count < 10 %}
  Intermediate student. Focus on:
  - Reinforcing good habits they've developed
  - Introducing next-level concepts gradually
  - Specific code quality improvements
  
  {% else %}
  Experienced student. Focus on:
  - Advanced best practices
  - Code efficiency and optimization
  - Preparing for next course level
  {% endif %}
```

### Language-Specific Adaptation

```yaml
prompt: |
  ## Language Detection and Adaptation
  Files changed: {{ changed_files }}
  
  {% for file in changed_files %}
  {% if file.endswith('.py') %}
  Python file detected: {{ file }}
  Focus areas:
  - Indentation and PEP 8 compliance
  - Pythonic idioms and best practices
  - Error handling with try/except
  
  {% elif file.endswith('.cpp') %}
  C++ file detected: {{ file }}
  Focus areas:
  - Compilation and syntax correctness
  - Memory management awareness
  - Standard library usage
  {% endif %}
  {% endfor %}
```

---

## Layer Checklist

Use this checklist when writing prompts:

### Context Layer ✓
- [ ] Student identifier included
- [ ] Course name specified
- [ ] Current week/module stated
- [ ] Topics to avoid listed
- [ ] Prior submission count (if available)

### Data Layer ✓
- [ ] Compilation results included
- [ ] Linter/style output included
- [ ] Test results (if applicable)
- [ ] File change statistics
- [ ] Relevant code snippets

### Pedagogical Layer ✓
- [ ] Priority stated (learning vs. perfection)
- [ ] Tone explicitly described
- [ ] Concept limit specified (1-3)
- [ ] Skill level indicated
- [ ] Conditional guidance for different scenarios

### Format Layer ✓
- [ ] Exact structure template provided
- [ ] Word/length limit specified
- [ ] Emoji usage defined
- [ ] Example format shown

---

## Related Resources

- [Architecture Diagram](./architecture_diagram.md) - System overview
- [Starter Templates](./templates/) - Ready-to-use workflow files
- [Original Developer's Guide](./Developers_Guide__Building_Educational_AI_Workflows.pdf) - Full documentation
