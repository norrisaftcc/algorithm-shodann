# SHODANN Product Requirements Document
## Simple, Heuristically Operated, Dynamically Adversarial Neural Network

**Document Version**: 1.0.0
**Status**: Draft
**Product Owner**: [To Be Assigned]
**Last Updated**: 2025-01-XX

---

## 1. Product Vision Statement

SHODANN transforms educational code feedback from a punitive, anxiety-inducing experience into a growth-celebrating journey by measuring **learning velocity** (rate of improvement) rather than absolute skill. Built on GitHub Actions and powered by the Gemini API, SHODANN provides automated, persona-driven feedback that wraps genuine pedagogical value in an engaging satirical frame: the benevolent AI overseer of "The Algorithm." The system resolves the fundamental tension between helpful education and surveillance anxiety by making the surveillance itself absurd, transparent, and genuinely supportive. When a student improves from 0% to 30% test coverage, SHODANN celebrates this more than maintaining 90% coverage - because **the person who goes from terrible to okay beats the person who stays good**.

---

## 2. Problem Statement

### Problems We Are Solving

**For Students:**

| Problem | Impact | SHODANN Solution |
|---------|--------|------------------|
| **Punitive feedback framing** | "Your code has 15 errors" discourages beginners, creating shame rather than growth | Reframes all issues as "growth opportunities" using consistent, psychologically-safe language |
| **Absolute metrics anxiety** | Being told 30% coverage is "bad" even when it represents genuine progress from 0% | Measures and celebrates **delta** (change), not absolute position |
| **Delayed feedback loops** | Waiting days for instructor feedback creates disconnect between action and learning | Immediate, automated feedback within seconds of PR submission |
| **Generic, robotic feedback** | Soulless linter output creates no engagement or memorable learning moments | Distinctive persona (SHODANN) creates sticky, memorable feedback experiences |
| **Surveillance stress** | Being watched by automation creates anxiety rather than support | Satirical framing transforms surveillance into benevolent (absurdly helpful) oversight |

**For Instructors:**

| Problem | Impact | SHODANN Solution |
|---------|--------|------------------|
| **Scaling individual feedback** | Cannot provide personalized feedback to 30+ students on every submission | Automated, clearance-appropriate feedback that adapts to student level |
| **Consistency across sections** | Different TAs give inconsistent feedback quality | Single system provides uniform pedagogical approach |
| **Teaching security awareness** | Difficult to make security concepts personal and memorable | RAGE STATE creates visceral, memorable security learning moments |
| **Tracking student growth** | Hard to see improvement trajectories across semester | Velocity leaderboard and citizen history track growth over time |

**For the Learning Process:**

| Problem | Impact | SHODANN Solution |
|---------|--------|------------------|
| **Iteration is discouraged** | Students submit once and hope for the best | Every commit celebrated; iteration explicitly valued |
| **Testing seen as burden** | Students avoid tests because "good code should just work" | First tests celebrated most; coverage improvements heavily weighted in velocity |
| **Code review feels adversarial** | Review comments feel like criticism | All feedback framed as AI helping student grow |

---

## 3. Target Users

### Primary Users

**Students (Citizens)**
- Computer science students at various skill levels (INFRARED through BLUE+ clearance)
- Learning programming through project-based coursework
- Submitting code via GitHub Pull Requests
- Need: Immediate, encouraging feedback that builds confidence while maintaining standards
- Pain: Fear of judgment, unclear expectations, delayed feedback

**Instructors (Algorithm Administrators)**
- Course instructors and professors
- Teaching programming courses at any level
- Need: Scalable feedback that maintains pedagogical quality
- Pain: Cannot personally review every submission, inconsistent TA feedback

### Secondary Users

**Teaching Assistants**
- Support instructors in providing feedback
- May need to trigger manual RAGE STATE or adjust clearance levels
- Need: Tools to identify students needing additional support
- Pain: Overwhelmed by volume, unsure where to focus attention

