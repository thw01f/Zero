# Database Schema

DarkLead uses SQLAlchemy with SQLite (swappable to PostgreSQL). The database is created automatically on first run.

---

## Entity Relationship

```
Project ──< Job ──< Issue
                ──< Module
                ──< Misconfiguration
                ──< ComplianceResult
                ──< DependencyUpdate
Job (advisory) ──< Advisory (scheduled, not per-job)
```

---

## Tables

### `projects`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `project_id` | String(36) UNIQUE | UUID |
| `name` | String(256) | Repo name |
| `repo_url` | String(512) | GitHub URL |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### `jobs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `job_id` | String(36) UNIQUE | UUID, used in all API endpoints |
| `project_id` | FK → projects | |
| `repo_url` | String(512) | Scanned URL |
| `branch` | String(128) | Git branch |
| `status` | Enum | `queued\|running\|completed\|failed` |
| `grade` | String(1) | `A\|B\|C\|D\|F` |
| `debt_score` | Integer | 0–100 |
| `issue_count` | Integer | Total findings |
| `summary` | Text | LLM executive summary |
| `current_step` | String(32) | Current pipeline step |
| `loc_total` | Integer | Lines of code |
| `loc_by_language` | JSON | `{"Python": 1200, "JS": 800}` |
| `module_count` | Integer | Distinct modules found |
| `misconfig_count` | Integer | Misconfiguration count |
| `created_at` | DateTime | |
| `completed_at` | DateTime | |

### `issues`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `job_id` | FK → jobs.job_id | |
| `severity` | Enum | `critical\|major\|minor\|info` |
| `category` | Enum | `security\|quality\|performance\|maintainability` |
| `rule` | String(64) | Rule ID (e.g., `B602`, `E501`) |
| `message` | Text | Short description |
| `explanation` | Text | LLM explanation |
| `file_path` | String(512) | Relative path in repo |
| `line_number` | Integer | Line number |
| `cwe` | String(16) | CWE ID (e.g., `CWE-78`) |
| `owasp` | String(16) | OWASP 2021 (e.g., `A03:2021`) |
| `fix_suggestion` | Text | AI-generated fix code |
| `tool` | String(32) | Source scanner |
| `fingerprint` | String(16) | Dedup hash |
| `priority_score` | Integer | 0–100 remediation priority |

### `modules`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `job_id` | FK → jobs.job_id | |
| `name` | String(256) | Module name (e.g., `api`, `models`) |
| `file_count` | Integer | Files in module |
| `loc` | Integer | Lines of code |
| `issue_count` | Integer | Total issues |
| `debt_score` | Integer | Module-level score |
| `category` | String(32) | `api\|models\|utils\|tests\|…` |

### `misconfigurations`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `job_id` | FK → jobs.job_id | |
| `severity` | Enum | |
| `category` | String(32) | `dockerfile\|terraform\|yaml\|env` |
| `rule` | String(64) | Rule ID |
| `message` | Text | Description |
| `file_path` | String(512) | |
| `line_number` | Integer | |
| `fix_suggestion` | Text | |

### `advisories`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `cve_id` | String(32) UNIQUE | CVE identifier |
| `severity` | Enum | |
| `cvss_score` | Float | 0.0–10.0 |
| `description` | Text | NVD description |
| `published` | DateTime | NVD publish date |
| `ecosystems` | JSON | `["Python", "npm"]` |
| `fetched_at` | DateTime | When DarkLead fetched it |

### `compliance_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | |
| `job_id` | FK → jobs.job_id | |
| `framework` | String(32) | `OWASP2021\|NIST_SP800_53` |
| `category` | String(32) | `A01:2021` or `AC-1` |
| `status` | String(16) | `pass\|fail\|partial` |
| `finding_count` | Integer | Issues in this category |

---

## Indexes

```sql
CREATE INDEX ix_jobs_job_id ON jobs(job_id);
CREATE INDEX ix_issues_job_id ON issues(job_id);
CREATE INDEX ix_issues_severity ON issues(severity);
CREATE INDEX ix_advisories_cve_id ON advisories(cve_id);
```

---

## Migrations

DarkLead uses `SQLAlchemy.create_all()` for automatic schema creation. For production schema migrations, use Alembic:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Switching to PostgreSQL

```bash
# .env
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/darklead
```

All SQLAlchemy ORM code is database-agnostic. No SQL queries are written manually.
