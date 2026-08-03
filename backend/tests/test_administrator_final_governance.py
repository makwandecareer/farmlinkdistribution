from app.main import app

def test_administrator_governance_routes_are_static_and_available():
    paths=[getattr(r,"path",None) for r in app.routes]
    required=[
        "/api/admin/users",
        "/api/admin/users/{user_id}",
        "/api/admin/users/{user_id}/status",
        "/api/admin/users/{user_id}/reset-password",
        "/api/admin/users/{user_id}/audit",
    ]
    for path in required:
        assert path in paths
    assert paths.index("/api/admin/users") < paths.index("/api/admin/{resource}")