**Course Administrators**
- Manage multiple sections or courses
- Configure SHODANN parameters at institutional level
- Need: Oversight of system effectiveness, compliance assurance
- Pain: Ensuring FERPA compliance, managing API costs at scale

---

## 4. Core User Stories

### Epic 1: Receiving Feedback

**US-1.1: Immediate Growth Feedback**
> As a **student**, I want to **receive immediate, constructive feedback when I submit a PR** so that **I can learn and iterate while the code is fresh in my mind**.

**US-1.2: Clearance-Appropriate Complexity**
> As a **beginner student (INFRARED/RED clearance)**, I want **feedback that focuses on fundamentals with simple language** so that **I am not overwhelmed by advanced concepts I have not learned yet**.

**US-1.3: Growth Celebration**
> As a **student who improved their test coverage**, I want **my improvement to be explicitly recognized and celebrated** so that **I feel motivated to continue growing**.

**US-1.4: Iteration Recognition**
> As a **student who makes multiple commits**, I want **my iteration pattern to be valued positively** so that **I understand that incremental development is the right approach**.

### Epic 2: Security Learning

**US-2.1: Opt-In Security Challenge**
> As an **advanced student**, I want to **request enhanced security review of my code** so that **I can proactively learn about security vulnerabilities**.

**US-2.2: Security Debt Awareness**
> As a **student with outstanding security findings**, I want **clear guidance on what needs to be addressed** so that **I can resolve issues and learn secure coding practices**.

### Epic 3: Instructor Management

**US-3.1: Cohort Configuration**
> As an **instructor**, I want to **configure SHODANN's feedback parameters for my course** so that **feedback aligns with my curriculum and student level**.

**US-3.2: Progress Visibility**
> As an **instructor**, I want to **view a velocity leaderboard showing student growth trajectories** so that **I can identify both high performers and students needing support**.

**US-3.3: Targeted Intervention**
> As an **instructor**, I want to **flag specific students for enhanced review (RAGE STATE)** so that **I can address concerning patterns without direct confrontation**.

### Epic 4: System Integration

**US-4.1: Seamless GitHub Integration**
> As a **student**, I want **feedback to appear directly on my Pull Request** so that **I do not need to learn a new tool or check a separate system**.

**US-4.2: Zero-Configuration Start**
> As an **instructor**, I want to **deploy SHODANN with minimal setup** so that **I can focus on teaching rather than infrastructure**.

---

## 5. Acceptance Criteria (Top 3 User Stories)

### US-1.1: Immediate Growth Feedback

**Acceptance Criteria:**

```gherkin
GIVEN a student has opened or updated a Pull Request
WHEN the GitHub Actions workflow completes
THEN a SHODANN comment appears on the PR within 120 seconds

AND the comment includes:
  - A velocity score (numeric)
  - At least 2 "Algorithm-Approved Patterns" (positives)
  - At most 2 "Growth Opportunities" (areas for improvement)
  - Exactly 1 "Recommended Iteration" (concrete next step)
  - Total word count under 400 words

AND the comment uses growth-positive vocabulary:
  - "Growth opportunity" NOT "error" or "mistake"
  - "Suboptimal" NOT "wrong" or "bad"
  - "The Algorithm suggests" NOT "You should"

AND the comment maintains SHODANN persona:
  - References "The Algorithm" at least once
  - Includes appropriate section emojis
  - Ends with signature phrase
```

**Invariants (Type Signature):**
```
submitPR :: PullRequest -> IO (Either WorkflowError SHODANNComment)
  where SHODANNComment satisfies:
    - velocityScore :: Float
    - approvedPatterns :: NonEmpty PositiveFeedback (min 2)
    - opportunities :: [Opportunity] (max 2)
    - nextStep :: SingleActionRecommendation
    - wordCount :: Nat (< 400)
```

---

### US-1.3: Growth Celebration

