"""
Orders Tests

Integration tests สำหรับ orders endpoints
- POST /orders/ — สร้าง order + items (staff/admin)
- GET /orders/ — ดู orders วันนี้ (staff/admin)
- GET /orders/{id} — ดู order เดี่ยว (staff/admin)
- PATCH /orders/{id} — อัปเดต status/finish (staff/admin)
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.config.settings import settings
from app.models.order import Order, OrderItem
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

TEST_PREFIX = "TESTORD_"
TEST_SUFFIX = "_testord"


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
    username = f"ordcust{suffix}{TEST_SUFFIX}"
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


def create_test_table(token: str, number: str = "80") -> dict:
    """สร้าง test table แล้วคืน response data"""
    res = client.post("/tables/", headers=auth_header(token), json={
        "table_number": f"{TEST_PREFIX}{number}",
        "capacity": 4,
    })
    return res.json()


def get_seed_product_id() -> int:
    """ดึง product_id จาก seed data (public endpoint)"""
    res = client.get("/products/")
    products = res.json()
    assert len(products) > 0, "ต้องมี seed products"
    return products[0]["product_id"]


def create_test_order(token: str, product_id: int, table_ids: list[int] | None = None) -> dict:
    """สร้าง test order แล้วคืน response data"""
    payload = {
        "table_ids": table_ids or [],
        "items": [
            {
                "product_id": product_id,
                "quantity": 2,
                "sweetness": "50%",
                "milk_type": "oat",
                "note": f"{TEST_PREFIX}test note",
            }
        ],
    }
    res = client.post("/orders/", headers=auth_header(token), json=payload)
    return res.json()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """ลบ test data ก่อนและหลังแต่ละ test"""
    db = TestingSessionLocal()
    _cleanup(db)
    yield
    _cleanup(db)
    db.close()


def _cleanup(db):
    """ลบ test data ทั้งหมด"""
    # ลบ order items ที่มี note ขึ้นต้นด้วย TEST_PREFIX
    db.query(OrderItem).filter(
        OrderItem.note.like(f"{TEST_PREFIX}%")
    ).delete(synchronize_session=False)
    # ลบ orders ที่ไม่มี items แล้ว (orphaned from test)
    # ใช้วิธีหา orders ที่ table_ids ว่าง + net_price ที่สร้างจาก test
    # ง่ายกว่า: ลบ orders ที่มี table_ids ผูกกับ test tables
    db.query(Order).filter(
        Order.order_id.notin_(
            db.query(OrderItem.order_id).distinct()
        )
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


# ===== POST /orders/ =====

class TestCreateOrder:
    """ทดสอบ POST /orders/"""

    def test_create_order_success(self):
        """staff สร้าง order สำเร็จ + net_price คำนวณถูกต้อง"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()

        # ดึง product price เพื่อตรวจสอบ
        product_res = client.get(f"/products/{product_id}", headers=auth_header(admin_token))
        product_price = product_res.json()["price"]

        order = create_test_order(admin_token, product_id)

        assert order["order_status"] == "pending"
        assert order["net_price"] == product_price * 2  # quantity = 2
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 2
        assert order["items"][0]["sweetness"] == "50%"

    def test_create_order_table_status_full(self):
        """สร้าง order ผูก table → table status เปลี่ยนเป็น full"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()
        table = create_test_table(admin_token, "81")

        order = create_test_order(admin_token, product_id, [table["table_id"]])

        assert order["table_ids"] == [table["table_id"]]

        # ตรวจ table status
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "full"

    def test_create_order_takeaway_no_table_update(self):
        """สร้าง order แบบ take-home (ไม่ผูก table) → ไม่เปลี่ยน table status"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()

        order = create_test_order(admin_token, product_id)  # no table_ids

        assert order["table_ids"] == []
        assert order["order_status"] == "pending"

    def test_create_order_invalid_product(self):
        """product ไม่มี → 404"""
        admin_token = get_admin_token()

        res = client.post("/orders/", headers=auth_header(admin_token), json={
            "items": [{"product_id": 999999, "quantity": 1}],
        })
        assert res.status_code == 404

    def test_create_order_no_auth(self):
        """ไม่มี token → 401"""
        res = client.post("/orders/", json={
            "items": [{"product_id": 1, "quantity": 1}],
        })
        assert res.status_code == 401

    def test_create_order_customer_forbidden(self):
        """customer สร้าง order ไม่ได้ → 403"""
        customer_token = create_customer_and_get_token("1")
        product_id = get_seed_product_id()

        res = client.post("/orders/", headers=auth_header(customer_token), json={
            "items": [{"product_id": product_id, "quantity": 1}],
        })
        assert res.status_code == 403


