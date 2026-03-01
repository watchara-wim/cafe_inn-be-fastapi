"""
Reservation Schemas

Pydantic models สำหรับ Reservation API
- ReservationResponse: ข้อมูลการจอง + customer detail
- ReservationCreate: สร้างการจอง
- ReservationUpdate: อัปเดต status (staff)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerDetail(BaseModel):
    """ข้อมูลลูกค้าแนบกับ reservation"""
    customer_name: str | None = None
    customer_tel: str | None = None


class ReservationResponse(BaseModel):
    """Response schema สำหรับ reservation"""
    model_config = ConfigDict(from_attributes=True)

    reservation_id: int
    customer_id: int
    staff_id: int | None = None
    table_ids: list[int]
    capacity: int
    reservation_time: datetime
    customer_amount: int
    reservation_detail: str | None = None
    cancel_detail: str | None = None
    reservation_status: str
    response_at: datetime | None = None
    finish_at: datetime | None = None
    created_at: datetime
    customer_detail: CustomerDetail | None = None


class ReservationCreate(BaseModel):
    """Request schema สำหรับสร้างการจอง"""
    table_ids: list[int] = Field(..., min_length=1)
    capacity: int = Field(..., ge=1)
    reservation_time: datetime
    customer_amount: int = Field(..., ge=1)
    reservation_detail: str | None = None


class ReservationUpdate(BaseModel):
    """Request schema สำหรับอัปเดต status — staff/admin"""
    reservation_status: str = Field(..., max_length=50)
    response_at: datetime | None = None
    finish_at: datetime | None = None
    cancel_detail: str | None = None
