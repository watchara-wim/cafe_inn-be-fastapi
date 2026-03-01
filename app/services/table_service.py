"""
Table Service

Business logic สำหรับ tables endpoints
- get_all_tables: ดึงโต๊ะทั้งหมด
- get_table_by_id: ดึงโต๊ะเดี่ยว (404 ถ้าไม่พบ)
- create_table: เพิ่มโต๊ะใหม่
- update_table: แก้ไขโต๊ะ
- delete_table: ลบโต๊ะ
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.table import Table
from app.schemas.table import TableCreate, TableUpdate


def get_all_tables(db: Session) -> list[Table]:
    """ดึง tables ทั้งหมด"""
    return db.query(Table).all()


def get_table_by_id(db: Session, table_id: int) -> Table:
    """ดึง table ตาม ID — 404 ถ้าไม่พบ"""

    table = db.query(Table).filter(Table.table_id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบโต๊ะ",
        )

    return table


def create_table(db: Session, data: TableCreate) -> Table:
    """สร้าง table ใหม่"""

    new_table = Table(
        table_number=data.table_number,
        capacity=data.capacity,
        status=data.status,
    )

    db.add(new_table)
    db.commit()
    db.refresh(new_table)

    return new_table


def update_table(db: Session, table_id: int, data: TableUpdate) -> Table:
    """แก้ไข table — 404 ถ้าไม่พบ"""

    table = get_table_by_id(db, table_id)

    # อัปเดต fields ที่ส่งมา (ไม่ None)
    if data.table_number is not None:
        table.table_number = data.table_number
    if data.capacity is not None:
        table.capacity = data.capacity
    if data.status is not None:
        table.status = data.status

    db.commit()
    db.refresh(table)

    return table


def delete_table(db: Session, table_id: int) -> dict:
    """ลบ table — 404 ถ้าไม่พบ"""

    table = get_table_by_id(db, table_id)

    db.delete(table)
    db.commit()

    return {"message": f"ลบโต๊ะ '{table.table_number}' สำเร็จ"}
