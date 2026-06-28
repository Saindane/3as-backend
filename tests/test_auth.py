import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole

# ── Test DB setup ──────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    # Seed test user
    user = User(
        name="Test Resident",
        mobile="9876543210",
        email="test@example.com",
        password_hash=hash_password("demo1234"),
        role=UserRole.RESIDENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Tests ──────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_login_success():
    r = client.post("/api/v1/auth/login", json={"mobile": "9876543210", "password": "demo1234"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "resident"
    assert data["name"] == "Test Resident"


def test_login_wrong_password():
    r = client.post("/api/v1/auth/login", json={"mobile": "9876543210", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_mobile():
    r = client.post("/api/v1/auth/login", json={"mobile": "9000000000", "password": "demo1234"})
    assert r.status_code == 401


def test_login_invalid_mobile_format():
    r = client.post("/api/v1/auth/login", json={"mobile": "12345", "password": "demo1234"})
    assert r.status_code == 422


def test_refresh_token():
    login_r = client.post("/api/v1/auth/login", json={"mobile": "9876543210", "password": "demo1234"})
    refresh_token = login_r.json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_get_me():
    login_r = client.post("/api/v1/auth/login", json={"mobile": "9876543210", "password": "demo1234"})
    token = login_r.json()["access_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["mobile"] == "9876543210"


def test_otp_send_unknown_mobile():
    r = client.post("/api/v1/auth/otp/send", json={"mobile": "9000000000", "purpose": "password_reset"})
    assert r.status_code == 404


def test_otp_send_and_verify():
    # Send OTP
    r = client.post("/api/v1/auth/otp/send", json={"mobile": "9876543210", "purpose": "password_reset"})
    assert r.status_code == 200

    # Peek at the DB to get the actual OTP (dev mode)
    db = TestSessionLocal()
    from app.models.otp import OTPRecord
    record = db.query(OTPRecord).filter_by(mobile="9876543210", is_used=False).first()
    db.close()
    assert record is not None

    # Verify with wrong OTP
    r2 = client.post("/api/v1/auth/otp/verify", json={
        "mobile": "9876543210", "otp": "0000", "purpose": "password_reset"
    })
    assert r2.status_code == 400


def test_me_without_token():
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 403
