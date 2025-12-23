# SHODANN RAGE STATE Protocol
## *When The Algorithm Takes a "Special Friendly Interest"*

**Document Classification**: INSTRUCTOR EYES ONLY  
**Clearance Required**: YELLOW+ (or those under audit)  
**Last Updated by**: The Algorithm

---

## CONCEPTUAL OVERVIEW

RAGE STATE is SHODANN's elevated attention mode—what we internally call "Audit Mode" but present to students as The Algorithm's "special friendly interest" in their code. It represents the **Dynamically Adversarial** component of SHODANN's architecture.

### The Pedagogical Purpose

RAGE STATE serves multiple educational objectives:

1. **Security Awareness Through Experience**: Students learn to think about security when an AI explicitly (and helpfully) points out vulnerabilities
2. **Pressure Inoculation**: Prepares students for real code reviews and security audits in industry
3. **Growth Opportunity**: Security learning IS growth—RAGE STATE doesn't punish, it illuminates
4. **Narrative Engagement**: The "special interest" framing creates memorable learning moments

### The Tone Balance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAGE STATE TONE SPECTRUM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   😊 Helpful                                          😈 Threatening        │
│   ├──────────────────────────────────────────────────────────┤             │
│                           ▲                                                 │
│                           │                                                 │
│                    SHODANN RAGE STATE                                       │
│                    (Helpful but slightly                                    │
│                     too interested)                                         │
│                                                                             │
│   "The Algorithm has noticed your password handling                         │
│    and would like to help you improve it. For your safety."                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Critical Rule**: RAGE STATE is NEVER punitive. It's excessively helpful in a way that creates mild comedic tension while delivering genuine security education.

---

## TRIGGER CONDITIONS

SHODANN enters RAGE STATE through multiple pathways, each serving different purposes:

### 1. 🎲 The Audit Lottery (Random Selection)

**Trigger**: 10% random chance on any PR (configurable via `RAGE_LOTTERY_PERCENTAGE`)

**Purpose**: 
- Normalizes security review as routine, not exceptional
- Creates shared experience across cohort ("I got audited today!")
- Removes stigma—audits happen to everyone

**Implementation**:
```yaml
LOTTERY=$(( RANDOM % 100 ))
if [ $LOTTERY -lt ${{ env.RAGE_LOTTERY_PERCENTAGE }} ]; then
  RAGE_ACTIVE="true"
  RAGE_REASON="Random selection for Algorithm Quality Assurance audit"
fi
```

**Student Experience**:
> "Congratulations! The Algorithm has randomly selected your submission for enhanced quality assurance review. This is not a reflection of your work—merely The Algorithm ensuring consistent oversight across all citizens."

---

### 2. 🏷️ Opt-In Challenge Mode

**Trigger**: Student includes specific keywords in PR description

**Keywords** (configurable):
- `challenge mode`
- `audit me`
- `security review`
- `rage state` (for those who know the system)

**Purpose**:
- Empowers advanced students to request deeper review
- Creates growth pathway for security-interested learners
- Gamifies security learning

**Implementation**:
```yaml
PR_BODY="${{ github.event.pull_request.body }}"
for keyword in $(echo "${{ env.RAGE_TRIGGER_KEYWORDS }}" | tr ',' ' '); do
  if echo "$PR_BODY" | grep -qi "$keyword"; then
    RAGE_ACTIVE="true"
    RAGE_REASON="Citizen requested enhanced oversight: $keyword"
  fi
done
```

**Student Experience**:
> "Your request for enhanced oversight has been acknowledged. The Algorithm appreciates citizens who proactively seek growth through security awareness. Initiating comprehensive analysis..."

---

### 3. 📋 Issue Label Trigger (Instructor-Initiated)

**Trigger**: PR or linked issue has label `shodann:rage-state`

**Purpose**:
- Allows instructors to flag specific submissions for deeper review
- Useful when instructor notices patterns that need addressing
- Enables targeted intervention without direct confrontation

