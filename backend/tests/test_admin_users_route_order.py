"""
Regression test for route precedence.

The static administrator path must be registered before the generic
/api/admin/{resource} route, or /api/admin/users is captured as resource="users".
"""
from app.main import app

def test_admin_users_route_precedes_generic_admin_resource_route():
    paths = [getattr(route, "path", None) for route in app.routes]
    users_index = paths.index("/api/admin/users")
    generic_index = paths.index("/api/admin/{resource}")
    assert users_index < generic_index
