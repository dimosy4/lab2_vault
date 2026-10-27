from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.passwords import validate_policy, hash_password, verify_password, WeakPasswordError
from app.core.jwt import create_access_token
from app.core.deps import get_current_user
from app.audit.service import write_event

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str


def origin(request: Request):
    return {"ip": request.client.host if request.client else None, "user_agent": request.headers.get("user-agent")}


@router.post("/register")
def register(data: Credentials, request: Request, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    try:
        validate_policy(data.password, [email])
    except WeakPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    user = User(email=email, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()
    write_event(db, "user.created", actor_id=user.id, **origin(request), commit=False)
    db.commit()
    return {"access_token": create_access_token(email), "token_type": "bearer"}


@router.post("/login")
def login(data: Credentials, request: Request, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(data.password, user.hashed_password):
        write_event(db, "user.login.failure", metadata={"email": email}, **origin(request))
        raise HTTPException(status_code=401, detail="Invalid credentials")
    write_event(db, "user.login.success", actor_id=user.id, **origin(request))
    return {"access_token": create_access_token(email), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}
