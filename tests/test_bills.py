import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.property import Property
from app.models.bill import Bill, BillStatus
from app.models.setting import Setting

SQLALCHEMY_TEST_URL = "sqlite:///./test_bills.db"
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

    admin    = User(name="Admin", mobile="9000000001",
                    password_hash=hash_password("admin1234"), role=UserRole.ADMIN, is_active=True)
    resident = User(name="Resident", mobile="9000000003",
                    password_hash=hash_password("res1234"), role=UserRole.RESIDENT, is_active=True)
    db.add_all([admin, resident])
    db.commit()
    db.refresh(admin); db.refresh(resident)

    prop = Property(unit_no="4B", floor=4, area_sqft=1050, owner_id=resident.user_id)
    db.add(prop)
    db.commit()
    db.refresh(prop)

    # Default penalty setting
    db.add(Setting(key="penalty_daily_pct", value="0.05"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _token(mobile, password):
    r = client.post("/api/v1/auth/login", json={"mobile": mobile, "password": password})
    return r.json()["access_token"]


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


def test_generate_bills_as_admin():
    tok = _token("9000000001", "admin1234")
    due = (date.today() + timedelta(days=10)).isoformat()
    r = client.post("/api/v1/bills/generate", headers=_hdr(tok), json={
        "month": 6, "year": 2025,
        "maintenance": 2000, "due_date": due,
        "include_penalty": False,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["generated"] >= 1
    assert data["total_amount"] >= 2000


def test_generate_bills_duplicate_skipped():
    tok = _token("9000000001", "admin1234")
    due = (date.today() + timedelta(days=10)).isoformat()
    payload = {"month": 7, "year": 2025, "maintenance": 2000,
               "due_date": due, "include_penalty": False}
    client.post("/api/v1/bills/generate", headers=_hdr(tok), json=payload)
    r = client.post("/api/v1/bills/generate", headers=_hdr(tok), json=payload)
    assert r.status_code == 201
    assert r.json()["skipped"] >= 1


def test_generate_bills_as_resident_forbidden():
    tok = _token("9000000003", "res1234")
    r = client.post("/api/v1/bills/generate", headers=_hdr(tok), json={
        "month": 6, "year": 2025, "maintenance": 2000,
        "due_date": date.today().isoformat(), "include_penalty": False,
    })
    assert r.status_code == 403


def test_resident_sees_own_bills():
    # First generate a bill
    admin_tok = _token("9000000001", "admin1234")
    due = (date.today() + timedelta(days=10)).isoformat()
    client.post("/api/v1/bills/generate", headers=_hdr(admin_tok), json={
        "month": 8, "year": 2025, "maintenance": 2000,
        "due_date": due, "include_penalty": False,
    })
    # Resident fetches bills
    res_tok = _token("9000000003", "res1234")
    r = client.get("/api/v1/bills", headers=_hdr(res_tok))
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_collection_summary():
    admin_tok = _token("9000000001", "admin1234")
    due = (date.today() + timedelta(days=10)).isoformat()
    client.post("/api/v1/bills/generate", headers=_hdr(admin_tok), json={
        "month": 9, "year": 2025, "maintenance": 2000,
        "due_date": due, "include_penalty": False,
    })
    r = client.get("/api/v1/bills/summary?month=9&year=2025", headers=_hdr(admin_tok))
    assert r.status_code == 200
    data = r.json()
    assert data["total_bills"] >= 1
    assert "paid_amount" in data
    assert "collection_pct" in data


def test_penalty_formula():
    """Unit test the penalty calculation directly."""
    from app.services.bill_service import apply_penalties_for_all
    db = TestSessionLocal()

    # Create an overdue bill
    prop = db.query(Property).first()
    overdue_date = date.today() - timedelta(days=10)
    bill = Bill(
        property_id=prop.property_id,
        month=1, year=2025,
        maintenance=2000.0, penalty=0.0, total=2000.0,
        due_date=overdue_date,
        status=BillStatus.PENDING,
    )
    db.add(bill)
    db.commit()

    updated = apply_penalties_for_all(db)
    db.refresh(bill)

    # 2000 * 0.05% * 10 days = 10.0
    assert updated >= 1
    assert bill.penalty == pytest.approx(10.0, abs=0.01)
    assert bill.total   == pytest.approx(2010.0, abs=0.01)
    assert bill.status  == BillStatus.OVERDUE
    db.close()


def test_waive_bill():
    admin_tok = _token("9000000001", "admin1234")
    due = (date.today() + timedelta(days=5)).isoformat()
    gen = client.post("/api/v1/bills/generate", headers=_hdr(admin_tok), json={
        "month": 10, "year": 2025, "maintenance": 2000,
        "due_date": due, "include_penalty": False,
    })
    bills_r = client.get("/api/v1/bills?month=10&year=2025", headers=_hdr(admin_tok))
    bill_id = bills_r.json()["items"][0]["bill_id"]

    r = client.patch(f"/api/v1/bills/{bill_id}/waive", headers=_hdr(admin_tok))
    assert r.status_code == 200