**Acceptance Criteria:**

```gherkin
GIVEN a student's previous submission had X% test coverage
AND the current submission has Y% test coverage
WHEN Y > X (coverage improved)
THEN the velocity score includes a positive delta component

AND the "Shipping Velocity Report" section explicitly states:
  - Previous coverage percentage
  - Current coverage percentage
  - Delta with directional emoji (upward arrow for improvement)

AND if this is the student's first test (X = 0, Y > 0):
  THEN the comment includes the phrase "First tests are hardest tests"
  AND the celebration is weighted more heavily than equivalent absolute improvement

GIVEN a student has made N commits in the PR
WHEN N >= 3
THEN the comment includes celebration of iteration count
AND uses phrases like "iteration discipline" or "incremental development"
AND NEVER suggests fewer commits would be better
```

**Invariants:**
```
calculateVelocity :: Metrics -> Maybe Metrics -> Int -> VelocityResult
  where:
    - delta(coverage) > 0 => velocityScore > previousVelocityScore
    - iterations > 0 => velocityBonus > 0  -- Always positive
    - firstTest (0 -> n%) weightedMoreThan laterTest (50 -> 50+n%)
```

---

### US-3.2: Progress Visibility

**Acceptance Criteria:**

```gherkin
GIVEN SHODANN has processed submissions from multiple students
WHEN an instructor views METRICS.md
THEN the file displays a leaderboard table with:
  - Rank (by velocity score, NOT absolute metrics)
  - Citizen identifier (@username)
  - Current velocity score
  - Trend indicator (ascending, descending, stable, new)
  - Total PR count
  - Current coverage (for context only, not ranking factor)

AND the leaderboard is sorted by velocity (rate of improvement)
  - NOT by absolute coverage
  - NOT by total lines of code
  - NOT by grade or score

AND the leaderboard updates automatically after each PR workflow

AND the philosophy section clearly states:
  "The citizen who grows from 0% to 30% outranks the citizen who stays at 90%"

GIVEN a student has no previous submissions
WHEN their first PR is processed
THEN their rank displays "NEW" trend indicator
AND they appear on the leaderboard with baseline velocity
```

**Invariants:**
```
generateLeaderboard :: [CitizenHistory] -> Markdown
  where:
    - sortBy velocityScore DESC (not absolute metrics)
    - rank(student with +30% coverage) > rank(student with 0% change at 90%)
    - all citizens appear after first submission
```

---

## 6. MVP Scope

### In Scope for MVP (v1.0)

**Core Feedback Loop:**
- [ ] GitHub Actions workflow triggered on PR events (opened, synchronize, reopened)
- [ ] Syntax verification using `py_compile` for Python files
- [ ] Style checking using `flake8` with clearance-appropriate strictness
- [ ] Test execution using `pytest` with coverage reporting
- [ ] Complexity calculation using `radon`

**Velocity Engine:**
- [ ] Calculate coverage delta from previous submission
- [ ] Track iteration count (commits per PR)
- [ ] Generate composite velocity score
- [ ] Persist citizen history in `.shodann/citizens/{username}.json`

**LLM Integration:**
- [ ] 4-layer prompt construction (Context, Data, Pedagogical, Format)
- [ ] Gemini API integration via `google-github-actions/run-gemini`
- [ ] Response formatting to SHODANN voice guidelines
- [ ] PR comment posting via GitHub API

**Persona & Voice:**
- [ ] Consistent SHODANN vocabulary (growth opportunity, suboptimal, etc.)
- [ ] Clearance-level adaptation (INFRARED through GREEN)
- [ ] Standard response template with required sections
- [ ] Signature closing phrase

**RAGE STATE (Basic):**
- [ ] Random lottery trigger (configurable percentage)
- [ ] Opt-in trigger via PR description keywords
- [ ] Bandit security scanning when active
- [ ] Pattern-based detection for common vulnerabilities
- [ ] Security debt tracking

