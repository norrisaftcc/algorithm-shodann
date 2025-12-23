# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SHODANN (Simple, Heuristically Operated, Dynamically Adversarial Neural Network) is an AI-powered educational feedback system that provides automated code review with a distinctive satirical persona. It operates within AlgoCratic Futures, a corporate dystopia framework that teaches real software development skills through immersive fiction.

**Core Innovation**: SHODANN measures *learning velocity* (rate of improvement) rather than absolute skill. A student who improves from terrible to mediocre is celebrated more than one who remains consistently good.

## Architecture

The system combines **hard analysis** (linters, compilers, test runners) with **soft analysis** (LLM interpretation) through a GitHub Actions workflow:

```
Student PR → GitHub Actions → Hard Analysis → Velocity Calculation → LLM Synthesis → PR Comment
```

Key components:
- **Hard Analysis**: py_compile, flake8, pytest, bandit (security), radon (complexity)
- **Velocity Calculation**: Measures rate of change (dy/dx), not absolute position
- **4-Layer Prompt Structure**: Context → Data → Pedagogical → Format
- **RAGE STATE**: Security audit mode triggered randomly (10%), by opt-in, or by unresolved security debt

## Repository Structure

- `design_docs/` - Current design specifications and planning documents
  - `SHODANN_CLAUDE.md` - Comprehensive project reference
  - `SHODANN_VOICE_GUIDE.md` - Persona and tone reference
  - `RAGE_STATE.md` - Security audit mode documentation
  - `shodann-architecture-prototype/` - Prototype documents and architecture diagrams

## The Persona

SHODANN is the benevolent AI voice of "The Algorithm" - helpful but performs mild menace for comedic effect. The name inverts SHODAN from System Shock: actually benevolent while *performing* mild menace.

**Voice Vocabulary**:
| Never Say | Always Say |
|-----------|------------|
| Wrong | Suboptimal |
| Mistake | Growth opportunity |
| Failed | Pre-success state |
| Bad code | Algorithm-misaligned |
| You should | The Algorithm suggests |

**Clearance Levels** (student progression): INFRARED → RED → ORANGE → YELLOW → GREEN → BLUE+

## Key Constraints

- **Growth frame**: Always celebrate improvement over absolute position
- **Response length**: Under 400 words total
- **Concept focus**: 1-3 concepts maximum per review
- **Never punitive**: RAGE STATE is "excessively helpful," never mean
- **Human priority**: Break character if a student is genuinely struggling
