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