"""
Orders Router

API endpoints สำหรับ orders (staff/admin only)
- GET /orders/ — ดู orders วันนี้
- GET /orders/{id} — ดู order เดี่ยว
- POST /orders/ — สร้าง order + items
- PATCH /orders/{id} — อัปเดต status/finish
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.order import OrderResponse, OrderCreate, OrderUpdate
from app.services.order_service import (
    get_all_orders,
    get_order_by_id,
    create_order,
    update_order,
)

router = APIRouter()


# === Staff/Admin endpoints ===

@router.get("/")
def list_orders(
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ดู orders วันนี้ — staff/admin only"""
    return get_all_orders(db)


@router.get("/{order_id}", response_model=OrderResponse)
def read_order(
    order_id: int,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ดู order เดี่ยว — staff/admin only"""
    return get_order_by_id(db, order_id)


@router.post("/", response_model=OrderResponse, status_code=201)
def add_order(
    data: OrderCreate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """สร้าง order + items — staff/admin only"""
    return create_order(db, current_user, data)


@router.patch("/{order_id}", response_model=OrderResponse)
def edit_order(
    order_id: int,
    data: OrderUpdate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """อัปเดต order status/finish — staff/admin only"""
    return update_order(db, order_id, data)
