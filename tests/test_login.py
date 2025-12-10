def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()

def test_login_rejects_wrong_password(client, test_user):
    resp = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpass"},
        follow_redirects=True,
    )
    assert b"invalid" in resp.data.lower() or b"error" in resp.data.lower()

def test_login_success_redirects_to_dashboard(client, test_user):
    resp = client.post(
        "/login",
        data={"username": "testuser", "password": "testpass"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert "/dashboard" in resp.headers.get("Location", "")
