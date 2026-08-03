"""
Regression tests for static admin route precedence.
"""
from app.main import app

def test_static_admin_routes_precede_generic_resource_routes():
    paths = [getattr(route, "path", None) for route in app.routes]
    generic_collection = paths.index("/api/admin/{resource}")
    generic_detail = paths.index("/api/admin/{resource}/{record_id}")

    assert paths.index("/api/admin/users") < generic_collection
    assert paths.index("/api/admin/audit") < generic_collection
    assert paths.index("/api/admin/payments") < generic_collection
    assert paths.index("/api/admin/payments/{payment_id}") < generic_detail
