"""
Table Schemas

Pydantic models สำหรับ Table API
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TableResponse(BaseModel):
    """Response schema สำหรับ table"""
    table_id: int
    table_number: str
    capacity: int
    status: str
    last_update: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
