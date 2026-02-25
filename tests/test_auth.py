"""
Auth Tests

Integration tests สำหรับ authentication endpoints
- POST /auth/register
- POST /auth/login
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
from app.models.base import Base
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

# Suffix สำหรับแยก test users ไม่ให้ชนกับ data จริง (ได้ลบง่าย ๆ)
TEST_SUFFIX = "_testauth"


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


# ===== Register Tests =====

class TestRegister:
    """ทดสอบ POST /auth/register"""

    def test_register_success(self):
        """สมัครสมาชิกสำเร็จ"""
        response = client.post("/auth/register", json={
            "username": f"newuser{TEST_SUFFIX}",
            "password": "test1234",
            "name": "Test User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == f"newuser{TEST_SUFFIX}"
        assert data["user_role"] == "customer"
        assert data["name"] == "Test User"
        assert "password" not in data  # ต้องไม่ส่ง password กลับ

    def test_register_with_email(self):
        """สมัครสมาชิกพร้อม email"""
        response = client.post("/auth/register", json={
            "username": f"emailuser{TEST_SUFFIX}",
            "password": "test1234",
            "email": "testauth@example.com",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "testauth@example.com"

    def test_register_duplicate_username(self):
        """สมัครด้วย username ซ้ำ → 409"""
        payload = {"username": f"dupuser{TEST_SUFFIX}", "password": "test1234"}
        client.post("/auth/register", json=payload)
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 409
        assert "ถูกใช้งานแล้ว" in response.json()["detail"]

    def test_register_duplicate_email(self):
        """สมัครด้วย email ซ้ำ → 409"""
        client.post("/auth/register", json={
            "username": f"emaildup1{TEST_SUFFIX}",
            "password": "test1234",
            "email": "dup_testauth@example.com",
        })
        response = client.post("/auth/register", json={
            "username": f"emaildup2{TEST_SUFFIX}",
            "password": "test1234",
            "email": "dup_testauth@example.com",
        })
        assert response.status_code == 409

    def test_register_short_password(self):
        """Password สั้นเกินไป → 422 validation error"""
        response = client.post("/auth/register", json={
            "username": f"shortpw{TEST_SUFFIX}",
            "password": "ab",
        })
        assert response.status_code == 422

    def test_register_short_username(self):
        """Username สั้นเกินไป → 422 validation error"""
        response = client.post("/auth/register", json={
            "username": "ab",
            "password": "test1234",
        })
        assert response.status_code == 422

    def test_register_invalid_email(self):
        """Email format ผิด → 422 validation error"""
        response = client.post("/auth/register", json={
            "username": f"bademail{TEST_SUFFIX}",
            "password": "test1234",
            "email": "not-an-email",
        })
        assert response.status_code == 422


# ===== Login Tests =====

class TestLogin:
    """ทดสอบ POST /auth/login"""

    def test_login_with_admin(self):
        """Login ด้วย admin (seed data)"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_registered_user(self):
        """Register แล้ว login ด้วย user ใหม่"""
        client.post("/auth/register", json={
            "username": f"logintest{TEST_SUFFIX}",
            "password": "mypassword",
        })
        response = client.post("/auth/login", json={
            "username": f"logintest{TEST_SUFFIX}",
            "password": "mypassword",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self):
        """Login ด้วย password ผิด → 401"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Login ด้วย user ที่ไม่มี → 401"""
        response = client.post("/auth/login", json={
            "username": "nobody_exists",
            "password": "whatever",
        })
        assert response.status_code == 401
