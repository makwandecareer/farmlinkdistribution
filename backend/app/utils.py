import secrets
from datetime import datetime
from sqlalchemy.orm import Session
from .models import AuditLog, User

def make_reference(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow():%Y%m%d}-{secrets.token_hex(3).upper()}"

def audit(db: Session, actor: User | None, action: str, entity_type: str, entity_id: int | None, detail: dict | None = None, ip: str | None = None):
    db.add(AuditLog(actor_id=actor.id if actor else None, actor_name=actor.full_name if actor else "Public website", action=action, entity_type=entity_type, entity_id=entity_id, detail=detail, ip_address=ip))
