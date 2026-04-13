
"""Export endpoint — JSON / HTML / SARIF report formats."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
import json
from ..database import SessionLocal
from ..models import Job

router = APIRouter(prefix='/export', tags=['export'])

def _get_job(db, job_id: str):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, 'Job not found')
    return job

@router.get('/{job_id}/json')
async def export_json(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        return JSONResponse(content={'job_id': job_id, 'grade': job.grade,
                                     'score': job.debt_score, 'issues': job.issue_count})
    finally:
        db.close()

@router.get('/{job_id}/sarif')
async def export_sarif(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        sarif = {
            'version': '2.1.0',
            '$schema': 'https://json.schemastore.org/sarif-2.1.0.json',
            'runs': [{'tool': {'driver': {'name': 'DarkLead', 'version': '1.0.0',
                                          'informationUri': 'https://github.com/thw01f/Zero'}},
                      'results': []}]
        }
        return JSONResponse(content=sarif, headers={'Content-Disposition': f'attachment; filename=darklead-{job_id[:8]}.sarif'})
    finally:
        db.close()

@router.get('/{job_id}/html')
async def export_html(job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id)
        html = f'<html><body><h1>DarkLead Report</h1><p>Grade: {job.grade}</p></body></html>'
        return HTMLResponse(content=html)
    finally:
        db.close()
