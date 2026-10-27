from sqlalchemy import select
from app.models import AuditEvent
from tests.test_passwords import STRONG_PASSWORD

EMAIL = "demo@example.com"


def test_register_login_me_and_audit(client, db):
    assert client.get("/auth/me").status_code == 401
    weak = client.post("/auth/register", json={"email": EMAIL, "password": "123456789012"})
    assert weak.status_code == 400
    reg = client.post("/auth/register", json={"email": EMAIL, "password": STRONG_PASSWORD})
    assert reg.status_code == 200
    assert reg.json()["token_type"] == "bearer"
    wrong = client.post("/auth/login", json={"email": EMAIL, "password": "wrong"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "Invalid credentials"
    logged = client.post("/auth/login", json={"email": EMAIL, "password": STRONG_PASSWORD})
    assert logged.status_code == 200
    token = logged.json()["access_token"]
    who = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert who.status_code == 200
    assert who.json()["email"] == EMAIL
    db.expire_all()
    events = db.scalars(select(AuditEvent.event_type)).all()
    assert "user.login.success" in events
    assert "user.login.failure" in events
