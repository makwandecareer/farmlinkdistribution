from app.models import AuditLog

def test_audit_log_uses_actor_id_field():
    assert hasattr(AuditLog, "actor_id")
    assert not hasattr(AuditLog, "actor_user_id")
