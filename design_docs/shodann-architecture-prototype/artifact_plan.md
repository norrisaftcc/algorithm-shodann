# Educational Artifact Plan: Building Educational AI Workflows

## Overview

This plan outlines a series of educational artifacts designed to help college software developers understand and implement AI-powered educational automation systems using GitHub Actions + Gemini CLI.

---

## Target Audience Profile

- **Who**: College-level software developers (CS students, junior developers, teaching assistants)
- **Prerequisites**: Basic Git/GitHub knowledge, familiarity with YAML, introductory programming experience
- **Goals**: Understand AI-assisted code review, implement educational workflows, adapt prompts for different contexts

---

## Artifact Roadmap

### Phase 1: Conceptual Foundation

| # | Artifact | Format | Purpose |
|---|----------|--------|---------|
| 1 | **System Architecture Diagram** | Interactive React/Mermaid | Visual overview of how GitHub Actions + Gemini CLI + Prompts work together |
| 2 | **Core Concepts Explainer** | Markdown document | Define key terms: workflow, trigger, prompt layer, pedagogical feedback |
| 3 | **"Why This Matters" Infographic** | SVG/React | Compare traditional code review vs. AI-augmented educational feedback |

### Phase 2: Technical Deep-Dives

| # | Artifact | Format | Purpose |
|---|----------|--------|---------|
| 4 | **Workflow Anatomy Breakdown** | Interactive React component | Step-through visualization of a PR review workflow with annotations |
| 5 | **Prompt Engineering Cheatsheet** | PDF/Markdown | The 4-layer prompt structure with templates and examples |
| 6 | **YAML Workflow Builder** | Interactive React tool | Drag-and-drop or guided workflow creation with live preview |

### Phase 3: Hands-On Implementation

| # | Artifact | Format | Purpose |
|---|----------|--------|---------|
| 7 | **Starter Template Collection** | GitHub-ready YAML files | Copy-paste workflows for Python, JavaScript, Java courses |
| 8 | **Customization Cookbook** | Markdown guide | Recipes for adapting workflows to different course types |
| 9 | **Security & Privacy Checklist** | Interactive checklist | FERPA compliance, API key management, student data protection |

### Phase 4: Advanced Topics

| # | Artifact | Format | Purpose |
|---|----------|--------|---------|
| 10 | **Scaling Guide** | Markdown + diagrams | From single course to institution-wide deployment |
| 11 | **Analytics Dashboard Mock** | React component | What metrics to track and how to visualize learning outcomes |
| 12 | **Troubleshooting Decision Tree** | Interactive flowchart | Common issues and their solutions |

---

## Detailed Artifact Specifications

### Artifact 1: System Architecture Diagram

**Goal**: Provide mental model of the entire system in one view

**Key Elements**:
- Student action triggers (PR open, push, comment)
- GitHub Actions runner activation
- Pre-processing tools (linters, compilers)
- Gemini API call with prompt
- Response formatting and delivery

**Interactivity**: 
- Click nodes to expand details
- Hover for tooltips explaining each component
- Toggle between "simple" and "detailed" views

---

### Artifact 4: Workflow Anatomy Breakdown

**Goal**: Deep understanding of what each YAML section does

**Structure**:
```
┌─────────────────────────────────────────────┐
│  TRIGGER SECTION                            │
│  ├── Event type (pull_request)              │
│  ├── Activity types (opened, synchronize)   │
│  └── Path filters (**.py)                   │
├─────────────────────────────────────────────┤
│  PRE-PROCESSING SECTION                     │
│  ├── Checkout code                          │
│  ├── Run syntax checker                     │
│  └── Capture tool outputs                   │
├─────────────────────────────────────────────┤
│  AI INTEGRATION SECTION                     │
│  ├── Load Gemini Action                     │
│  ├── Inject context variables               │
│  └── Execute prompt with layered structure  │
├─────────────────────────────────────────────┤
│  OUTPUT SECTION                             │
│  └── Post comment to PR                     │
└─────────────────────────────────────────────┘
```

---

### Artifact 5: Prompt Engineering Cheatsheet

**The Four Layers**:

1. **Context Layer** 🎯
   - Student identifier
   - Course/week information  
   - Current learning objectives
   - *Why*: Calibrates difficulty appropriately

2. **Data Layer** 📊
   - Compilation results
   - Linter output
   - File change statistics
   - *Why*: Grounds AI in concrete facts

3. **Pedagogical Layer** 🎓
   - Tone instructions (encouraging)
   - Focus areas (1-3 concepts max)
   - Skill level specification
   - *Why*: Ensures teaching mindset

4. **Format Layer** 📝
   - Response structure template
   - Section headers
   - Emoji conventions
   - *Why*: Consistent, scannable feedback

---

### Artifact 7: Starter Template Collection

**Templates to Include**:

| Template | Use Case | Key Features |
|----------|----------|--------------|
| `python-intro.yml` | Intro to Python courses | Syntax focus, PEP 8 basics |
| `python-ds.yml` | Data Structures course | Complexity analysis, container choice |
| `web-dev.yml` | Web development | HTML/CSS/JS, accessibility checks |
| `team-project.yml` | Software engineering | Git practices, code review, documentation |
| `multi-lang.yml` | Advanced courses | Language detection, cross-language feedback |

---

### Artifact 9: Security & Privacy Checklist

**Categories**:

- [ ] **API Key Management**
  - [ ] Keys stored in GitHub Secrets
  - [ ] Monthly rotation scheduled
  - [ ] Access limited to necessary repos

- [ ] **Student Privacy (FERPA)**
  - [ ] No grades in AI prompts
  - [ ] Student IDs hashed in analytics
  - [ ] Personal info stripped from code

- [ ] **Data Handling**
  - [ ] Code not stored beyond analysis
  - [ ] Audit logging enabled
  - [ ] Clear data retention policy

---

## Implementation Priority

### 🔴 High Priority (Create First)
1. System Architecture Diagram - Essential mental model
2. Prompt Engineering Cheatsheet - Most actionable takeaway
3. Starter Template Collection - Immediate practical value

### 🟡 Medium Priority
4. Workflow Anatomy Breakdown - Deepens understanding
5. Customization Cookbook - Enables adaptation
6. Security Checklist - Critical for deployment

### 🟢 Lower Priority (Create Later)
7. YAML Workflow Builder - Nice-to-have tool
8. Scaling Guide - Advanced topic
9. Analytics Dashboard - Future enhancement

---

## Success Metrics

An artifact is successful if a developer can:

1. **Architecture Diagram**: Explain the system to a peer in 2 minutes
2. **Prompt Cheatsheet**: Write a new 4-layer prompt without reference
3. **Templates**: Deploy a working workflow in under 30 minutes
4. **Security Checklist**: Pass a compliance review for their institution

---

## Next Steps

1. **Immediate**: Create the System Architecture Diagram (interactive React)
2. **Then**: Build the Prompt Engineering Cheatsheet (PDF-ready markdown)
3. **Then**: Develop starter templates with extensive comments

Ready to proceed with Artifact #1?