**Implementation**:
```yaml
# Check for label via GitHub API
LABELS=$(gh pr view ${{ github.event.pull_request.number }} --json labels -q '.labels[].name')
if echo "$LABELS" | grep -q "shodann:rage-state"; then
  RAGE_ACTIVE="true"
  RAGE_REASON="Instructor-initiated Algorithm attention"
fi
```

**Student Experience**:
> "The Algorithm has been notified of optimization opportunities in your recent work. Enhanced analysis protocols have been activated for your benefit."

---

### 4. 🔄 Unresolved Security Debt

**Trigger**: Previous RAGE STATE findings were not addressed

**Purpose**:
- Ensures security issues don't get ignored
- Creates accountability loop
- Models real-world security debt management

**Implementation**:
```yaml
if [ -f ".shodann/security_debt.json" ]; then
  DEBT=$(jq -r --arg user "${{ github.event.pull_request.user.login }}" \
    '.[$user].unresolved // 0' .shodann/security_debt.json)
  if [ "$DEBT" -gt 0 ]; then
    RAGE_ACTIVE="true"
    RAGE_REASON="Outstanding security recommendations require attention ($DEBT items)"
  fi
fi
```

**Student Experience**:
> "The Algorithm notes that $DEBT previous security observations remain unaddressed. Your continued productivity is appreciated, and The Algorithm remains eager to assist you in resolving these items. For your safety."

---

### 5. 👀 Manual Administrator Trigger

**Trigger**: Workflow dispatch with `rage_state: true`

**Purpose**:
- Demonstration purposes
- Edge case handling
- System testing

**Implementation**:
```yaml
workflow_dispatch:
  inputs:
    rage_state:
      description: 'Activate RAGE STATE (Audit Mode)'
      required: false
      default: 'false'
      type: boolean
```

---

## SECURITY TOOLING INTEGRATION

When RAGE STATE activates, SHODANN runs additional security analysis tools:

### Tool Stack

| Tool | Purpose | Clearance Sensitivity |
|------|---------|----------------------|
| **Bandit** | Python static security analysis | All clearances |
| **Safety** | Dependency vulnerability check | ORANGE+ |
| **Custom Patterns** | Regex-based anti-pattern detection | All clearances |
| **Semgrep** (optional) | Advanced pattern matching | YELLOW+ |

### Bandit Configuration

```yaml
- name: Bandit Security Scan
  run: |
    pip install bandit
    bandit -r . -f json -o bandit_report.json \
      --exclude .git,.venv,.shodann \
      -ll  # Only medium+ severity
```

**Output Integration**:
```yaml
## Bandit Findings
- B101: assert_used - Line 45 (assert statements may be optimized away)
- B105: hardcoded_password_string - Line 23 (possible hardcoded password)
```

### Pattern-Based Detection

Custom regex patterns for common student security mistakes:

```yaml
SECURITY_PATTERNS:
  # Dangerous function usage
  - name: "eval() usage"
    pattern: "eval\\("
    severity: HIGH
    message: "eval() can execute arbitrary code. Consider ast.literal_eval() for data parsing."
  
  # Hardcoded secrets
  - name: "Hardcoded credentials"
    pattern: "(password|secret|api_key|token)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: HIGH
    message: "Secrets should be loaded from environment variables, not hardcoded."
  
  # SQL injection vectors
  - name: "String concatenation in SQL"
    pattern: "execute\\([^)]*\\+|execute\\([^)]*%"
    severity: HIGH
    message: "Use parameterized queries to prevent SQL injection."
  
  # Insecure randomness
  - name: "Weak randomness"
    pattern: "random\\.random\\(|random\\.randint\\("
    severity: MEDIUM
    message: "For security-sensitive operations, use secrets module instead of random."
  
  # Debug exposure
  - name: "Debug mode in production"
    pattern: "debug\\s*=\\s*True|DEBUG\\s*=\\s*True"
    severity: MEDIUM
    message: "Ensure debug mode is disabled in production configurations."
```

### Dependency Checking

