"""
Products Router

API endpoints สำหรับ products
- GET /products/ — ดูเมนูทั้งหมด (public: 4 fields, staff/admin: ทุก fields)
- GET /products/{id} — ดูเมนูเดี่ยว (public: 4 fields, staff/admin: ทุก fields)
- POST /products/ — เพิ่มเมนู (staff/admin)
- PUT /products/{id} — แก้เมนู (staff/admin)
- DELETE /products/{id} — ลบเมนู (staff/admin)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.deps import get_current_user_optional, require_role
from app.models.user import User
from app.schemas.product import ProductPublicResponse, ProductResponse, ProductCreate, ProductUpdate
from app.services.product_service import (
    get_all_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
)

router = APIRouter()


STAFF_ROLES = ["staff", "admin"]


# === Public / Role-based endpoints ===

@router.get("/")
def list_products(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """ดูเมนูทั้งหมด — staff/admin ได้ข้อมูลครบ, คนอื่นได้เฉพาะข้อมูลพื้นฐาน"""
    products = get_all_products(db)

    if current_user and current_user.user_role in STAFF_ROLES:
        return [ProductResponse.model_validate(p) for p in products]
    return [ProductPublicResponse.model_validate(p) for p in products]


@router.get("/{product_id}")
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """ดูเมนูเดี่ยว — staff/admin ได้ข้อมูลครบ, คนอื่นได้เฉพาะข้อมูลพื้นฐาน"""
    product = get_product_by_id(db, product_id)

    if current_user and current_user.user_role in STAFF_ROLES:
        return ProductResponse.model_validate(product)
    return ProductPublicResponse.model_validate(product)


# === Staff/Admin endpoints ===

@router.post("/", response_model=ProductResponse, status_code=201)
def add_product(
    data: ProductCreate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """เพิ่มเมนูใหม่ — staff/admin only"""
    return create_product(db, data)


@router.put("/{product_id}", response_model=ProductResponse)
def edit_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """แก้ไขเมนู — staff/admin only"""
    return update_product(db, product_id, data)


@router.delete("/{product_id}")
def remove_product(
    product_id: int,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ลบเมนู — staff/admin only"""
    return delete_product(db, product_id)
