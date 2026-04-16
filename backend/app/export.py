import csv
import io
import json
from .models import Job, Issue, Module, Misconfig, DepUpdate, ComplianceResult, Advisory
from .database import SessionLocal


def build_report_dict(job_id: str, db) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {}

    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    modules = db.query(Module).filter(Module.job_id == job_id).all()
    misconfigs = db.query(Misconfig).filter(Misconfig.job_id == job_id).all()
    dep_updates = db.query(DepUpdate).filter(DepUpdate.job_id == job_id).all()
    compliance = db.query(ComplianceResult).filter(ComplianceResult.job_id == job_id).all()
    advisories = db.query(Advisory).order_by(Advisory.cvss_score.desc().nullslast()).limit(20).all()

    sev_counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
    cat_counts: dict = {}
    for i in issues:
        sev_counts[i.severity] = sev_counts.get(i.severity, 0) + 1
        cat_counts[i.category] = cat_counts.get(i.category, 0) + 1

    top_risks = []
    for i in sorted(issues, key=lambda x: {"critical": 0, "major": 1}.get(x.severity, 2))[:5]:
        top_risks.append(f"[{i.severity.upper()}] {i.rule_id} in {i.file_path}:{i.line_start}")

    return {
        "job_id": job_id,
        "repo_url": job.repo_url,
        "language": job.language or "unknown",
        "scan_time_ms": job.scan_time_ms or 0,
        "total_issues": len(issues),
        "issues_by_severity": sev_counts,
        "issues_by_category": cat_counts,
        "overall_debt_score": job.overall_debt_score or 0.0,
        "overall_grade": job.overall_grade or "?",
        "issues": [_issue_to_dict(i) for i in issues],
        "modules": [_module_to_dict(m) for m in modules],
        "misconfigs": [_misconfig_to_dict(m) for m in misconfigs],
        "dep_updates": [_dep_to_dict(d) for d in dep_updates],
        "compliance": [_compliance_to_dict(c) for c in compliance],
        "summary_narrative": job.summary_narrative or "",
        "top_risks": top_risks,
        "secret_count": sum(1 for i in issues if i.category == "secret"),
        "mandatory_update_count": sum(1 for d in dep_updates if d.classification == "MANDATORY"),
        "advisories": [
            {
                "advisory_id": a.advisory_id,
                "title": a.title,
                "severity": a.severity,
                "cvss_score": a.cvss_score,
                "advisory_url": a.advisory_url,
            }
            for a in advisories
        ],
        "top_cvss_score": advisories[0].cvss_score if advisories and advisories[0].cvss_score else None,
    }


def generate_issues_csv(report: dict) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "file_path", "line_start", "severity", "category", "rule_id", "message", "tool", "owasp_category", "cwe_id", "fix_accepted"
    ])
    writer.writeheader()
    for issue in report.get("issues", []):
        writer.writerow({k: issue.get(k, "") for k in writer.fieldnames})
    return output.getvalue()


def generate_pdf(report: dict) -> bytes:
    try:
        from weasyprint import HTML
        html = _build_html_report(report)
        return HTML(string=html).write_pdf()
    except Exception:
        # fallback: return JSON as bytes if weasyprint unavailable
        return json.dumps(report, indent=2).encode()


