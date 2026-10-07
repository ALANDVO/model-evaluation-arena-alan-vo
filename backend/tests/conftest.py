import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["APP_ENV"] = "testing"
os.environ["DEMO_MODE"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-chars-long"

from app.core.database import Base, get_db
from app.main import app
from app.services.seed_data import seed_benchmarks_if_empty

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_benchmarks_if_empty(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def analyst_auth(client):
    resp = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert resp.status_code == 200
    data = resp.json()
    return {
        "token": data["token"],
        "csrf": data["csrf_token"],
        "headers": {
            "Authorization": f"Bearer {data['token']}",
            "X-CSRF-Token": data["csrf_token"],
        },
    }

@pytest.fixture
def viewer_auth(client):
    resp = client.post("/api/auth/demo-login", json={"role": "viewer"})
    assert resp.status_code == 200
    data = resp.json()
    return {
        "token": data["token"],
        "csrf": data["csrf_token"],
        "headers": {
            "Authorization": f"Bearer {data['token']}",
            "X-CSRF-Token": data["csrf_token"],
        },
    }
