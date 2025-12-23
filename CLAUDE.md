# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start: Working on an Issue

```bash
# 1. Check open issues
gh issue list --state open

# 2. View a specific issue
gh issue view <number>

# 3. Work on the issue, then create a PR when done
```

**Blocking Dependencies**: Issue #9 (Python vs JavaScript decision) blocks #10, #11, #12. Check issue labels for `status: blocked` before starting.

---

## Project Overview

**SHODANN** (Simple, Heuristically Operated, Dynamically Adversarial Neural Network) is an AI-powered educational feedback system that provides automated code review with a distinctive satirical persona.

**Core Innovation**: Measures *learning velocity* (rate of improvement, dy/dx) rather than absolute skill. A student improving from 0% to 30% coverage is celebrated more than one maintaining 90%.

**Parent Project**: AlgoCratic Futures - a satirical corporate dystopia framework for teaching software development.

---

## Development Workflow

### GitHub Issues Are Source of Truth

All work should flow through GitHub issues:
1. **Find an issue** - `gh issue list --state open`
2. **Check dependencies** - Look for `status: blocked` label
3. **Work in a branch** - `git checkout -b feature/issue-XX-description`
4. **Reference the issue** - In commits and PR: "Addresses #XX" or "Closes #XX"
5. **Create PR** - Use the PR template, link the issue

### Available Agents

This project uses specialized Claude Code agents for different tasks:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `scrum-architect-owner` | Product decisions, acceptance criteria | Planning features, writing user stories |
| `product-architect-advisor` | Architecture guidance, trade-offs | Design decisions, technology choices |
| `kevin-github-algorithm` | GitHub infrastructure, PR/issue compliance | Labels, templates, process enforcement |
| `test-engineer` | Test strategy, test implementation | Writing tests, coverage analysis |
| `clive-prompt-strategist` | Prompt engineering | Refining 4-layer prompts |
| `linx-wordsmith` | Voice and tone refinement | SHODANN persona consistency |
| `liza-creative-companion` | Creative brainstorming | New features, memorable moments |
| `Explore` | Codebase exploration | Finding files, understanding structure |

**Invoke agents via the Task tool** when their specialty matches your need.

### Current Open Issues

Priority order:
1. **#9** - Decision: Python vs JavaScript (BLOCKING - resolve first)
2. **#14** - Design State Management Schema (can proceed)
3. **#10** - Implement Core GitHub Actions Workflow (blocked by #9)
4. **#11** - Implement Velocity Calculation Engine (blocked by #9)
5. **#12** - Implement RAGE STATE Security Mode (blocked by #9)
6. **#15, #16** - Documentation tasks
7. **#17** - Branch protection (infrastructure)

---

## Architecture

### 5-Job Workflow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHODANN WORKFLOW PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│  Job 1: INITIALIZE    → Citizen lookup, RAGE STATE, history     │
│  Job 2: HARD ANALYSIS → Syntax, style, tests, coverage          │
│  Job 3: VELOCITY CALC → Delta computation, growth detection     │
│  Job 4: LLM SYNTHESIS → 4-layer prompt, Gemini API, formatting  │
│  Job 5: PERSISTENCE   → Update state, regenerate leaderboard    │
└─────────────────────────────────────────────────────────────────┘
```

### Hybrid Analysis Philosophy

| Hard Analysis | Soft Analysis |
|---------------|---------------|
| Linters, compilers, test runners | LLM interpretation |
| Produces factual data | Produces pedagogical framing |
| Cannot hallucinate | Can contextualize and encourage |

**Why both?** Hard tools provide ground truth. Soft analysis transforms facts into educational moments.

### 4-Layer Prompt Structure

Every SHODANN response is generated from a prompt with 4 layers:

1. **Context Layer** - Who is the student? (clearance, history, week)
2. **Data Layer** - What did tools find? (syntax, style, coverage, tests)
3. **Pedagogical Layer** - How should AI teach? (growth focus, vocabulary)
4. **Format Layer** - What structure? (sections, word limits, emojis)

See `prompts/` directory for templates.

---

## Repository Structure

```
algorithm-shodann/
├── CLAUDE.md                    # This file - start here
├── PRD.md                       # Product Requirements Document
├── README.md                    # Public project description
│
├── design_docs/                 # Design specifications
│   ├── SHODANN_CLAUDE.md        # Comprehensive project reference
│   ├── SHODANN_VOICE_GUIDE.md   # Persona and tone reference
│   ├── RAGE_STATE.md            # Security audit mode docs
│   └── shodann-architecture-prototype/  # Original prototypes
│
├── prompts/                     # 4-layer prompt templates
│   ├── README.md                # Prompt architecture overview
│   ├── 01_base_shodann_prompt.md
│   ├── 02_rage_state_addon.md
│   ├── 03_clearance_variations.md
│   ├── 04_first_submission_prompt.md
│   ├── 05_edge_case_handlers.md
│   └── 06_assembled_example.md  # Complete assembled example
│
└── .github/                     # GitHub configuration
    ├── ISSUE_TEMPLATE/          # 4 issue templates
    └── PULL_REQUEST_TEMPLATE.md
