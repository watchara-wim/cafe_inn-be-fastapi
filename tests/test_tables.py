"""
Tables Tests

Integration tests สำหรับ tables endpoints
- GET /tables/ — ดูโต๊ะทั้งหมด (public)
- GET /tables/{id} — ดูโต๊ะเดี่ยว (staff/admin)
- POST /tables/ — เพิ่มโต๊ะ (admin)
- PUT /tables/{id} — แก้ไขโต๊ะ (staff/admin)
- DELETE /tables/{id} — ลบโต๊ะ (admin)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
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

TEST_PREFIX = "TESTTBL_"
TEST_SUFFIX = "_testtbl"


# === Helpers ===

def get_admin_token() -> str:
    """Login ด้วย admin (seed data) แล้วคืน token"""
    res = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin",
    })
    return res.json()["access_token"]


def create_customer_and_get_token() -> str:
    """สร้าง customer test user แล้วคืน token"""
    client.post("/auth/register", json={
        "username": f"tblcust{TEST_SUFFIX}",
        "password": "test1234",
    })
    res = client.post("/auth/login", json={
        "username": f"tblcust{TEST_SUFFIX}",
        "password": "test1234",
    })
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_test_table(token: str, number: str = "99") -> dict:
    """สร้าง test table แล้วคืน response data"""
    res = client.post("/tables/", headers=auth_header(token), json={
        "table_number": f"{TEST_PREFIX}{number}",
        "capacity": 4,
    })
    return res.json()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """ลบ test tables + test users ก่อนและหลังแต่ละ test"""
    db = TestingSessionLocal()
    db.query(Table).filter(Table.table_number.like(f"{TEST_PREFIX}%")).delete(synchronize_session=False)
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(Table).filter(Table.table_number.like(f"{TEST_PREFIX}%")).delete(synchronize_session=False)
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    db.close()


# ===== GET /tables/ (public) =====

class TestListTables:
    """ทดสอบ GET /tables/"""

    def test_list_tables_public(self):
        """ดูโต๊ะทั้งหมดได้โดยไม่ต้อง login"""
        response = client.get("/tables/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_tables_has_fields(self):
        """response มี fields ที่ต้องการ"""
        response = client.get("/tables/")
        assert response.status_code == 200
        tables = response.json()
        if len(tables) > 0:
            table = tables[0]
            assert "table_id" in table
            assert "table_number" in table
            assert "capacity" in table
            assert "status" in table


# ===== GET /tables/{id} (staff/admin) =====

class TestGetTable:
    """ทดสอบ GET /tables/{id}"""

    def test_get_table_staff_success(self):
        """admin ดูโต๊ะเดี่ยวสำเร็จ"""
        token = get_admin_token()
        table = create_test_table(token)

        response = client.get(f"/tables/{table['table_id']}", headers=auth_header(token))
        assert response.status_code == 200
        assert response.json()["table_number"] == f"{TEST_PREFIX}99"

    def test_get_table_not_found(self):
        """ไม่พบโต๊ะ → 404"""
        token = get_admin_token()
        response = client.get("/tables/999999", headers=auth_header(token))
        assert response.status_code == 404

    def test_get_table_customer_forbidden(self):
        """customer ไม่มีสิทธิ์ดูโต๊ะเดี่ยว → 403"""
        token_admin = get_admin_token()
        table = create_test_table(token_admin)
        token_customer = create_customer_and_get_token()

        response = client.get(f"/tables/{table['table_id']}", headers=auth_header(token_customer))
        assert response.status_code == 403


# ===== POST /tables/ (admin) =====

class TestCreateTable:
    """ทดสอบ POST /tables/"""

    def test_create_table_admin(self):
        """admin สร้างโต๊ะสำเร็จ"""
        token = get_admin_token()

        response = client.post("/tables/", headers=auth_header(token), json={
            "table_number": f"{TEST_PREFIX}15",
            "capacity": 6,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["table_number"] == f"{TEST_PREFIX}15"
        assert data["capacity"] == 6
        assert data["status"] == "empty"

    def test_create_table_customer_forbidden(self):
        """customer ไม่มีสิทธิ์สร้างโต๊ะ → 403"""
        token = create_customer_and_get_token()

        response = client.post("/tables/", headers=auth_header(token), json={
            "table_number": f"{TEST_PREFIX}16",
            "capacity": 4,
        })
        assert response.status_code == 403


# ===== PUT /tables/{id} (staff/admin) =====

class TestUpdateTable:
    """ทดสอบ PUT /tables/{id}"""

    def test_update_table_success(self):
        """admin แก้ไขโต๊ะสำเร็จ"""
        token = get_admin_token()
        table = create_test_table(token)

        response = client.put(
            f"/tables/{table['table_id']}",
            headers=auth_header(token),
            json={"status": "reserved", "capacity": 8},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "reserved"
        assert response.json()["capacity"] == 8

    def test_update_table_not_found(self):
        """แก้ไขโต๊ะที่ไม่มี → 404"""
        token = get_admin_token()

        response = client.put(
            "/tables/999999",
            headers=auth_header(token),
            json={"status": "full"},
        )
        assert response.status_code == 404


# ===== DELETE /tables/{id} (admin) =====

class TestDeleteTable:
    """ทดสอบ DELETE /tables/{id}"""

    def test_delete_table_success(self):
        """admin ลบโต๊ะสำเร็จ"""
        token = get_admin_token()
        table = create_test_table(token)

        response = client.delete(
            f"/tables/{table['table_id']}",
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert "สำเร็จ" in response.json()["message"]

        # ต้องไม่พบโต๊ะนี้อีก
        get_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(token))
        assert get_res.status_code == 404

    def test_delete_table_customer_forbidden(self):
        """customer ไม่มีสิทธิ์ลบโต๊ะ → 403"""
        token_admin = get_admin_token()
        table = create_test_table(token_admin)
        token_customer = create_customer_and_get_token()

        response = client.delete(
            f"/tables/{table['table_id']}",
            headers=auth_header(token_customer),
        )
        assert response.status_code == 403