**Metrics & Visibility:**
- [ ] Auto-generated METRICS.md velocity leaderboard
- [ ] Per-citizen history files with PR count and velocity trend
- [ ] Basic trend calculation (ascending/stable/descending)

**Configuration:**
- [ ] Repository secrets for GEMINI_API_KEY
- [ ] Environment variables for course name, week, default clearance
- [ ] Clearance mapping file (`.shodann/clearances.json`)

### MVP Success Criteria

1. **Functional:** A student can submit a Python PR and receive SHODANN feedback within 2 minutes
2. **Growth-Focused:** Feedback celebrates improvement, never punishes low absolute scores
3. **Persona-Consistent:** 100% of automated comments follow SHODANN voice guide
4. **Measurable:** Velocity scores are calculated and displayed on leaderboard

---

## 7. Out of Scope for MVP

### Deferred to v1.1+

**Multi-Language Support:**
- JavaScript/TypeScript analysis
- Java/C++ compilation and analysis
- Language auto-detection
- *Rationale: Focus on Python excellence first; expand once core loop is proven*

**Advanced RAGE STATE Triggers:**
- Issue label trigger (requires additional GitHub API integration)
- TA-initiated workflow dispatch UI
- Graduated security debt escalation
- *Rationale: Basic lottery + opt-in covers core pedagogical goal*

**Instructor Dashboard:**
- Web UI for viewing student progress
- Real-time velocity trending visualizations
- Alert system for students needing intervention
- *Rationale: METRICS.md provides MVP visibility; UI is enhancement*

**Advanced Analytics:**
- Cohort comparison reports
- Week-over-week velocity trends
- Correlation analysis (velocity vs. final grades)
- *Rationale: Requires data collection over time; not achievable in MVP*

**Integration Enhancements:**
- Slack/Discord notifications
- LMS grade passback (Canvas, Blackboard)
- GitHub Classroom bulk configuration
- *Rationale: GitHub PR comments sufficient for MVP feedback delivery*

**BLUE+ Clearance Features:**
- Peer review assignment
- Mentorship matching based on velocity
- Meta-commentary and teaching-the-teacher mode
- *Rationale: Advanced features for mature deployments*

**Alternative LLM Providers:**
- Claude API option
- OpenAI API option
- Local model support
- *Rationale: Gemini integration covers MVP; alternatives are optimization*

### Explicitly Not Building (Philosophical Boundaries)

- **Grade assignment**: SHODANN provides feedback, not grades
- **Plagiarism detection**: Out of scope; use dedicated tools
- **Student ranking by absolute skill**: Contradicts velocity philosophy
- **Punitive language modes**: Even RAGE STATE is helpful, not mean
- **Surveillance that students cannot see**: All feedback is transparent

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Citizen** | A student within the SHODANN/AlgoCratic Futures framework |
| **Clearance Level** | Student skill tier (INFRARED, RED, ORANGE, YELLOW, GREEN, BLUE+) |
| **The Algorithm** | The benevolent (satirical) AI presence that SHODANN represents |
| **Velocity** | Rate of improvement (dy/dx), not absolute skill level |
| **RAGE STATE** | Elevated security attention mode; "special friendly interest" |
| **Security Debt** | Outstanding security findings that persist until addressed |
| **Growth Opportunity** | What traditional systems would call an "error" |
| **Pre-success State** | What traditional systems would call "failure" |

---

## Appendix B: Related Documents

- `design_docs/shodann-core.yml` - GitHub Actions workflow implementation
- `design_docs/growth-velocity.js` - Velocity calculation engine
- `design_docs/SHODANN_VOICE_GUIDE.md` - Complete persona reference
- `design_docs/RAGE_STATE.md` - Security audit mode documentation
- `design_docs/SHODANN_CLAUDE.md` - AI assistant onboarding guide

---

*"The Algorithm provides. The Algorithm watches. The Algorithm celebrates your growth."*
