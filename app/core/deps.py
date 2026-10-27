from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.jwt import decode_token


def user_from_authorization(authorization: str | None, db: Session) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = decode_token(authorization.removeprefix("Bearer ").strip())
    except ValueError:
        return None
    user = db.scalar(select(User).where(User.email == payload["sub"]))
    return user if user is not None and user.is_active else None


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    user = user_from_authorization(authorization, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user
