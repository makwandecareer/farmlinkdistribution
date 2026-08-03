FarmLink Backend — Audit Trail Route Fix

Root cause:
The endpoint GET /api/admin/audit was declared after GET /api/admin/{resource}.
Because FastAPI/Starlette resolves routes in declaration order, "audit" was
captured as the generic resource value and returned 404.

Fix:
The audit endpoint is moved above the generic resource route. The previous
administrator-users route fix is retained.

Install:
1. Replace backend/app/main.py with the corrected file.
2. Optionally add backend/tests/test_admin_static_route_order.py.
3. Commit and push.
4. Wait for the Render backend service to redeploy.
