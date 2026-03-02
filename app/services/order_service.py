"""
Order Service

Business logic สำหรับ orders endpoints
- get_all_orders: ดึง orders วันนี้ + customer detail + items
- get_order_by_id: ดึง order ตาม ID
- create_order: สร้าง order + items + คำนวณ net_price + table status
- update_order: อัปเดต status + ถ้า finish_at → table status → empty
"""

from datetime import datetime, time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.table import Table
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate


def _get_today_start() -> datetime:
    """คืน datetime ของจุดเริ่มต้นวันนี้ (00:00:00)"""
    now = datetime.now()
    return datetime.combine(now.date(), time.min)


def _enrich_with_customer_detail(db: Session, order: Order) -> dict:
    """เพิ่ม customer_detail (name, point) + items เข้าไปใน order data"""
    data = {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "staff_id": order.staff_id,
        "reservation_id": order.reservation_id,
        "table_ids": order.table_ids or [],
        "order_status": order.order_status,
        "net_price": order.net_price,
        "finish_at": order.finish_at,
        "created_at": order.created_at,
        "items": [
            {
                "id": item.id,
                "order_id": item.order_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "sweetness": item.sweetness,
                "milk_type": item.milk_type,
                "product_type": item.product_type,
                "note": item.note,
            }
            for item in order.items
        ],
    }

    # Customer detail enrichment (ตาม Node.js ต้นฉบับ)
    if order.customer_id:
        customer = db.query(User).filter(User.user_id == order.customer_id).first()
        if customer:
            data["customer_detail"] = {
                "customer_name": customer.name or "-",
                "point": customer.point or 0,
            }
        else:
            data["customer_detail"] = {
                "customer_name": "-",
                "point": 0,
            }
    else:
        data["customer_detail"] = None

    return data


def _update_table_statuses(db: Session, table_ids: list[int], new_status: str):
    """อัปเดต status ของหลาย tables พร้อมกัน"""
    for table_id in table_ids:
        table = db.query(Table).filter(Table.table_id == table_id).first()
        if table:
            table.status = new_status


def get_all_orders(db: Session) -> list[dict]:
    """ดึง orders วันนี้ เรียงจากใหม่ → เก่า + customer detail + items"""

    today_start = _get_today_start()

    orders = (
        db.query(Order)
        .filter(Order.created_at >= today_start)
        .order_by(Order.created_at.desc())
        .all()
    )

    return [_enrich_with_customer_detail(db, o) for o in orders]


def get_order_by_id(db: Session, order_id: int) -> dict:
    """ดึง order ตาม ID — 404 ถ้าไม่พบ"""

    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการสั่งซื้อ",
        )

    return _enrich_with_customer_detail(db, order)


def create_order(db: Session, staff: User, data: OrderCreate) -> dict:
    """สร้าง order + items + คำนวณ net_price + table status → full"""

    # ตรวจสอบ customer_id (ถ้ามี)
    if data.customer_id:
        customer = db.query(User).filter(User.user_id == data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ไม่พบข้อมูลลูกค้า",
            )

    # ตรวจสอบ product_ids + คำนวณ net_price
    net_price = 0
    product_map: dict[int, Product] = {}

    for item in data.items:
        if item.product_id not in product_map:
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ไม่พบสินค้า ID {item.product_id}",
                )
            product_map[item.product_id] = product
        net_price += product_map[item.product_id].price * item.quantity

    # สร้าง order
    new_order = Order(
        customer_id=data.customer_id,
        staff_id=staff.user_id,
        reservation_id=data.reservation_id,
        table_ids=data.table_ids,
        order_status="pending",
        net_price=net_price,
    )

    db.add(new_order)
    db.flush()  # ให้ได้ order_id ก่อนสร้าง items

    # สร้าง order items
    for item in data.items:
        order_item = OrderItem(
            order_id=new_order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            sweetness=item.sweetness,
            milk_type=item.milk_type,
            product_type=item.product_type,
            note=item.note,
        )
        db.add(order_item)

    # อัปเดต table status → full (เฉพาะ order ที่ผูกกับ table)
    if data.table_ids:
        _update_table_statuses(db, data.table_ids, "full")

    db.commit()
    db.refresh(new_order)

    return _enrich_with_customer_detail(db, new_order)


def update_order(db: Session, order_id: int, data: OrderUpdate) -> dict:
    """อัปเดต order status + ถ้า finish_at → table status → empty"""

    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการสั่งซื้อ",
        )

    # อัปเดต fields ที่ส่งมา
    if data.order_status is not None:
        order.order_status = data.order_status
    if data.finish_at is not None:
        order.finish_at = data.finish_at

        # ถ้า set finish_at + order ผูกกับ table → table status → empty
        if order.table_ids:
            _update_table_statuses(db, order.table_ids, "empty")

    db.commit()
    db.refresh(order)

    return _enrich_with_customer_detail(db, order)
