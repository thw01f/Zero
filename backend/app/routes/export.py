"""Export endpoint — JSON / HTML / SARIF report formats."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import func
from ..database import SessionLocal
from ..models import Job, Issue, Module

router = APIRouter(prefix='/export', tags=['export'])


def _get_job(db, job_id: str):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, 'Job not found')
    return job


@router.get('/{job_id}/json')
async def export_json(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        modules = db.query(Module).filter(Module.job_id == job_id).all()
        return JSONResponse(content={
            'job_id': job_id,
            'repo_url': job.repo_url,
            'language': job.language,
            'grade': job.overall_grade,
            'debt_score': job.overall_debt_score,
            'scan_time_ms': job.scan_time_ms,
            'completed_at': str(job.completed_at) if job.completed_at else None,
            'summary': job.summary_narrative,
            'issue_count': len(issues),
            'issues': [
                {'id': i.id, 'file': i.file_path, 'line': i.line_start,
                 'severity': i.severity, 'rule': i.rule_id, 'message': i.message,
                 'cwe': i.cwe_id, 'owasp': i.owasp_category, 'tool': i.tool}
                for i in issues
            ],
            'modules': [
                {'path': m.path, 'language': m.language, 'loc': m.loc,
                 'debt_score': m.debt_score, 'grade': m.grade}
                for m in modules
            ],
        })
    finally:
        db.close()


@router.get('/{job_id}/sarif')
async def export_sarif(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        results = []
        for i in issues:
            results.append({
                'ruleId': i.rule_id or 'unknown',
                'level': {'critical': 'error', 'major': 'error', 'minor': 'warning', 'info': 'note'}.get(i.severity, 'note'),
                'message': {'text': i.message or ''},
                'locations': [{'physicalLocation': {
                    'artifactLocation': {'uri': i.file_path},
                    'region': {'startLine': i.line_start or 1},
                }}],
            })
        sarif = {
            'version': '2.1.0',
            '$schema': 'https://json.schemastore.org/sarif-2.1.0.json',
            'runs': [{'tool': {'driver': {'name': 'DarkLead', 'version': '1.0.0',
                                          'informationUri': 'https://github.com/thw01f/darklead'}},
                      'results': results}],
        }
        return JSONResponse(content=sarif, headers={
            'Content-Disposition': f'attachment; filename=darklead-{job_id[:8]}.sarif'
        })
    finally:
        db.close()


@router.get('/{job_id}/html')
async def export_html(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        issues = db.query(Issue).filter(Issue.job_id == job_id).all()
        sev_colors = {'critical': '#ef4444', 'major': '#f97316', 'minor': '#eab308', 'info': '#60a5fa'}
        rows = ''.join(
            f'<tr><td>{i.file_path}:{i.line_start}</td><td style="color:{sev_colors.get(i.severity,"#9ca3af")}">'
            f'{i.severity}</td><td>{i.rule_id or ""}</td><td>{i.message or ""}</td></tr>'
            for i in issues
        )
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>DarkLead Report — {job_id[:8]}</title>
<style>body{{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:24px}}
h1{{color:#58a6ff}}table{{width:100%;border-collapse:collapse;margin-top:16px}}
th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid #30363d;font-size:13px}}
th{{background:#161b22;color:#8b949e}}</style></head>
<body><h1>DarkLead Security Report</h1>
<p>Repo: {job.repo_url} &nbsp;|&nbsp; Grade: <strong>{job.overall_grade or 'N/A'}</strong>
&nbsp;|&nbsp; Debt: {job.overall_debt_score or 0:.1f} &nbsp;|&nbsp; Issues: {len(issues)}</p>
<table><thead><tr><th>Location</th><th>Severity</th><th>Rule</th><th>Message</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>"""
        return HTMLResponse(content=html, headers={
            'Content-Disposition': f'attachment; filename=darklead-{job_id[:8]}.html'
        })
    finally:
        db.close()
