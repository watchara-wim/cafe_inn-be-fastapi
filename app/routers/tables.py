"""
Tables Router

API endpoints สำหรับ tables
- GET /tables/ - ดูโต๊ะทั้งหมด
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.table import Table
from app.schemas.table import TableResponse

router = APIRouter()


@router.get("/", response_model=list[TableResponse])
def get_all_tables(db: Session = Depends(get_db)):
    """ดูโต๊ะทั้งหมด"""
    tables = db.query(Table).all()
    return tables
