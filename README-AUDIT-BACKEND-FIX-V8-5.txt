FarmLink Administrator Audit Backend Fix V8.5

Root cause:
The administrator audit endpoint queried AuditLog.actor_user_id, but the actual
SQLAlchemy model field is AuditLog.actor_id. That raised a server-side
AttributeError before a normal API response was produced. The browser surfaced
the failed response as a CORS/fetch error.

Fix:
AuditLog.actor_user_id -> AuditLog.actor_id

Only backend/app/main.py needs to be deployed.
