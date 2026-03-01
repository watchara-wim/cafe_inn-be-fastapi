"""
Products Tests

Integration tests สำหรับ products endpoints
- GET /products/ — ดูเมนูทั้งหมด (public)
- GET /products/{id} — ดูเมนูเดี่ยว (public)
- POST /products/ — เพิ่มเมนู (staff/admin)
- PUT /products/{id} — แก้เมนู (staff/admin)
- DELETE /products/{id} — ลบเมนู (staff/admin)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
from app.models.product import Product
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

TEST_PREFIX = "TESTPROD_"
TEST_SUFFIX = "_testprod"


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
        "username": f"prodcust{TEST_SUFFIX}",
        "password": "test1234",
    })
    res = client.post("/auth/login", json={
        "username": f"prodcust{TEST_SUFFIX}",
        "password": "test1234",
    })
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_test_product(token: str, name: str = "Test Coffee") -> dict:
    """สร้าง test product แล้วคืน response data"""
    res = client.post("/products/", headers=auth_header(token), json={
        "product_name": f"{TEST_PREFIX}{name}",
        "price": 65,
        "sweetness_options": ["25%", "50%", "75%", "100%"],
        "type_options": ["ร้อน", "เย็น", "ปั่น"],
    })
    return res.json()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """ลบ test products + test users ก่อนและหลังแต่ละ test"""
    db = TestingSessionLocal()
    db.query(Product).filter(Product.product_name.like(f"{TEST_PREFIX}%")).delete(synchronize_session=False)
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    yield
    db.query(Product).filter(Product.product_name.like(f"{TEST_PREFIX}%")).delete(synchronize_session=False)
    db.query(User).filter(User.username.like(f"%{TEST_SUFFIX}")).delete(synchronize_session=False)
    db.commit()
    db.close()


# ===== GET /products/ (public) =====

class TestListProducts:
    """ทดสอบ GET /products/"""

    def test_list_products_public(self):
        """ดูเมนูทั้งหมดได้โดยไม่ต้อง login"""
        response = client.get("/products/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_products_public_fields(self):
        """Public response มีเฉพาะ id, name, price, image — ไม่มี options"""
        token = get_admin_token()
        create_test_product(token)

        response = client.get("/products/")
        assert response.status_code == 200
        products = response.json()

        test_product = next(p for p in products if p["product_name"].startswith(TEST_PREFIX))
        assert "product_id" in test_product
        assert "product_name" in test_product
        assert "price" in test_product
        # public response ต้องไม่มี options
        assert "sweetness_options" not in test_product
        assert "milk_type_options" not in test_product
        assert "type_options" not in test_product

    def test_list_products_admin_full_fields(self):
        """admin เรียก GET /products/ → ได้ options fields ด้วย"""
        token = get_admin_token()
        create_test_product(token)

        response = client.get("/products/", headers=auth_header(token))
        assert response.status_code == 200
        products = response.json()

        test_product = next(p for p in products if p["product_name"].startswith(TEST_PREFIX))
        assert "sweetness_options" in test_product
        assert "type_options" in test_product
        assert len(test_product["sweetness_options"]) == 4


# ===== GET /products/{id} (public) =====

class TestGetProduct:
    """ทดสอบ GET /products/{id}"""

    def test_get_product_success(self):
        """ดูเมนูเดี่ยวสำเร็จ"""
        token = get_admin_token()
        product = create_test_product(token)

        response = client.get(f"/products/{product['product_id']}")
        assert response.status_code == 200
        assert response.json()["product_name"] == f"{TEST_PREFIX}Test Coffee"

    def test_get_product_not_found(self):
        """ไม่พบเมนู → 404"""
        response = client.get("/products/999999")
        assert response.status_code == 404

    def test_get_product_admin_full_fields(self):
        """admin เรียก GET /products/{id} → ได้ options fields ด้วย"""
        token = get_admin_token()
        product = create_test_product(token)

        response = client.get(f"/products/{product['product_id']}", headers=auth_header(token))
        assert response.status_code == 200
        data = response.json()
        assert "sweetness_options" in data
        assert "type_options" in data
        assert len(data["sweetness_options"]) == 4


# ===== POST /products/ (staff/admin) =====

class TestCreateProduct:
    """ทดสอบ POST /products/"""

    def test_create_product_admin(self):
        """admin สร้างเมนูสำเร็จ — response มี options ครบ"""
        token = get_admin_token()

        response = client.post("/products/", headers=auth_header(token), json={
            "product_name": f"{TEST_PREFIX}Latte",
            "price": 75,
            "sweetness_options": ["50%", "100%"],
            "milk_type_options": ["นมสด", "นมข้น"],
            "type_options": ["ร้อน", "เย็น"],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["product_name"] == f"{TEST_PREFIX}Latte"
        assert data["price"] == 75
        assert len(data["sweetness_options"]) == 2
        assert len(data["type_options"]) == 2

    def test_create_product_customer_forbidden(self):
        """customer ไม่มีสิทธิ์สร้างเมนู → 403"""
        token = create_customer_and_get_token()

        response = client.post("/products/", headers=auth_header(token), json={
            "product_name": f"{TEST_PREFIX}Forbidden",
            "price": 50,
        })
        assert response.status_code == 403


# ===== PUT /products/{id} (staff/admin) =====

class TestUpdateProduct:
    """ทดสอบ PUT /products/{id}"""

    def test_update_product_success(self):
        """admin แก้ไขเมนูสำเร็จ"""
        token = get_admin_token()
        product = create_test_product(token)

        response = client.put(
            f"/products/{product['product_id']}",
            headers=auth_header(token),
            json={"price": 80, "product_name": f"{TEST_PREFIX}Updated Coffee"},
        )
        assert response.status_code == 200
        assert response.json()["price"] == 80
        assert response.json()["product_name"] == f"{TEST_PREFIX}Updated Coffee"

    def test_update_product_not_found(self):
        """แก้ไขเมนูที่ไม่มี → 404"""
        token = get_admin_token()

        response = client.put(
            "/products/999999",
            headers=auth_header(token),
            json={"price": 100},
        )
        assert response.status_code == 404


# ===== DELETE /products/{id} (staff/admin) =====

class TestDeleteProduct:
    """ทดสอบ DELETE /products/{id}"""

    def test_delete_product_success(self):
        """admin ลบเมนูสำเร็จ"""
        token = get_admin_token()
        product = create_test_product(token)

        response = client.delete(
            f"/products/{product['product_id']}",
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert "สำเร็จ" in response.json()["message"]

        # ต้องไม่พบเมนูนี้อีก
        get_res = client.get(f"/products/{product['product_id']}")
        assert get_res.status_code == 404

    def test_delete_product_customer_forbidden(self):
        """customer ไม่มีสิทธิ์ลบเมนู → 403"""
        token_admin = get_admin_token()
        product = create_test_product(token_admin)
        token_customer = create_customer_and_get_token()

        response = client.delete(
            f"/products/{product['product_id']}",
            headers=auth_header(token_customer),
        )
        assert response.status_code == 403
