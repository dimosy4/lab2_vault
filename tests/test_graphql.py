from sqlalchemy import select
from app.models import User, OAuthClient, AuditEvent
from tests.test_passwords import STRONG_PASSWORD


def query(client, body, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post("/graphql/", json={"query": body}, headers=headers).json()


def test_permissions_and_mutations(client, db):
    assert "Authentication required" in str(query(client, "{ me { email } }")["errors"])
    assert "Admin only" in str(query(client, "{ users { email } }")["errors"])
    registered = client.post("/auth/register", json={"email":"admin@example.com", "password": STRONG_PASSWORD}).json()
    token = registered["access_token"]
    assert query(client, "{ me { email } }")["errors"]
    assert "Admin only" in str(query(client, "{ users { email } }", token)["errors"])
    db_user = db.scalar(select(User).where(User.email == "admin@example.com"))
    db_user.is_admin = True
    db.commit()
    created = query(client, 'mutation { createClient(name:"Example",isConfidential:false) { name clientId } }', token)
    assert created["data"]["createClient"]["name"] == "Example"
    assert len(db.scalars(select(OAuthClient)).all()) == 1
    db.expire_all()
    assert "client.created" in db.scalars(select(AuditEvent.event_type)).all()
    admins = query(client, "{ users { email isAdmin } clients { name } auditEvents { eventType } }", token)
    assert not admins.get("errors")
    assert admins["data"]["users"][0]["isAdmin"] is True
