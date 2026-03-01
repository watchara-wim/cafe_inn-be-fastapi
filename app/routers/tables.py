"""
Tables Router

API endpoints สำหรับ tables
- GET /tables/ — ดูโต๊ะทั้งหมด (public)
- GET /tables/{id} — ดูโต๊ะเดี่ยว (staff/admin)
- POST /tables/ — เพิ่มโต๊ะ (admin)
- PUT /tables/{id} — แก้ไขโต๊ะ (staff/admin)
- DELETE /tables/{id} — ลบโต๊ะ (admin)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.table import TableResponse, TableCreate, TableUpdate
from app.services.table_service import (
    get_all_tables,
    get_table_by_id,
    create_table,
    update_table,
    delete_table,
)

router = APIRouter()


# === Public endpoints ===

@router.get("/", response_model=list[TableResponse])
def list_tables(db: Session = Depends(get_db)):
    """ดูโต๊ะทั้งหมด — public"""
    return get_all_tables(db)


# === Staff/Admin endpoints ===

@router.get("/{table_id}", response_model=TableResponse)
def read_table(
    table_id: int,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ดูโต๊ะเดี่ยว — staff/admin only"""
    return get_table_by_id(db, table_id)


@router.post("/", response_model=TableResponse, status_code=201)
def add_table(
    data: TableCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """เพิ่มโต๊ะใหม่ — admin only"""
    return create_table(db, data)


@router.put("/{table_id}", response_model=TableResponse)
def edit_table(
    table_id: int,
    data: TableUpdate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """แก้ไขโต๊ะ — staff/admin only"""
    return update_table(db, table_id, data)


@router.delete("/{table_id}")
def remove_table(
    table_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """ลบโต๊ะ — admin only"""
    return delete_table(db, table_id)
