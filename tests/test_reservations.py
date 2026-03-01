"""
Reservations Tests

Integration tests สำหรับ reservations endpoints
- POST /reservations/ — สร้างการจอง (ทุก role)
- GET /reservations/me — ดูการจองของตัวเอง
- GET /reservations/ — ดูรายการจองทั้งหมด (staff/admin)
- GET /reservations/{id} — ดูรายการจองเดี่ยว (staff/admin)
- PATCH /reservations/{id} — อัปเดต status (staff/admin)
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
from app.models.reservation import Reservation
from app.models.table import Table
from app.models.user import User

# Test DB setup
engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

TEST_PREFIX = "TESTRSV_"
TEST_SUFFIX = "_testrsv"


# === Helpers ===

def get_admin_token() -> str:
    """Login ด้วย admin (seed data) แล้วคืน token"""
    res = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin",
    })
    return res.json()["access_token"]


def create_customer_and_get_token(suffix: str = "") -> str:
    """สร้าง customer test user แล้วคืน token"""
    username = f"rsvcust{suffix}{TEST_SUFFIX}"
    client.post("/auth/register", json={
        "username": username,
        "password": "test1234",
    })
    res = client.post("/auth/login", json={
        "username": username,
        "password": "test1234",
    })
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_test_table(token: str, number: str = "90") -> dict:
    """สร้าง test table แล้วคืน response data"""
    res = client.post("/tables/", headers=auth_header(token), json={
        "table_number": f"{TEST_PREFIX}{number}",
        "capacity": 4,
    })
    return res.json()


def create_test_reservation(token: str, table_ids: list[int]) -> dict:
    """สร้าง test reservation แล้วคืน response data"""
    reservation_time = (datetime.now() + timedelta(hours=1)).isoformat()
    res = client.post("/reservations/", headers=auth_header(token), json={
        "table_ids": table_ids,
        "capacity": 4,
        "reservation_time": reservation_time,
        "customer_amount": 2,
        "reservation_detail": f"{TEST_PREFIX}test reservation",
    })
    return res.json()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """ลบ test data ก่อนและหลังแต่ละ test"""
    db = TestingSessionLocal()
    # ลบ reservations ที่มี detail ขึ้นต้นด้วย TEST_PREFIX
    db.query(Reservation).filter(
        Reservation.reservation_detail.like(f"{TEST_PREFIX}%")
    ).delete(synchronize_session=False)
    # ลบ test tables
    db.query(Table).filter(
        Table.table_number.like(f"{TEST_PREFIX}%")
    ).delete(synchronize_session=False)
    # ลบ test users
    db.query(User).filter(
        User.username.like(f"%{TEST_SUFFIX}")
    ).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(Reservation).filter(
        Reservation.reservation_detail.like(f"{TEST_PREFIX}%")
    ).delete(synchronize_session=False)
    db.query(Table).filter(
        Table.table_number.like(f"{TEST_PREFIX}%")
    ).delete(synchronize_session=False)
    db.query(User).filter(
        User.username.like(f"%{TEST_SUFFIX}")
    ).delete(synchronize_session=False)
    db.commit()
    db.close()


# ===== POST /reservations/ =====

class TestCreateReservation:
    """ทดสอบ POST /reservations/"""

    def test_create_reservation_success(self):
        """customer จองสำเร็จ + table status เปลี่ยนเป็น onHold"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "91")

        customer_token = create_customer_and_get_token("1")
        reservation = create_test_reservation(customer_token, [table["table_id"]])

        assert reservation["reservation_status"] == "pending"
        assert reservation["table_ids"] == [table["table_id"]]
        assert reservation["customer_amount"] == 2

        # ตรวจ table status เปลี่ยนเป็น onHold
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "onHold"

    def test_create_reservation_invalid_table(self):
        """จอง table ที่ไม่มี → 404"""
        customer_token = create_customer_and_get_token("2")
        reservation_time = (datetime.now() + timedelta(hours=1)).isoformat()

        res = client.post("/reservations/", headers=auth_header(customer_token), json={
            "table_ids": [999999],
            "capacity": 4,
            "reservation_time": reservation_time,
            "customer_amount": 2,
            "reservation_detail": f"{TEST_PREFIX}invalid",
        })
        assert res.status_code == 404

    def test_create_reservation_no_auth(self):
        """ไม่มี token → 401"""
        reservation_time = (datetime.now() + timedelta(hours=1)).isoformat()

        res = client.post("/reservations/", json={
            "table_ids": [1],
            "capacity": 4,
            "reservation_time": reservation_time,
            "customer_amount": 2,
        })
        assert res.status_code == 401


