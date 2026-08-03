from app.main import app

def test_user_governance_routes_exist_before_generic_routes():
    paths=[getattr(r,"path",None) for r in app.routes]
    generic_detail=paths.index("/api/admin/{resource}/{record_id}")
    for path in ["/api/admin/users/{user_id}","/api/admin/users/{user_id}/status","/api/admin/users/{user_id}/reset-password","/api/admin/users/{user_id}/audit"]:
        assert path in paths
    assert paths.index("/api/admin/users/{user_id}") < generic_detail
