import pytest
from app.core.passwords import validate_policy, hash_password, verify_password, WeakPasswordError

STRONG_PASSWORD = "River!Sunset83?Marble#Omega"


def test_weak_password_rejected():
    with pytest.raises(WeakPasswordError):
        validate_policy("123456789012", ["admin@example.com"])


def test_strong_password_accepted_and_hash_verified():
    validate_policy(STRONG_PASSWORD, ["admin@example.com"])
    encoded = hash_password(STRONG_PASSWORD)
    assert encoded.startswith("$argon2id$")
    assert verify_password(STRONG_PASSWORD, encoded)
    assert not verify_password("incorrect", encoded)
