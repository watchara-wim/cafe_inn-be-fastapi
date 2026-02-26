"""
User Schemas

Pydantic models สำหรับ users endpoints
- UserResponse: ข้อมูล user เต็ม (สำหรับ /me, /users/{id})
- UserUpdate: request body สำหรับแก้ไขโปรไฟล์
- UserListResponse: ข้อมูล user แบบย่อ (สำหรับ /users/)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """Response schema สำหรับ user profile — ข้อมูลเต็ม"""
    user_id: int
    username: str
    user_role: str
    name: str | None = None
    email: str | None = None
    tel: str | None = None
    birth_date: datetime | None = None
    point: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response schema สำหรับรายการ users — ข้อมูลย่อ (admin view)"""
    user_id: int
    username: str
    user_role: str
    name: str | None = None
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Request schema สำหรับแก้ไขโปรไฟล์ — ต้องส่ง password ยืนยันเสมอ"""
    password: str = Field(..., description="รหัสผ่านปัจจุบัน (ยืนยันตัวตน)")
    name: str | None = None
    email: EmailStr | None = None
    tel: str | None = None
    new_password: str | None = Field(None, min_length=4, max_length=255)
