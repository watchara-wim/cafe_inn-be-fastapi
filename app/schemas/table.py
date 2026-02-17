from datetime import datetime

from pydantic import BaseModel


class TableResponse(BaseModel):
    table_id: int
    table_number: str
    capacity: int
    status: str
    last_update: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