def _build_html_report(report: dict) -> str:
    grade_color = {"A": "#22c55e", "B": "#3b82f6", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}
    sev_color = {"critical": "#ef4444", "major": "#f97316", "minor": "#eab308", "info": "#6b7280"}

    issues_rows = ""
    for i in report["issues"][:50]:
        color = sev_color.get(i["severity"], "#6b7280")
        issues_rows += f"""<tr>
            <td><span style="color:{color};font-weight:bold">{i["severity"].upper()}</span></td>
            <td>{i["file_path"]}:{i["line_start"]}</td>
            <td>{i["rule_id"]}</td>
            <td>{i["message"][:80]}</td>
            <td>{i["tool"]}</td>
        </tr>"""

    module_rows = ""
    for m in report["modules"][:20]:
        gc = grade_color.get(m["grade"], "#6b7280")
        module_rows += f"""<tr>
            <td>{m["path"]}</td>
            <td><span style="color:{gc};font-weight:bold">{m["grade"]}</span></td>
            <td>{m["debt_score"]}</td>
            <td>{m["loc"]}</td>
            <td>{m["issue_count_critical"]}</td>
            <td>{m["issue_count_major"]}</td>
        </tr>"""

    grade = report.get("overall_grade", "?")
    gc = grade_color.get(grade, "#6b7280")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>DarkLead Report — {report["repo_url"]}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 40px; }}
  h1 {{ color: #7c3aed; border-bottom: 2px solid #7c3aed; padding-bottom: 8px; }}
  h2 {{ color: #a78bfa; margin-top: 32px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th {{ background: #1e293b; padding: 8px; text-align: left; color: #94a3b8; font-size: 12px; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #1e293b; font-size: 12px; }}
  .grade {{ font-size: 64px; font-weight: bold; color: {gc}; }}
  .stat {{ display: inline-block; margin: 8px 16px; text-align: center; }}
  .stat-val {{ font-size: 28px; font-weight: bold; color: #7c3aed; }}
  .stat-lbl {{ font-size: 11px; color: #64748b; }}
  .narrative {{ background: #1e293b; padding: 16px; border-radius: 8px; line-height: 1.6; }}
</style></head><body>
<h1>🔍 DarkLead Code Intelligence Report</h1>
<p style="color:#64748b">Repo: {report["repo_url"]} | Language: {report["language"]} | Scan time: {report["scan_time_ms"]}ms</p>
<div style="margin: 24px 0">
  <span class="grade">{grade}</span>
  <div class="stat"><div class="stat-val" style="color:#ef4444">{report["issues_by_severity"].get("critical",0)}</div><div class="stat-lbl">Critical</div></div>
  <div class="stat"><div class="stat-val" style="color:#f97316">{report["issues_by_severity"].get("major",0)}</div><div class="stat-lbl">Major</div></div>
  <div class="stat"><div class="stat-val" style="color:#eab308">{report["issues_by_severity"].get("minor",0)}</div><div class="stat-lbl">Minor</div></div>
  <div class="stat"><div class="stat-val">{report["total_issues"]}</div><div class="stat-lbl">Total Issues</div></div>
  <div class="stat"><div class="stat-val">{report["overall_debt_score"]}</div><div class="stat-lbl">Debt Score</div></div>
</div>
<h2>Executive Summary</h2>
<div class="narrative">{report.get("summary_narrative","")}</div>
<h2>Top Issues (showing 50)</h2>
<table><tr><th>Severity</th><th>Location</th><th>Rule</th><th>Message</th><th>Tool</th></tr>
{issues_rows}</table>
<h2>Module Debt Scores</h2>
<table><tr><th>Module</th><th>Grade</th><th>Debt Score</th><th>LOC</th><th>Critical</th><th>Major</th></tr>
{module_rows}</table>
</body></html>"""


def _issue_to_dict(i) -> dict:
    return {
        "id": i.id, "file_path": i.file_path, "line_start": i.line_start,
        "line_end": i.line_end, "severity": i.severity, "category": i.category,
        "rule_id": i.rule_id, "message": i.message, "tool": i.tool,
        "owasp_category": i.owasp_category, "cwe_id": i.cwe_id,
        "llm_explanation": i.llm_explanation, "fix_diff": i.fix_diff,
        "fix_accepted": i.fix_accepted,
    }

def _module_to_dict(m) -> dict:
    import json as _j
    counts = _j.loads(m.issue_counts or "{}") if isinstance(m.issue_counts, str) else (m.issue_counts or {})
    return {
        "id": m.id, "path": m.path, "loc": m.loc,
        "complexity_avg": m.complexity_avg, "max_complexity": m.max_complexity,
        "churn_count": m.churn_count, "debt_score": m.debt_score, "grade": m.grade,
        "issue_count_critical": counts.get("critical", 0),
        "issue_count_major":    counts.get("major", 0),
        "issue_count_minor":    counts.get("minor", 0),
    }

def _misconfig_to_dict(m) -> dict:
    return {
        "id": m.id, "tool": m.tool, "resource_type": m.resource_type,
        "file_path": m.file_path, "line_start": m.line_start,
        "check_id": m.check_id, "title": m.title,
        "severity": m.severity, "remediation": m.remediation,
    }

def _dep_to_dict(d) -> dict:
    return {
        "id": d.id, "ecosystem": d.ecosystem, "package_name": d.package_name,
        "current_version": d.current_version, "latest_version": d.latest_version,
        "classification": d.classification, "cve_ids": d.cve_ids or [],
        "changelog_summary": d.changelog_summary,
        "upgrade_command": d.upgrade_command,
    }

def _compliance_to_dict(c) -> dict:
    return {
        "framework": c.standard, "control_id": c.control_id,
        "control_name": c.control_name, "status": c.status,
        "issue_count": c.issue_count, "evidence": __import__('json').loads(c.evidence) if c.evidence else [],
    }
