#!/usr/bin/env python3
"""Seed a complete demo job for jury presentation."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import uuid, datetime
os.environ.setdefault("ANTHROPIC_API_KEY", "demo")

from app.database import engine, SessionLocal
from app.models import Base, Job, Issue, Module, Misconfig, DepUpdate, Advisory, ComplianceResult, StatusEnum

Base.metadata.create_all(bind=engine)
db = SessionLocal()

JOB_ID = "demo-darklead-" + str(uuid.uuid4())[:8]

# Job
job = Job(
    id=JOB_ID,
    repo_url="https://github.com/demo/vulnerable-app",
    language="python",
    status=StatusEnum.complete,
    progress=100,
    scan_time_ms=18432,
    overall_debt_score=62.4,
    overall_grade="C",
    summary_narrative=(
        "The repository presents significant security and maintainability concerns that require immediate attention. "
        "Eight critical vulnerabilities have been identified, predominantly SQL injection and hardcoded secrets, "
        "posing direct exploitation risk in production environments. The overall debt score of 62.4 (Grade C) "
        "reflects accumulated technical debt across authentication, data handling, and configuration modules.\n\n"
        "Top priority remediation actions: First, address the three SQL injection vulnerabilities in "
        "auth/db_utils.py immediately — these represent direct data breach risk and are trivially exploitable. "
        "Second, rotate all hardcoded API keys found in config.py and migrate to environment variables. "
        "Third, update six dependencies with known CVEs, particularly requests 2.25.1 which has a critical "
        "SSRF vulnerability fixed in 2.31.0.\n\n"
        "On the positive side, the test coverage for the core payment module is exemplary at 94%, "
        "and the authentication module's overall structure follows modern patterns despite the SQL injection issues."
    ),
    completed_at=datetime.datetime.utcnow(),
)
db.add(job)

# Issues
issues_data = [
    ("auth/db_utils.py", 42, 45, "critical", "security", "B608", "SQL injection via string concatenation in login query", "bandit", "A03:2021-Injection", "CWE-89", "User-controlled input is concatenated directly into a SQL query, enabling complete database compromise.", "--- a/auth/db_utils.py\n+++ b/auth/db_utils.py\n@@ -42,3 +42,3 @@\n-    query = f\"SELECT * FROM users WHERE email='{email}' AND password='{password}'\"\n+    query = \"SELECT * FROM users WHERE email=? AND password=?\"\n+    cursor.execute(query, (email, password))"),
    ("auth/db_utils.py", 87, 90, "critical", "security", "B608", "SQL injection in user search endpoint", "bandit", "A03:2021-Injection", "CWE-89", "Same SQL injection pattern in user search — all user records at risk.", None),
    ("config.py", 12, 12, "critical", "secret", "aws-access-key", "Hardcoded AWS access key detected", "gitleaks", "A02:2021-Cryptographic Failures", "CWE-259", "AWS credentials committed to source control — rotate immediately.", None),
    ("config.py", 15, 15, "critical", "secret", "generic-api-key", "Hardcoded API key for payment processor", "gitleaks", "A02:2021-Cryptographic Failures", "CWE-259", "Payment processor API key in plaintext — any repo access means full payment API access.", None),
    ("api/upload.py", 23, 28, "critical", "security", "path-traversal", "Path traversal in file upload handler", "semgrep", "A01:2021-Broken Access Control", "CWE-22", "User-supplied filename is used directly in file path construction without sanitization.", "--- a/api/upload.py\n+++ b/api/upload.py\n@@ -23,3 +23,4 @@\n-    file_path = os.path.join(UPLOAD_DIR, filename)\n+    filename = os.path.basename(filename)  # strip any path components\n+    file_path = os.path.join(UPLOAD_DIR, filename)"),
    ("auth/jwt_handler.py", 8, 8, "critical", "security", "B105", "Hardcoded JWT secret key", "bandit", "A02:2021-Cryptographic Failures", "CWE-321", "JWT tokens signed with a hardcoded secret can be forged by anyone who reads the source.", None),
    ("api/admin.py", 55, 58, "critical", "security", "missing-auth", "Admin endpoint has no authentication check", "semgrep", "A07:2021-Identification Failures", "CWE-306", "The /admin/users endpoint returns all user data without verifying the caller is an admin.", None),
    ("utils/crypto.py", 3, 3, "critical", "security", "B303", "Use of MD5 for password hashing", "bandit", "A02:2021-Cryptographic Failures", "CWE-327", "MD5 is cryptographically broken — passwords can be cracked in seconds with GPU rainbow tables.", "--- a/utils/crypto.py\n+++ b/utils/crypto.py\n@@ -3,2 +3,3 @@\n-import hashlib\n-return hashlib.md5(password.encode()).hexdigest()\n+import bcrypt\n+return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()"),
    ("api/user.py", 34, 40, "major", "security", "B601", "Shell injection risk in subprocess call", "bandit", "A03:2021-Injection", "CWE-78", "User input passed to subprocess.run with shell=True enables arbitrary command execution.", None),
    ("api/user.py", 67, 70, "major", "security", "xss-reflected", "Reflected XSS in error message", "semgrep", "A03:2021-Injection", "CWE-79", "User input echoed in HTML response without escaping — enables script injection.", None),
    ("models/user.py", 89, 95, "major", "debt", "CCN_HIGH", "Function 'validate_user_input' has cyclomatic complexity 18", "lizard", None, None, "This function has too many branches — split into smaller, testable validation functions.", None),
    ("services/email.py", 12, 12, "major", "security", "B501", "SMTP connection without TLS verification", "bandit", "A02:2021-Cryptographic Failures", "CWE-295", "Email credentials and content sent over unverified TLS — susceptible to MITM attacks.", None),
    ("requirements.txt", 0, 0, "major", "dep", "CVE-2023-32681", "requests 2.25.1 — SSRF via Proxy-Authorization header leak (CVSS 6.1)", "trivy", "A06:2021-Vulnerable Components", "CWE-918", "Update to requests>=2.31.0 to fix proxy credential leakage.", None),
    ("requirements.txt", 0, 0, "major", "dep", "CVE-2022-40897", "setuptools 57.0.0 — ReDoS vulnerability (CVSS 7.5)", "pip-audit", "A06:2021-Vulnerable Components", "CWE-1333", "Update setuptools to >=65.5.1 to fix regex denial-of-service.", None),
    ("api/auth.py", 45, 52, "major", "security", "B104", "Binding to 0.0.0.0 exposes service on all interfaces", "bandit", "A05:2021-Security Misconfiguration", "CWE-605", "Consider binding to localhost only unless external access is intentional.", None),
    ("utils/helpers.py", 78, 95, "major", "debt", "CCN_HIGH", "Function 'process_request' has cyclomatic complexity 16", "lizard", None, None, "Refactor into smaller single-responsibility functions to improve testability.", None),
    ("services/payment.py", 34, 34, "minor", "smell", "E501", "Line too long (142 > 88 characters)", "ruff", None, None, "Break this line for readability.", None),
    ("utils/helpers.py", 12, 12, "minor", "debt", "dead-code", "Unused function 'format_legacy_date'", "vulture", None, None, "Remove dead code to reduce cognitive overhead.", None),
    ("models/product.py", 23, 23, "minor", "smell", "F401", "Imported but unused: 'datetime'", "ruff", None, None, "Remove the unused import.", None),
]

for (fp, ls, le, sev, cat, rid, msg, tool, owasp, cwe, expl, fix_diff) in issues_data:
    db.add(Issue(
        id=str(uuid.uuid4()), job_id=JOB_ID,
        file_path=fp, line_start=ls, line_end=le,
        severity=sev, category=cat, rule_id=rid, message=msg, tool=tool,
        owasp_category=owasp, cwe_id=cwe, llm_explanation=expl, fix_diff=fix_diff,
    ))

# Modules
modules_data = [
    ("auth/db_utils.py", 280, 8.4, 18.0, 0.8, 78.2, "F", 2, 3, 4),
    ("config.py", 95, 2.1, 5.0, 0.3, 72.1, "F", 2, 1, 2),
    ("api/upload.py", 145, 5.2, 12.0, 0.5, 58.3, "C", 1, 2, 3),
    ("api/admin.py", 210, 6.8, 14.0, 0.6, 55.1, "C", 1, 2, 2),
    ("utils/crypto.py", 67, 3.4, 8.0, 0.2, 51.2, "C", 1, 1, 1),
    ("api/user.py", 334, 7.1, 16.0, 0.7, 44.8, "B", 0, 2, 3),
    ("models/user.py", 189, 9.2, 18.0, 0.4, 38.5, "B", 0, 1, 2),
    ("services/payment.py", 445, 4.1, 9.0, 0.9, 22.1, "B", 0, 0, 1),
    ("tests/test_auth.py", 290, 2.8, 6.0, 0.3, 12.4, "A", 0, 0, 0),
    ("services/email.py", 156, 3.6, 8.0, 0.4, 19.8, "A", 0, 1, 1),