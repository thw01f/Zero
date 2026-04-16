
"""Aggregate statistics endpoint."""
from fastapi import APIRouter
from sqlalchemy import func
from ..database import SessionLocal
from ..models import Job, Issue

router = APIRouter(prefix='/stats', tags=['stats'])

@router.get('/overview')
async def overview():
    db = SessionLocal()
    try:
        total_jobs = db.query(func.count(Job.id)).scalar() or 0
        total_issues = db.query(func.count(Issue.id)).scalar() or 0
        grade_dist = {}
        for row in db.query(Job.grade, func.count(Job.id)).group_by(Job.grade).all():
            grade_dist[row[0] or 'N/A'] = row[1]
        avg_score = db.query(func.avg(Job.debt_score)).scalar() or 0
        critical = db.query(func.count(Issue.id)).filter(Issue.severity == 'critical').scalar() or 0
        return {'total_scans': total_jobs, 'total_issues': total_issues,
                'grade_distribution': grade_dist, 'avg_debt_score': round(float(avg_score), 1),
                'critical_issues': critical}
    finally:
        db.close()

@router.get('/trends')
async def trends():
    db = SessionLocal()
    try:
        jobs = db.query(Job.created_at, Job.debt_score, Job.grade).order_by(Job.created_at).limit(30).all()
        return {'points': [{'date': str(j.created_at)[:10], 'score': j.debt_score, 'grade': j.grade} for j in jobs]}
    finally:
        db.close()
