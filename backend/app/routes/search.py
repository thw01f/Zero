"""Full-text search across scan findings."""
from fastapi import APIRouter, Query
from ..database import SessionLocal
from ..models import Issue, Job

router = APIRouter(prefix='/search', tags=['search'])


@router.get('/findings')
async def search_findings(
    q: str = Query(..., min_length=2, description='Search query'),
    severity: str | None = None,
    limit: int = Query(50, le=200),
):
    db = SessionLocal()
    try:
        query = db.query(Issue, Job).join(Job, Issue.job_id == Job.id)
        query = query.filter(
            Issue.message.ilike(f'%{q}%') | Issue.rule_id.ilike(f'%{q}%')
        )
        if severity:
            query = query.filter(Issue.severity == severity)
        rows = query.limit(limit).all()
        return {
            'results': [
                {
                    'job_id': job.id,
                    'repo_url': job.repo_url,
                    'severity': issue.severity,
                    'rule': issue.rule_id,
                    'message': issue.message,
                    'file_path': issue.file_path,
                    'line_start': issue.line_start,
                }
                for issue, job in rows
            ],
            'total': len(rows),
            'query': q,
        }
    finally:
        db.close()
