from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import JWTError, jwt
from app.config import settings


def create_access_token(sub: str, ttl_min: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_min or settings.access_token_ttl_min)).timestamp()),
        "jti": str(uuid4()),
        "typ": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if data.get("typ") != "access" or not data.get("sub"):
            raise ValueError("Invalid token type or subject")
        return data
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
