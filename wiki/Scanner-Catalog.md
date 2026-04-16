# Scanner Catalog

DarkLead runs **19 static analysis tools** in parallel. Each tool is wrapped in a standardized MCP (Model Context Protocol) scanner class that normalizes output to a common finding schema.

---

## Finding Schema (all tools)

```json
{
  "line": 42,
  "severity": "critical|major|minor|info",
  "category": "security|quality|performance|maintainability",
  "rule": "B602",
  "message": "subprocess call with shell=True",
  "tool": "bandit",
  "file_path": "app/utils.py"
}
```

After LLM triage, findings also get:
- `explanation` — why this matters in context
- `cwe` — CWE identifier (e.g., `CWE-78`)
- `owasp` — OWASP 2021 category (e.g., `A03:2021`)
- `fix_suggestion` — AI-generated code fix

---

## Python Scanners

### bandit
**Purpose:** Python security vulnerability detection  
**What it finds:** B-codes — shell injection, SQL injection, hardcoded secrets, weak crypto, XML/YAML attacks, `eval()`/`exec()`, insecure deserialization  
**Key rules:** B601 (paramiko exec), B602 (subprocess shell=True), B103 (chmod unsafe), B501 (TLS verify=False), B324 (MD5/SHA1)  
**Severity mapping:** HIGH→critical, MEDIUM→major, LOW→minor

### ruff
**Purpose:** Python linting — PEP 8 + 700+ rules  
**What it finds:** F-codes (undefined vars, unused imports), E-codes (style), W-codes (warnings), C90 (complexity), security rules  
**Speed:** 10-100x faster than flake8; runs in milliseconds  
**Severity mapping:** All findings → minor (style/quality)

### lizard
**Purpose:** Cyclomatic complexity analysis  
**What it finds:** Functions with CC > 10 (major), CC > 20 (critical)  
**Multi-language:** Python, JavaScript, TypeScript, Java, C/C++, Go, Ruby  
**Output:** Function name, start line, CC value

### radon
**Purpose:** Python maintainability metrics  
**What it finds:** Maintainability Index (A–F), Halstead complexity  
**Thresholds:** MI < 20 = critical, MI < 65 = major

### vulture
**Purpose:** Dead code detection  
**What it finds:** Unused functions, classes, variables, imports  
**Confidence:** Reports confidence % for each finding

---

## Secret & Credential Scanners

### gitleaks
**Purpose:** Git history secret scanning  
**What it finds:** API keys, tokens, passwords, PEM keys committed in git history  
**Modes:** Scans entire git history, not just current state  
**Rules:** 150+ built-in patterns (AWS, GitHub, Stripe, Slack, GCP, etc.)

### detect-secrets
**Purpose:** Entropy-based secret detection  
**What it finds:** High-entropy strings that look like secrets  
**Advantage:** Catches novel/custom secret formats that pattern rules miss

### DarkLead Secret Scanner (built-in)
**Purpose:** Fast pre-LLM regex secret gate  
**Patterns:** API keys, hardcoded passwords, AWS AKIA keys, GitHub PATs (`ghp_`), OpenAI/Anthropic keys (`sk-`), PEM headers, bearer tokens  
**Speed:** < 1ms per file

---

## Dependency Scanners

### pip-audit
**Purpose:** Python dependency vulnerability scanning  
**Data source:** PyPI Advisory Database + OSV.dev  
**What it finds:** Known CVEs in installed packages with CVSS scores

### npm audit
**Purpose:** Node.js dependency vulnerability scanning  
**Data source:** npm Security Advisory database  
**What it finds:** CVEs in package.json dependencies and devDependencies

### trivy
**Purpose:** Container + filesystem vulnerability scanning  
**What it finds:** OS package CVEs, language runtime CVEs, Docker image vulnerabilities  
**Data source:** NVD, GitHub Security Advisories, OS vendor advisories

### osv-scanner
**Purpose:** Open Source Vulnerability cross-ecosystem scanner  
**What it finds:** Vulnerabilities across PyPI, npm, Go, Rust, Maven, NuGet  
**Data source:** OSV.dev database (aggregates NVD + ecosystem DBs)

---

## Infrastructure / Config Scanners

### checkov
**Purpose:** Terraform + CloudFormation + Kubernetes IaC scanning  
**What it finds:** 2000+ security misconfigurations in IaC templates  
**Coverage:** AWS, GCP, Azure, Kubernetes, Docker, GitHub Actions

### tfsec
**Purpose:** Terraform-specific security scanner  
**What it finds:** Terraform HCL misconfigs — unencrypted S3, public RDS, open security groups  
**Speed:** Faster and more Terraform-focused than checkov

### hadolint
**Purpose:** Dockerfile linter  
**What it finds:** Dockerfile anti-patterns, security issues, best practice violations  
**Rules:** DL3000–DL4000 series (60+ rules)

### DarkLead Config Auditor (built-in)
**Purpose:** YAML + .env misconfiguration detection  
**What it finds:** debug=True, weak passwords, ALLOWED_HOSTS=*, TLS disabled  
**Languages:** YAML, JSON, .env files

### env-checker (built-in)
**Purpose:** Environment variable secret detection  
**What it finds:** Hardcoded secrets in .env files, docker-compose.yml, CI config

---

## Multi-Language Scanners

### semgrep
**Purpose:** Pattern-based SAST for 30+ languages  
**What it finds:** OWASP Top 10 patterns, framework-specific vulnerabilities, custom rules  
**Rules:** Uses `p/owasp-top-ten`, `p/python`, `p/javascript` rulesets

### ESLint (security plugins)
**Purpose:** JavaScript/TypeScript static analysis  
**What it finds:** `eslint-plugin-security` rules — unsafe regex, path traversal, prototype pollution  
**Coverage:** Node.js, React, Vue, TypeScript

---

## Java Scanners

### PMD
**Purpose:** Java static code analysis  
**What it finds:** Null pointer dereferences, resource leaks, dead code, complexity  
**Coverage:** Java, Apex, PLSQL

### SpotBugs
**Purpose:** Java bytecode analysis  
**What it finds:** Bug patterns in compiled bytecode — FindBugs successor  
**Coverage:** Java, Kotlin, Scala (via plugin)

---

## Scanner Results Merging

After all 19 scanners run, results are merged with deduplication:

```python
# Deduplication key: (line_number, rule_id)
seen = set()
for finding in all_findings:
    key = (finding['line'], finding['rule'])
    if key not in seen:
        merged.append(finding)
        seen.add(key)
```

Then sorted by severity: `critical → major → minor → info`

---

## Adding a New Scanner

1. Create `backend/app/mcp/scanners/my_tool.py`:
```python
class MyToolScanner:
    async def run(self, repo_path: str, language: str) -> list[dict]:
        result = subprocess.run(['mytool', '--json', repo_path], ...)
        return self._parse(result.stdout)
    
    def _parse(self, output: str) -> list[dict]:
        return [{"line": r["line"], "severity": "major", 
                 "rule": r["id"], "message": r["msg"], "tool": "mytool"}
                for r in json.loads(output)]
```

2. Register in `backend/app/mcp/orchestrator.py`:
```python
from .scanners.my_tool import MyToolScanner
SCANNERS.append(MyToolScanner())
```

3. Add to health check in `backend/app/routes/health.py`
