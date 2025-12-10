def _login(client):
    return client.post(
        "/login",
        data={"username": "testuser", "password": "testpass"},
        follow_redirects=False,
    )

def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/login" in resp.headers.get("Location", "")

def test_dashboard_access_after_login(client, test_user):
    _login(client)
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"dashboard" in resp.data.lower()

def test_resident_pages_require_login(client):
    protected_paths = [
        "/maintenance/new",
        "/packages",
        "/community",
    ]
    for path in protected_paths:
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code in (302, 303)
        assert "/login" in resp.headers.get("Location", "")
