"""User profile management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
from .auth import get_current_user, require_user, hash_password, verify_password
import datetime

router = APIRouter(prefix="/profile", tags=["profile"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_color: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/")
async def get_profile(current_user: User = Depends(require_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "avatar_color": current_user.avatar_color,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
        "initials": _get_initials(current_user),
    }


@router.patch("/")
async def update_profile(req: UpdateProfileRequest, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.username is not None:
        existing = db.query(User).filter(User.username == req.username, User.id != user.id).first()
        if existing:
            raise HTTPException(400, "Username already taken")
        user.username = req.username
    if req.avatar_color is not None:
        user.avatar_color = req.avatar_color
    user.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "username": user.username,
            "full_name": user.full_name, "avatar_color": user.avatar_color,
            "initials": _get_initials(user)}


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    user = db.query(User).filter(User.id == current_user.id).first()
    user.hashed_password = hash_password(req.new_password)
    user.updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/stats")
async def get_user_stats(current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    from ..models import Job
    total_scans = db.query(Job).count()
    return {"total_scans": total_scans, "member_since": current_user.created_at.isoformat(),
            "role": current_user.role}


def _get_initials(user: User) -> str:
    if user.full_name:
        parts = user.full_name.strip().split()
        return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][1] if len(parts[0]) > 1 else '')).upper()
    return user.username[:2].upper()
