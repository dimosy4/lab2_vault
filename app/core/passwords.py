from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError
from zxcvbn import zxcvbn
from app.config import settings


class WeakPasswordError(ValueError):
    pass


hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID)


def validate_policy(password: str, user_inputs=None) -> None:
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(f"Password must contain at least {settings.password_min_length} characters")
    if zxcvbn(password, user_inputs=user_inputs or []).get("score", 0) < 3:
        raise WeakPasswordError("Password is too weak (zxcvbn score must be at least 3)")


def hash_password(password: str) -> str:
    return hasher.hash(password + settings.password_pepper)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bool(hasher.verify(hashed, password + settings.password_pepper))
    except (VerifyMismatchError, VerificationError, ValueError):
        return False
