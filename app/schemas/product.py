"""
Product Schemas

Pydantic models สำหรับ Product API
- ProductPublicResponse: ข้อมูลสำหรับ public (id, name, price, image)
- ProductResponse: ข้อมูลเต็ม (staff/admin)
- ProductCreate: สร้างเมนูใหม่
- ProductUpdate: แก้ไขเมนู
"""

from pydantic import BaseModel, ConfigDict, Field


class ProductPublicResponse(BaseModel):
    """Response schema สำหรับ public — เฉพาะข้อมูลที่ใช้แสดงบน frontend"""
    product_id: int
    product_name: str
    price: int
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """Response schema สำหรับ staff/admin — ข้อมูลเต็ม รวม options"""
    product_id: int
    product_name: str
    price: int
    sweetness_options: list[str] | None = []
    milk_type_options: list[str] | None = []
    type_options: list[str] | None = []
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """Request schema สำหรับสร้างเมนูใหม่"""
    product_name: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., ge=0)
    sweetness_options: list[str] | None = []
    milk_type_options: list[str] | None = []
    type_options: list[str] | None = []
    image: str | None = None


class ProductUpdate(BaseModel):
    """Request schema สำหรับแก้ไขเมนู — ทุก field optional"""
    product_name: str | None = Field(None, min_length=1, max_length=255)
    price: int | None = Field(None, ge=0)
    sweetness_options: list[str] | None = None
    milk_type_options: list[str] | None = None
    type_options: list[str] | None = None
    image: str | None = None
