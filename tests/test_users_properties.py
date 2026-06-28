import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.property import Property

SQLALCHEMY_TEST_URL = "sqlite:///./test_f2.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def _seed(db):
    admin = User(name="Admin", mobile="9000000001",
                 password_hash=hash_password("admin1234"), role=UserRole.ADMIN, is_active=True)
    mgmt  = User(name="Mgmt",  mobile="9000000002",
                 password_hash=hash_password("mgmt1234"),  role=UserRole.MANAGEMENT, is_active=True)
    user  = User(name="Resident", mobile="9000000003",
                 password_hash=hash_password("res1234"),   role=UserRole.RESIDENT, is_active=True)
    db.add_all([admin, mgmt, user])
    db.commit()
    db.refresh(admin); db.refresh(mgmt); db.refresh(user)
    return admin, mgmt, user


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    _seed(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _token(mobile, password):
    r = client.post("/api/v1/auth/login", json={"mobile": mobile, "password": password})
    return r.json()["access_token"]


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


# ── User tests ────────────────────────────────────────────────────

def test_list_users_as_admin():
    tok = _token("9000000001", "admin1234")
    r = client.get("/api/v1/users", headers=_hdr(tok))
    assert r.status_code == 200
    assert r.json()["total"] >= 3


def test_list_users_as_resident_forbidden():
    tok = _token("9000000003", "res1234")
    r = client.get("/api/v1/users", headers=_hdr(tok))
    assert r.status_code == 403


def test_create_user_as_admin():
    tok = _token("9000000001", "admin1234")
    r = client.post("/api/v1/users", headers=_hdr(tok), json={
        "name": "New User", "mobile": "9111111111",
        "password": "newpass123", "role": "resident"
    })
    assert r.status_code == 201
    assert r.json()["mobile"] == "9111111111"


def test_create_user_duplicate_mobile():
    tok = _token("9000000001", "admin1234")
    client.post("/api/v1/users", headers=_hdr(tok), json={
        "name": "Dup", "mobile": "9222222222", "password": "pass1234", "role": "resident"
    })
    r = client.post("/api/v1/users", headers=_hdr(tok), json={
        "name": "Dup2", "mobile": "9222222222", "password": "pass1234", "role": "resident"
    })
    assert r.status_code == 400


def test_get_me():
    tok = _token("9000000003", "res1234")
    r = client.get("/api/v1/users/me", headers=_hdr(tok))
    assert r.status_code == 200
    assert r.json()["mobile"] == "9000000003"


def test_update_user_as_admin():
    tok = _token("9000000001", "admin1234")
    users = client.get("/api/v1/users", headers=_hdr(tok)).json()["items"]
    uid = next(u["user_id"] for u in users if u["mobile"] == "9000000003")
    r = client.patch(f"/api/v1/users/{uid}", headers=_hdr(tok), json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


# ── Property tests ────────────────────────────────────────────────

def test_create_property_as_admin():
    tok = _token("9000000001", "admin1234")
    r = client.post("/api/v1/properties", headers=_hdr(tok), json={
        "unit_no": "3C", "floor": 3, "type": "residential", "area_sqft": 900
    })
    assert r.status_code == 201
    assert r.json()["unit_no"] == "3C"


def test_create_property_duplicate_unit():
    tok = _token("9000000001", "admin1234")
    client.post("/api/v1/properties", headers=_hdr(tok), json={"unit_no": "5D", "floor": 5})
    r = client.post("/api/v1/properties", headers=_hdr(tok), json={"unit_no": "5D", "floor": 5})
    assert r.status_code == 400


def test_list_properties_any_user():
    tok = _token("9000000003", "res1234")
    r = client.get("/api/v1/properties", headers=_hdr(tok))
    assert r.status_code == 200


def test_create_property_as_resident_forbidden():
    tok = _token("9000000003", "res1234")
    r = client.post("/api/v1/properties", headers=_hdr(tok), json={"unit_no": "9Z", "floor": 9})
    assert r.status_code == 403
