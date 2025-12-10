import pytest
from werkzeug.security import generate_password_hash
from app import app as flask_app, db

@pytest.fixture(scope="session")
def app():
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    return flask_app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db():
    if db is not None:
        for name in db.list_collection_names():
            if not name.startswith("system."):
                db[name].delete_many({})
    yield
    if db is not None:
        for name in db.list_collection_names():
            if not name.startswith("system."):
                db[name].delete_many({})

@pytest.fixture()
def test_user():
    if db is None:
        return {"username": "testuser", "password": "testpass"}
    user = {
        "username": "testuser",
        "password": generate_password_hash("testpass"),
        "role": "resident",
        "apartment_id": "3B",
    }
    db.users.insert_one(user)
    return user
