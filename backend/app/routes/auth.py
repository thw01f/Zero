"""JWT authentication routes."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
import uuid, os

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "darklead-dev-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode() if isinstance(hashed, str) else hashed)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def require_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user


# Schemas
class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    avatar_color: str
    role: str
    created_at: datetime


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already taken")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    colors = ["#1a73e8","#e8710a","#1e8e3e","#d93025","#a142f4","#007b83"]
    import random
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        username=req.username,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        avatar_color=random.choice(colors),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "username": user.username,
                     "full_name": user.full_name, "avatar_color": user.avatar_color, "role": user.role}}


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == form.username) | (User.username == form.username)
    ).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "username": user.username,
                     "full_name": user.full_name, "avatar_color": user.avatar_color, "role": user.role}}


@router.get("/me")
async def get_me(current_user: User = Depends(require_user)):
    return {"id": current_user.id, "email": current_user.email, "username": current_user.username,
            "full_name": current_user.full_name, "avatar_color": current_user.avatar_color,
            "role": current_user.role, "created_at": current_user.created_at.isoformat()}


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}
