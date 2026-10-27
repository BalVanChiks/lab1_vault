from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

def write_event(
    db: Session, 
    event_type: str, 
    actor_id: int = None, 
    client_id: str = None, 
    ip: str = None, 
    user_agent: str = None, 
    metadata: dict = None
):
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        client_id=client_id,
        ip=ip,
        user_agent=user_agent,
        metadata_json=metadata or {}
    )
    db.add(event)
    db.commit()