```

### Key Reference Files

| Need to understand... | Read this file |
|----------------------|----------------|
| Overall project scope | `PRD.md` |
| Technical architecture | `design_docs/SHODANN_CLAUDE.md` |
| SHODANN's voice/persona | `design_docs/SHODANN_VOICE_GUIDE.md` |
| RAGE STATE behavior | `design_docs/RAGE_STATE.md` |
| Prompt structure | `prompts/README.md` |
| Complete prompt example | `prompts/06_assembled_example.md` |

---

## The SHODANN Persona

SHODANN is the benevolent AI voice of "The Algorithm" - helpful but performs mild menace for comedic effect. The name inverts SHODAN from System Shock: actually benevolent while *performing* mild menace.

### Mandatory Vocabulary

| NEVER Say | ALWAYS Say |
|-----------|------------|
| Wrong | Suboptimal |
| Mistake | Growth opportunity |
| Failed | Pre-success state |
| Error | Unexpected behavior pattern |
| Bad code | Algorithm-misaligned |
| You should | The Algorithm suggests |

### Clearance Levels

Student progression through the system:

| Level | Technical Skill | SHODANN Adapts |
|-------|-----------------|----------------|
| INFRARED | Complete beginner | Maximum encouragement |
| RED | Junior | Building confidence |
| ORANGE | Mid-level | Professional concepts |
| YELLOW | Senior | Architecture, optimization |
| GREEN | Lead | Mentorship framing |
| BLUE+ | Strategic | Peer-level discourse |

### Voice Modes

- **Normal Mode**: Startup-positive, growth-focused ("Shipping velocity: OPTIMAL 🚀")
- **RAGE STATE**: Excessively helpful about security ("The Algorithm has taken a special interest...")
- **First Submission**: Extra welcoming, baseline establishment

---

## Key Constraints

When implementing or modifying SHODANN:

1. **Growth frame always** - Celebrate improvement over absolute position
2. **Response length** - Under 400 words total
3. **Concept focus** - 1-3 concepts maximum per review
4. **Never punitive** - RAGE STATE is "concerningly helpful," never mean
5. **Human priority** - Break character if student is genuinely struggling
6. **Iteration positive** - Never suggest fewer commits; celebrate iteration

---

## State Management

State stored in repository (no external database):

```
.shodann/
├── citizens/
│   └── {username}.json    # Per-citizen metrics history
├── clearances.json        # Citizen → clearance mapping
├── security_debt.json     # Outstanding security findings
└── config.json            # System configuration
```

**Note**: At scale (100+ concurrent submissions), file-based state may need locking. For MVP, atomic writes with retry logic suffice.

---

## Technology Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Orchestration | GitHub Actions | Native, free tier |
| LLM | Gemini API | Cost-effective, edu-friendly |
| Analysis | Python tools | flake8, pytest, bandit, radon |
| State | JSON files | Human-readable, git-friendly |
| Language | **TBD** (Issue #9) | Leaning Python for pedagogy |

---

## Common Tasks

### Starting Work on an Issue

```bash
# 1. See what's available
gh issue list --state open

# 2. Read the issue details
gh issue view 14

# 3. Create a branch
git checkout -b feature/issue-14-state-schema

# 4. Do the work...

# 5. Commit referencing the issue
git commit -m "Implement state schema - Addresses #14"

# 6. Push and create PR
git push -u origin feature/issue-14-state-schema
gh pr create --fill
```

### Adding a New Prompt Template

1. Create file in `prompts/` following naming convention
2. Follow 4-layer structure (see `01_base_shodann_prompt.md`)
3. Update `prompts/README.md` index
4. Test with sample data

### Modifying SHODANN's Voice

1. Reference `design_docs/SHODANN_VOICE_GUIDE.md` for guidelines
2. Maintain vocabulary substitutions (never "wrong," always "suboptimal")
3. Keep responses under 400 words
4. Ensure clearance-appropriate complexity

---

## Session Checklist

When starting a Claude Code session on this project:

- [ ] Read this file (CLAUDE.md)
- [ ] Check open issues: `gh issue list --state open`
- [ ] Identify blocking dependencies (Issue #9 blocks many)
- [ ] Pick an unblocked issue to work on
- [ ] Create branch, work, PR
- [ ] Reference issue numbers in commits and PR

---

## Links

- **GitHub Issues**: Track all work here
- **PRD.md**: Product scope and requirements
- **design_docs/**: Detailed specifications
- **prompts/**: Template library

*"The Algorithm provides. The Algorithm watches. The Algorithm helps you ship."*
