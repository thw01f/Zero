# Scoring Formula

DarkLead produces a **Debt Score** (0–100, higher is better) and a **Letter Grade** (A–F) for every scanned repository.

---

## Score Formula

```
Debt Score = 100 − penalty

penalty = (critical × 15) + (major × 8) + (minor × 2) + (info × 0.5)
          + (misconfigs × 5)
          + (outdated_deps × 3)
          + (complexity_penalty)
          + (no_tests_penalty)

Clamped to [0, 100]
```

### Penalty Weights

| Finding Type | Penalty per item |
|-------------|-----------------|
| Critical severity | 15 points |
| Major severity | 8 points |
| Minor severity | 2 points |
| Info | 0.5 points |
| Misconfiguration | 5 points |
| Outdated dependency with CVE | 3 points |
| Cyclomatic complexity > 20 | 2 points per function |
| No test files detected | 5 points flat |

### Complexity Penalty

```python
for fn in high_complexity_functions:
    if fn.cc > 20:
        penalty += 2
    elif fn.cc > 10:
        penalty += 0.5
```

---

## Grade Thresholds

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| **A** | 90–100 | Excellent — minimal issues, production-ready |
| **B** | 75–89 | Good — some minor issues to address |
| **C** | 55–74 | Fair — moderate debt, needs attention |
| **D** | 35–54 | Poor — significant issues, not recommended for production |
| **F** | 0–34 | Critical — severe vulnerabilities, immediate remediation required |

### Grade Color Coding

```
A → #3ecf8e (green)
B → #4a9ff5 (blue)
C → #f5a623 (amber)
D → #f26d21 (orange)
F → #f25555 (red)
```

---

## Priority Score

Each individual finding also gets a **Priority Score** (0–100) for the remediation queue:

```python
priority = (
    SEVERITY_WEIGHT[severity]        # critical=40, major=25, minor=10, info=2
  + CATEGORY_WEIGHT[category]        # security=30, quality=10, performance=8
  + (15 if in_owasp_top10 else 0)    # OWASP bonus
  + (10 if has_cwe else 0)           # CWE bonus
  + (5 if has_fix else 0)            # Fixable items prioritized
)
clamped to [0, 100]
```

This drives the ordering in the FixStudio remediation queue — highest priority = highest ROI fix first.

---

## Examples

### Grade F — 2 lines of code

```python
import subprocess
subprocess.run(cmd, shell=True)
password = 'admin123'
```

- bandit: B602 (critical, shell=True), B105 (major, hardcoded password)
- ruff: S603 (minor)
- LLM: 3 additional security findings

Penalty: `15 + 8 + 2 + 2 + 2 = 29` → Score: `max(0, 100 - 29) = 71`... actually:

The demo snippet from the Code Analyzer:
- Score: 20, Grade: F (8 findings from bandit+ruff+lizard+LLM combined)

### Grade A — clean utility module

Well-structured Python with:
- Parameterized queries
- No hardcoded secrets
- Input validation
- Type hints
- Test coverage

Penalty: `0` → Score: `100` → Grade: `A`

---

## Module-Level Scoring

Each module (api/, models/, utils/, etc.) also gets its own debt score:

```python
module_score = 100 - sum(
    SEVERITY_WEIGHT[issue.severity]
    for issue in module_issues
)
```

Module scores feed the Heatmap treemap — area = LOC, color = severity of worst finding.

---

## Debt Trend

When a repository is scanned multiple times (e.g., via webhook on every push), DarkLead tracks debt score over time. The Trend Analysis view shows:

- Score trajectory (improving / declining / stable)
- New issues introduced vs issues fixed
- Grade history