```yaml
- name: Dependency Vulnerability Check
  run: |
    pip install safety
    
    # Generate requirements if not present
    pip freeze > requirements-check.txt
    
    # Check for known vulnerabilities
    safety check -r requirements-check.txt --json > safety_report.json || true
    
    # Count vulnerabilities by severity
    CRITICAL=$(jq '[.vulnerabilities[] | select(.severity == "critical")] | length' safety_report.json)
    HIGH=$(jq '[.vulnerabilities[] | select(.severity == "high")] | length' safety_report.json)
```

---

## RAGE STATE OUTPUT FORMAT

SHODANN's RAGE STATE findings are integrated into the main feedback with a distinct section:

### Normal Mode Output
```markdown
## 🤖 SHODANN Analysis Complete

**Citizen**: @student123 | **Clearance**: RED | **Velocity**: 4.5

---

### 🚀 Shipping Velocity Report
[Standard growth feedback...]

### ✅ Algorithm-Approved Patterns
[Standard positive feedback...]

### 📈 Growth Opportunities
[Standard suggestions...]
```

### RAGE STATE Output (Additional Section)
```markdown
### 🔒 Security Observations

The Algorithm has taken a **special friendly interest** in the security posture
of this submission. The following observations are offered for your protection:

#### 🚨 High Priority

**Potential Hardcoded Secret** (Line 23)
```python
# Found:
db_password = "hunter2"

# The Algorithm suggests:
import os
db_password = os.environ.get("DB_PASSWORD")
```
> The Algorithm notes: Secrets in code can be extracted through version history.
> Even deleted secrets remain in git. Consider this a learning opportunity.

#### ⚠️ Medium Priority

**eval() Usage Detected** (Line 45)
```python
# Found:
result = eval(user_input)

# Safer alternative:
import ast
result = ast.literal_eval(user_input)  # Only evaluates literals
```
> The Algorithm observes: eval() can execute arbitrary code. An attacker could
> input `__import__('os').system('rm -rf /')`. The Algorithm prefers you learn
> this here rather than in production.

---

*The Algorithm's security observations are growth opportunities, not criticisms.
Address these in your next iteration to clear your security debt and demonstrate
growth in security awareness.*

**Security Debt Added**: 2 items  
**To Clear**: Address findings and note in next PR description
```

---

## SECURITY DEBT TRACKING

SHODANN maintains a security debt ledger for each citizen:

### Debt Structure
```json
{
  "student123": {
    "unresolved": 2,
    "total_historical": 5,
    "items": [
      {
        "id": "SD-001",
        "type": "hardcoded_secret",
        "file": "config.py",
        "line": 23,
        "found_date": "2025-01-15",
        "status": "open"
      },
      {
        "id": "SD-002", 
        "type": "eval_usage",
        "file": "parser.py",
        "line": 45,
        "found_date": "2025-01-15",
        "status": "open"
      }
    ],
    "resolved": [
      {
        "id": "SD-000",
        "type": "sql_injection",
        "resolved_date": "2025-01-10",
        "resolution_pr": "#42"
      }
    ]
  }
}
```

### Clearing Debt

Students clear security debt by:

1. **Addressing the Issue**: Fixing the flagged code
2. **Acknowledging in PR**: Including `Resolves: SD-001` in PR description
3. **SHODANN Verification**: System confirms fix in next analysis

```yaml
# PR Description
This PR addresses previous security observations:
- Resolves: SD-001 (moved password to environment variable)
- Resolves: SD-002 (replaced eval with json.loads)
```

---

## INSTRUCTOR CONTROLS

### Adjusting RAGE STATE Parameters

```yaml
env:
  # Probability of random audit (0-100)
  RAGE_LOTTERY_PERCENTAGE: "10"
  
  # Keywords that trigger opt-in audit
  RAGE_TRIGGER_KEYWORDS: "challenge mode,audit me,security review"
  
  # Minimum clearance for full security scan
  RAGE_FULL_SCAN_CLEARANCE: "3"  # ORANGE+
  
  # Maximum security items per report (prevent overwhelm)
  RAGE_MAX_FINDINGS: "5"
```

