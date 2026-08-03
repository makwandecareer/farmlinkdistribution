from app.main import app

def test_enterprise_static_routes_precede_generic_admin_routes():
    paths=[getattr(r,"path",None) for r in app.routes]
    generic=paths.index("/api/admin/{resource}")
    assert paths.index("/api/admin/executive-summary") < generic
    assert paths.index("/api/admin/payments/{payment_id}") < paths.index("/api/admin/{resource}/{record_id}")
