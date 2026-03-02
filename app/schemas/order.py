"""
Order Schemas

Pydantic models สำหรับ Order API
- OrderItemCreate: สร้าง item ใน order
- OrderItemResponse: ข้อมูล item สำหรับ response
- OrderCreate: สร้าง order ใหม่
- OrderUpdate: อัปเดต order status
- OrderResponse: ข้อมูล order เต็ม + items + customer detail
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    """Request schema สำหรับ item ภายใน order"""
    product_id: int
    quantity: int = Field(1, ge=1)
    sweetness: str | None = None
    milk_type: str | None = None
    product_type: str | None = None
    note: str | None = None


class OrderItemResponse(BaseModel):
    """Response schema สำหรับ item ภายใน order"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    sweetness: str | None = None
    milk_type: str | None = None
    product_type: str | None = None
    note: str | None = None


class CustomerDetail(BaseModel):
    """ข้อมูลลูกค้าแนบกับ order"""
    customer_name: str | None = None
    point: int | None = None


class OrderCreate(BaseModel):
    """Request schema สำหรับสร้าง order"""
    customer_id: int | None = None
    table_ids: list[int] = Field(default_factory=list)
    reservation_id: int | None = None
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
    """Request schema สำหรับอัปเดต order — staff/admin"""
    order_status: str | None = Field(None, max_length=50)
    finish_at: datetime | None = None


class OrderResponse(BaseModel):
    """Response schema สำหรับ order เต็ม"""
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int | None = None
    staff_id: int
    reservation_id: int | None = None
    table_ids: list[int]
    order_status: str
    net_price: int
    finish_at: datetime | None = None
    created_at: datetime
    items: list[OrderItemResponse] = []
    customer_detail: CustomerDetail | None = None