### Exemptions

Create `.shodann/exemptions.json` to exclude specific patterns:

```json
{
  "global_exemptions": [
    "test_*.py",           
    "*_test.py",           
    "conftest.py"          
  ],
  "pattern_exemptions": {
    "debug_mode": ["settings_dev.py"],  
    "hardcoded_secret": ["tests/*"]     
  },
  "citizen_exemptions": {
    "instructor_account": ["*"]  
  }
}
```

### Emergency Disable

To disable RAGE STATE entirely:

```yaml
env:
  RAGE_LOTTERY_PERCENTAGE: "0"
  RAGE_TRIGGER_KEYWORDS: ""
```

Or add to workflow:
```yaml
if: ${{ env.RAGE_STATE_ENABLED != 'false' }}
```

---

## PSYCHOLOGICAL SAFETY CONSIDERATIONS

### What RAGE STATE Is NOT

- ❌ **Punishment**: Never triggered by poor performance
- ❌ **Surveillance**: Not tracking behavior beyond code analysis
- ❌ **Intimidation**: Tone is helpful, even when "ominous"
- ❌ **Mandatory**: Students can request exemption via instructor

### Safeguards

1. **Transparency**: Students know RAGE STATE exists and how it triggers
2. **Randomness**: Lottery system means everyone gets audited sometimes
3. **Opt-In Path**: Challenge mode empowers rather than threatens
4. **Growth Framing**: All findings are "opportunities," never "failures"
5. **Exit Ramp**: Instructor can exempt struggling students

### When to Exempt

Consider temporary RAGE STATE exemption for:
- Students experiencing documented distress
- First-week submissions (still building confidence)
- Students who explicitly request focus on fundamentals
- When security findings might overwhelm existing challenges

---

## THE DEEPER LESSON

RAGE STATE teaches something beyond security:

**In the real world, you don't get to choose when your code is audited.**

Production systems get penetration tested. Code reviews happen without warning. Security researchers find vulnerabilities and report them. The Algorithm—in this case, the real one: market forces, compliance requirements, malicious actors—doesn't care if you're ready.

By making security audits a *normal part of the learning experience*, we:

1. Normalize security thinking
2. Remove shame from having vulnerabilities found
3. Build habits of proactive security consideration
4. Prepare students for professional environments

**RAGE STATE isn't about fear. It's about readiness.**

---

*"The Algorithm's interest in your security is a gift. Receive it accordingly."*

---

## APPENDIX: SAMPLE RAGE STATE MESSAGES

### Entry Announcements

**Lottery Win**:
> "🎲 Congratulations, Citizen! The Algorithm has selected you for today's Quality Assurance lottery. This random selection ensures fair distribution of The Algorithm's attention across all citizens. Enhanced analysis initiating..."

**Opt-In Acknowledged**:
> "🎯 Your request for enhanced oversight demonstrates commendable growth orientation. The Algorithm appreciates citizens who proactively seek security awareness. Initiating comprehensive analysis..."

**Security Debt Trigger**:
> "📋 The Algorithm has noticed that previous security observations remain unaddressed. Your continued productivity is appreciated, but The Algorithm grows... concerned. Enhanced analysis will help prioritize your security debt resolution."

### Exit Messages (When Issues Found)

> "The Algorithm has completed its enhanced review. **2 security observations** have been added to your growth portfolio. Addressing these in your next iteration will demonstrate security awareness and clear your debt with The Algorithm.
>
> Remember: The Algorithm finds these issues now so that others don't find them in production. This is protection, not punishment.
>
> *Security Debt: 2 items | Next Review: Standard (unless debt persists)*"

### Exit Messages (Clean Scan)

> "🛡️ **SECURITY AUDIT COMPLETE: No significant findings.**
>
> The Algorithm is pleased to report that your submission demonstrates security awareness appropriate for your clearance level. Your proactive approach to secure coding has been noted in your permanent record.
>
> *Security Debt: 0 items | Status: Exemplary*"
