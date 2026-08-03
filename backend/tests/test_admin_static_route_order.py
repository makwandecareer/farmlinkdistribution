"""
Regression tests for static admin route precedence.
"""
from app.main import app

def test_static_admin_routes_precede_generic_resource_route():
    paths = [getattr(route, "path", None) for route in app.routes]
    generic_index = paths.index("/api/admin/{resource}")
    assert paths.index("/api/admin/users") < generic_index
    assert paths.index("/api/admin/audit") < generic_index
