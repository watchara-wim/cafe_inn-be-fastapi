"""
Users Tests

Integration tests สำหรับ users endpoints
- GET /users/me — ดูข้อมูลตัวเอง
- PUT /users/me — แก้ไขข้อมูล
- GET /users/ — ดูรายการ users (admin only)
- GET /users/{id} — ดูข้อมูล user ตาม ID (admin only)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User

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

TEST_SUFFIX = "_testuser"


def create_test_user(username: str, password: str = "test1234") -> dict:
    """สมัคร test user แล้วคืน response data"""
    res = client.post("/auth/register", json={
        "username": f"{username}{TEST_SUFFIX}",
        "password": password,
        "name": "Test User",
        "email": f"{username}@testuser.com",
    })
    return res.json()


def get_token(username: str, password: str = "test1234") -> str:
    """Login แล้วคืน access token"""
    res = client.post("/auth/login", json={
        "username": f"{username}{TEST_SUFFIX}",
        "password": password,
    })
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    """สร้าง Authorization header"""
    return {"Authorization": f"Bearer {token}"}


def get_admin_token() -> str:
    """Login ด้วย admin (seed data) แล้วคืน token"""
    res = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin",
    })
    return res.json()["access_token"]


@pytest.fixture(autouse=True)
def cleanup_test_users():
    """ลบ test users ก่อนและหลังแต่ละ test"""
    db = TestingSessionLocal()
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    db.close()


# ===== GET /users/me =====

class TestGetMe:
    """ทดสอบ GET /users/me"""

    def test_get_profile_success(self):
        """ดูโปรไฟล์สำเร็จ — ตรวจ fields ที่คืนมา"""
        create_test_user("meuser")
        token = get_token("meuser")

        response = client.get("/users/me", headers=auth_header(token))
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == f"meuser{TEST_SUFFIX}"
        assert data["user_role"] == "customer"
        assert data["name"] == "Test User"
        assert data["email"] == "meuser@testuser.com"
        assert "password" not in data  # ต้องไม่ส่ง password กลับ

    def test_get_profile_no_token(self):
        """ไม่มี token → 401"""
        response = client.get("/users/me")
        assert response.status_code == 401


# ===== PUT /users/me =====

class TestUpdateMe:
    """ทดสอบ PUT /users/me"""

    def test_update_name_success(self):
        """อัปเดตชื่อสำเร็จ"""
        create_test_user("updateuser")
        token = get_token("updateuser")

        response = client.put("/users/me", headers=auth_header(token), json={
            "password": "test1234",
            "name": "Updated Name",
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_password_success(self):
        """เปลี่ยน password สำเร็จ — login ด้วย password ใหม่ได้"""
        create_test_user("pwchange")
        token = get_token("pwchange")

        response = client.put("/users/me", headers=auth_header(token), json={
            "password": "test1234",
            "new_password": "newpass5678",
        })
        assert response.status_code == 200

        login_res = client.post("/auth/login", json={
            "username": f"pwchange{TEST_SUFFIX}",
            "password": "newpass5678",
        })
        assert login_res.status_code == 200

    def test_update_wrong_password(self):
        """password เดิมผิด → 400"""
        create_test_user("wrongpw")
        token = get_token("wrongpw")

        response = client.put("/users/me", headers=auth_header(token), json={
            "password": "wrong_password",
            "name": "Should Fail",
        })
        assert response.status_code == 400
        assert "ไม่ถูกต้อง" in response.json()["detail"]

    def test_update_missing_password(self):
        """ไม่ส่ง password → 422 validation error"""
        create_test_user("nopw")
        token = get_token("nopw")

        response = client.put("/users/me", headers=auth_header(token), json={
            "name": "No Password",
        })
        assert response.status_code == 422

    def test_update_duplicate_email(self):
        """เปลี่ยน email เป็นของคนอื่น → 409"""
        create_test_user("emailowner")
        create_test_user("emailthief")
        token = get_token("emailthief")

        response = client.put("/users/me", headers=auth_header(token), json={
            "password": "test1234",
            "email": "emailowner@testuser.com",
        })
        assert response.status_code == 409


# ===== GET /users/ (admin only) =====

class TestListUsers:
    """ทดสอบ GET /users/"""

    def test_admin_list_users(self):
        """admin ดูรายการ users ได้"""
        token = get_admin_token()

        response = client.get("/users/", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1  # อย่างน้อยมี admin

    def test_customer_cannot_list(self):
        """customer เข้าถึง → 403"""
        create_test_user("normie")
        token = get_token("normie")

        response = client.get("/users/", headers=auth_header(token))
        assert response.status_code == 403


# ===== GET /users/{id} (admin only) =====

class TestGetUserById:
    """ทดสอบ GET /users/{id}"""

    def test_admin_get_user_by_id(self):
        """admin ดู user ตาม ID ได้"""
        user_data = create_test_user("targetuser")
        token = get_admin_token()
        user_id = user_data["user_id"]

        response = client.get(f"/users/{user_id}", headers=auth_header(token))
        assert response.status_code == 200
        assert response.json()["username"] == f"targetuser{TEST_SUFFIX}"

    def test_user_not_found(self):
        """user_id ไม่มี → 404"""
        token = get_admin_token()

        response = client.get("/users/999999", headers=auth_header(token))
        assert response.status_code == 404

    def test_customer_cannot_get_by_id(self):
        """customer เข้าถึง → 403"""
        create_test_user("sneaky")
        token = get_token("sneaky")

        response = client.get("/users/1", headers=auth_header(token))
        assert response.status_code == 403
