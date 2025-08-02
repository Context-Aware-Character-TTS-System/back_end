import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
import os

# Add the project root to sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from back_end.main import app
from back_end.security import get_db # get_db is now in security.py
from back_end.models import Base, User, Novel, Sentence, RevokedToken # Import all models

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Drop tables after test

@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_create_user(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data

def test_create_user_duplicate_email(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword"
        },
    )
    response = client.post(
        "/users/register",
        json={
            "email": "duplicate@example.com",
            "password": "anotherpassword"
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_login_for_access_token(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "login@example.com",
            "password": "loginpassword"
        },
    )
    response = client.post(
        "/users/login",
        data={
            "username": "login@example.com",
            "password": "loginpassword"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_for_access_token_bad_password(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "badpass@example.com",
            "password": "correctpassword"
        },
    )
    response = client.post(
        "/users/login",
        data={
            "username": "badpass@example.com",
            "password": "wrongpassword"
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_non_existent_user(client: TestClient):
    response = client.post(
        "/users/login",
        data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_read_users_me(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "me@example.com",
            "password": "mepassword"
        },
    )
    login_response = client.post(
        "/users/login",
        data={
            "username": "me@example.com",
            "password": "mepassword"
        },
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"

def test_read_users_me_invalid_token(client: TestClient):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalidtoken"
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_logout_user(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "logout@example.com",
            "password": "logoutpassword"
        },
    )
    login_response = client.post(
        "/users/login",
        data={
            "username": "logout@example.com",
            "password": "logoutpassword"
        },
    )
    token = login_response.json()["access_token"]

    logout_response = client.post(
        "/users/logout",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Successfully logged out"}

def test_access_after_logout(client: TestClient):
    client.post(
        "/users/register",
        json={
            "email": "afterlogout@example.com",
            "password": "afterlogoutpassword"
        },
    )
    login_response = client.post(
        "/users/login",
        data={
            "username": "afterlogout@example.com",
            "password": "afterlogoutpassword"
        },
    )
    token = login_response.json()["access_token"]

    client.post(
        "/users/logout",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Token has been revoked"}
