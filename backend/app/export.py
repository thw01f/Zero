import csv
import io
import json
from .models import Job, Issue, Module, Misconfig, DepUpdate, ComplianceResult
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