# ===== GET /orders/ =====

class TestListOrders:
    """ทดสอบ GET /orders/"""

    def test_list_orders_admin(self):
        """admin ดู orders สำเร็จ"""
        admin_token = get_admin_token()

        res = client.get("/orders/", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_orders_customer_forbidden(self):
        """customer ดู orders ไม่ได้ → 403"""
        customer_token = create_customer_and_get_token("2")

        res = client.get("/orders/", headers=auth_header(customer_token))
        assert res.status_code == 403


# ===== GET /orders/{id} =====

class TestGetOrder:
    """ทดสอบ GET /orders/{id}"""

    def test_get_order_by_id_success(self):
        """admin ดู order เดี่ยวสำเร็จ"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()
        order = create_test_order(admin_token, product_id)

        res = client.get(f"/orders/{order['order_id']}", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert res.json()["order_id"] == order["order_id"]
        assert len(res.json()["items"]) == 1

    def test_get_order_not_found(self):
        """order ไม่มี → 404"""
        admin_token = get_admin_token()

        res = client.get("/orders/999999", headers=auth_header(admin_token))
        assert res.status_code == 404


# ===== PATCH /orders/{id} =====

class TestUpdateOrder:
    """ทดสอบ PATCH /orders/{id}"""

    def test_update_order_status(self):
        """อัปเดต order status สำเร็จ"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()
        order = create_test_order(admin_token, product_id)

        res = client.patch(
            f"/orders/{order['order_id']}",
            headers=auth_header(admin_token),
            json={"order_status": "completed"},
        )
        assert res.status_code == 200
        assert res.json()["order_status"] == "completed"

    def test_finish_order_table_empty(self):
        """set finish_at → table status เปลี่ยนเป็น empty"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()
        table = create_test_table(admin_token, "82")

        order = create_test_order(admin_token, product_id, [table["table_id"]])

        # ตรวจว่า table เป็น full
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "full"

        # set finish_at
        res = client.patch(
            f"/orders/{order['order_id']}",
            headers=auth_header(admin_token),
            json={
                "order_status": "completed",
                "finish_at": datetime.now().isoformat(),
            },
        )
        assert res.status_code == 200

        # ตรวจ table กลับเป็น empty
        table_res = client.get(f"/tables/{table['table_id']}", headers=auth_header(admin_token))
        assert table_res.json()["status"] == "empty"

    def test_finish_takeaway_no_table_update(self):
        """finish order take-home → ไม่ crash (table_ids ว่าง)"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()

        order = create_test_order(admin_token, product_id)  # no table_ids

        res = client.patch(
            f"/orders/{order['order_id']}",
            headers=auth_header(admin_token),
            json={
                "order_status": "completed",
                "finish_at": datetime.now().isoformat(),
            },
        )
        assert res.status_code == 200
        assert res.json()["order_status"] == "completed"

    def test_create_order_with_customer_id(self):
        """สร้าง order แนบ customer_id + customer_detail ใน response"""
        admin_token = get_admin_token()
        product_id = get_seed_product_id()
        customer_token = create_customer_and_get_token("3")

        # ดึง customer user_id
        me_res = client.get("/users/me", headers=auth_header(customer_token))
        customer_id = me_res.json()["user_id"]

        res = client.post("/orders/", headers=auth_header(admin_token), json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "note": f"{TEST_PREFIX}customer order",
                }
            ],
        })
        assert res.status_code == 201
        assert res.json()["customer_id"] == customer_id
        assert res.json()["customer_detail"] is not None
