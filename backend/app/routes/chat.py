from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, Issue, ChatMessage
from ..schemas import ChatRequest
from ..mcp.llm_layer import chat_stream
import uuid, datetime

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{job_id}")
async def chat(job_id: str, req: ChatRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Load history
    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(ChatMessage)
        .filter(ChatMessage.job_id == job_id)
        .order_by(ChatMessage.created_at)
        .limit(10)
        .all()
    ]

    # Relevant findings (keyword match)
    q = req.message.lower()
    issues = db.query(Issue).filter(Issue.job_id == job_id).all()
    relevant = [
        {"rule": i.rule_id, "severity": i.severity, "file": i.file_path,
         "line": i.line_start, "message": i.message}
        for i in issues
        if q in (i.message or "").lower() or q in (i.rule_id or "").lower()
    ][:5]
    if not relevant:
        relevant = [
            {"rule": i.rule_id, "severity": i.severity, "file": i.file_path, "message": i.message}
            for i in sorted(issues, key=lambda x: {"critical": 0, "major": 1}.get(x.severity, 2))[:5]
        ]

    response_text = await chat_stream(req.message, job_id, history, relevant, "")

    # Persist turns
    db.add(ChatMessage(id=str(uuid.uuid4()), job_id=job_id, role="user",
                       content=req.message, created_at=datetime.datetime.utcnow()))
    db.add(ChatMessage(id=str(uuid.uuid4()), job_id=job_id, role="assistant",
                       content=response_text, created_at=datetime.datetime.utcnow()))
    db.commit()

    return {"response": response_text}


@router.get("/{job_id}/history")
def get_history(job_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.job_id == job_id)
        .order_by(ChatMessage.created_at)
        .limit(20)
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages]
