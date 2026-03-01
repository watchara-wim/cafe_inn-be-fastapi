"""
Product Service

Business logic สำหรับ products endpoints
- get_all_products: ดึงเมนูทั้งหมด
- get_product_by_id: ดึงเมนูเดี่ยว (404 ถ้าไม่พบ)
- create_product: เพิ่มเมนูใหม่
- update_product: แก้ไขเมนู
- delete_product: ลบเมนู
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_all_products(db: Session) -> list[Product]:
    """ดึง products ทั้งหมด"""
    return db.query(Product).all()


def get_product_by_id(db: Session, product_id: int) -> Product:
    """ดึง product ตาม ID — 404 ถ้าไม่พบ"""

    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบสินค้า",
        )

    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    """สร้าง product ใหม่"""

    new_product = Product(
        product_name=data.product_name,
        price=data.price,
        sweetness_options=data.sweetness_options or [],
        milk_type_options=data.milk_type_options or [],
        type_options=data.type_options or [],
        image=data.image,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    """แก้ไข product — 404 ถ้าไม่พบ"""

    product = get_product_by_id(db, product_id)

    # อัปเดต fields ที่ส่งมา (ไม่ None)
    if data.product_name is not None:
        product.product_name = data.product_name
    if data.price is not None:
        product.price = data.price
    if data.sweetness_options is not None:
        product.sweetness_options = data.sweetness_options
    if data.milk_type_options is not None:
        product.milk_type_options = data.milk_type_options
    if data.type_options is not None:
        product.type_options = data.type_options
    if data.image is not None:
        product.image = data.image

    db.commit()
    db.refresh(product)

    return product


def delete_product(db: Session, product_id: int) -> dict:
    """ลบ product — 404 ถ้าไม่พบ"""

    product = get_product_by_id(db, product_id)

    db.delete(product)
    db.commit()

    return {"message": f"ลบสินค้า '{product.product_name}' สำเร็จ"}
