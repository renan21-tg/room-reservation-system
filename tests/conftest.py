import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
event.listen(engine, "connect", _set_sqlite_pragma)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_user(client, email="user@example.com", role="user"):
    return client.post(
        "/users",
        json={
            "name": "Test User",
            "email": email,
            "password": "secret123",
            "role": role,
        },
    ).json()


def auth_headers(client, email, password="secret123"):
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client):
    create_user(client, email="admin@example.com", role="admin")
    return auth_headers(client, "admin@example.com")


@pytest.fixture(scope="function")
def user_headers(client):
    create_user(client, email="user@example.com", role="user")
    return auth_headers(client, "user@example.com")
