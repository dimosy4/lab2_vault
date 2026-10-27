from sqlalchemy.orm import Session
from app.models import AuditEvent


def write_event(db: Session, event_type: str, *, actor_id=None, client_id=None, ip=None, user_agent=None, metadata=None, commit=True):
    """Do not pass passwords, hashes or tokens into metadata."""
    event = AuditEvent(event_type=event_type, actor_id=actor_id, client_id=client_id,
                       ip=ip, user_agent=user_agent, metadata_json=metadata or {})
    db.add(event)
    if commit:
        db.commit()
    return event
