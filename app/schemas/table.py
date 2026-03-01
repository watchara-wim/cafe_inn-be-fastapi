"""
Table Schemas

Pydantic models สำหรับ Table API
- TableResponse: ข้อมูลโต๊ะ (response)
- TableCreate: สร้างโต๊ะใหม่
- TableUpdate: แก้ไขโต๊ะ
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TableResponse(BaseModel):
    """Response schema สำหรับ table"""
    model_config = ConfigDict(from_attributes=True)

    table_id: int
    table_number: str
    capacity: int
    status: str
    last_update: datetime | None = None
    created_at: datetime


class TableCreate(BaseModel):
    """Request schema สำหรับสร้างโต๊ะใหม่"""
    table_number: str = Field(..., min_length=1, max_length=255)
    capacity: int = Field(..., ge=1)
    status: str = Field("empty", max_length=255)


class TableUpdate(BaseModel):
    """Request schema สำหรับแก้ไขโต๊ะ — ทุก field optional"""
    table_number: str | None = Field(None, min_length=1, max_length=255)
    capacity: int | None = Field(None, ge=1)
    status: str | None = Field(None, max_length=255)