# ===== GET /reservations/me =====

class TestMyReservation:
    """ทดสอบ GET /reservations/me"""

    def test_my_reservation_success(self):
        """ดูการจองของตัวเองสำเร็จ"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "92")

        customer_token = create_customer_and_get_token("3")
        create_test_reservation(customer_token, [table["table_id"]])

        res = client.get("/reservations/me", headers=auth_header(customer_token))
        assert res.status_code == 200
        assert res.json()["reservation_status"] == "pending"

    def test_my_reservation_none(self):
        """ไม่มีการจองวันนี้ → คืน null"""
        customer_token = create_customer_and_get_token("4")

        res = client.get("/reservations/me", headers=auth_header(customer_token))
        assert res.status_code == 200
        assert res.json()["reservation"] is None


# ===== GET /reservations/ (staff/admin) =====

class TestListReservations:
    """ทดสอบ GET /reservations/"""

    def test_list_reservations_admin(self):
        """admin ดูรายการจองสำเร็จ"""
        admin_token = get_admin_token()

        res = client.get("/reservations/", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_reservations_customer_forbidden(self):
        """customer ไม่มีสิทธิ์ดูรายการจองทั้งหมด → 403"""
        customer_token = create_customer_and_get_token("5")

        res = client.get("/reservations/", headers=auth_header(customer_token))
        assert res.status_code == 403


# ===== GET /reservations/{id} (staff/admin) =====

class TestGetReservation:
    """ทดสอบ GET /reservations/{id}"""

    def test_get_reservation_success(self):
        """admin ดูรายการจองเดี่ยวสำเร็จ"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "93")

        customer_token = create_customer_and_get_token("6")
        reservation = create_test_reservation(customer_token, [table["table_id"]])

        res = client.get(
            f"/reservations/{reservation['reservation_id']}",
            headers=auth_header(admin_token),
        )
        assert res.status_code == 200
        assert res.json()["reservation_id"] == reservation["reservation_id"]

    def test_get_reservation_not_found(self):
        """ไม่พบรายการจอง → 404"""
        admin_token = get_admin_token()

        res = client.get("/reservations/999999", headers=auth_header(admin_token))
        assert res.status_code == 404


# ===== PATCH /reservations/{id} (staff/admin) =====

class TestUpdateReservation:
    """ทดสอบ PATCH /reservations/{id}"""

    def test_accept_reservation_table_reserved(self):
        """staff accept → table status เปลี่ยนเป็น reserved"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "94")

        customer_token = create_customer_and_get_token("7")
        reservation = create_test_reservation(customer_token, [table["table_id"]])

        res = client.patch(
            f"/reservations/{reservation['reservation_id']}",
            headers=auth_header(admin_token),
            json={
                "reservation_status": "accepted",
                "response_at": datetime.now().isoformat(),
            },
        )
        assert res.status_code == 200
        assert res.json()["reservation_status"] == "accepted"

        # ตรวจ table status
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "reserved"

    def test_cancel_reservation_table_empty(self):
        """staff cancel → table status เปลี่ยนเป็น empty"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "95")

        customer_token = create_customer_and_get_token("8")
        reservation = create_test_reservation(customer_token, [table["table_id"]])

        res = client.patch(
            f"/reservations/{reservation['reservation_id']}",
            headers=auth_header(admin_token),
            json={
                "reservation_status": "cancel",
                "cancel_detail": "ลูกค้ายกเลิก",
            },
        )
        assert res.status_code == 200
        assert res.json()["reservation_status"] == "cancel"

        # ตรวจ table status
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "empty"

    def test_update_reservation_customer_forbidden(self):
        """customer ไม่มีสิทธิ์อัปเดต status → 403"""
        admin_token = get_admin_token()
        table = create_test_table(admin_token, "96")

        customer_token = create_customer_and_get_token("9")
        reservation = create_test_reservation(customer_token, [table["table_id"]])

        res = client.patch(
            f"/reservations/{reservation['reservation_id']}",
            headers=auth_header(customer_token),
            json={"reservation_status": "accepted"},
        )
        assert res.status_code == 403
