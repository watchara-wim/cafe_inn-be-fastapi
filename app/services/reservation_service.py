"""
Reservation Service

Business logic สำหรับ reservations endpoints
- get_all_reservations: ดึงรายการจองวันนี้ + customer detail
- get_reservation_by_id: ดึงรายการจองตาม ID
- get_reservation_by_user: ดึงรายการจองของ user วันนี้
- create_reservation: สร้างการจอง + อัปเดต table status → onHold
- update_reservation: อัปเดต status + table status ตาม flow
"""

from datetime import datetime, time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.table import Table
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationUpdate


# Table status mapping ตาม reservation_status (อ้างอิง Node.js ต้นฉบับ)
TABLE_STATUS_MAP = {
    "accepted": "reserved",
    "arrive": "full",
    "cancel": "empty",
}


def _get_today_start() -> datetime:
    """คืน datetime ของจุดเริ่มต้นวันนี้ (00:00:00)"""
    now = datetime.now()
    return datetime.combine(now.date(), time.min)


def _enrich_with_customer_detail(db: Session, reservation: Reservation) -> dict:
    """เพิ่ม customer_detail (name, tel) เข้าไปใน reservation data"""
    data = {
        "reservation_id": reservation.reservation_id,
        "customer_id": reservation.customer_id,
        "staff_id": reservation.staff_id,
        "table_ids": reservation.table_ids,
        "capacity": reservation.capacity,
        "reservation_time": reservation.reservation_time,
        "customer_amount": reservation.customer_amount,
        "reservation_detail": reservation.reservation_detail,
        "cancel_detail": reservation.cancel_detail,
        "reservation_status": reservation.reservation_status,
        "response_at": reservation.response_at,
        "finish_at": reservation.finish_at,
        "created_at": reservation.created_at,
    }

    customer = db.query(User).filter(User.user_id == reservation.customer_id).first()
    if customer:
        data["customer_detail"] = {
            "customer_name": customer.name or "-",
            "customer_tel": customer.tel or "-",
        }
    else:
        data["customer_detail"] = {
            "customer_name": "-",
            "customer_tel": "-",
        }

    return data


def _update_table_statuses(db: Session, table_ids: list[int], new_status: str):
    """อัปเดต status ของหลาย tables พร้อมกัน"""
    for table_id in table_ids:
        table = db.query(Table).filter(Table.table_id == table_id).first()
        if table:
            table.status = new_status


def get_all_reservations(db: Session) -> list[dict]:
    """ดึง reservations วันนี้ เรียงจากใหม่ → เก่า + customer detail"""

    today_start = _get_today_start()

    reservations = (
        db.query(Reservation)
        .filter(Reservation.created_at >= today_start)
        .order_by(Reservation.created_at.desc())
        .all()
    )

    return [_enrich_with_customer_detail(db, r) for r in reservations]


def get_reservation_by_id(db: Session, reservation_id: int) -> dict:
    """ดึง reservation ตาม ID — 404 ถ้าไม่พบ หรือ finish/cancel"""

    reservation = (
        db.query(Reservation)
        .filter(Reservation.reservation_id == reservation_id)
        .first()
    )

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการจอง",
        )

    return _enrich_with_customer_detail(db, reservation)


def get_reservation_by_user(db: Session, user_id: int) -> dict | None:
    """ดึง reservation ล่าสุดของ user วันนี้"""

    today_start = _get_today_start()

    reservation = (
        db.query(Reservation)
        .filter(
            Reservation.customer_id == user_id,
            Reservation.created_at >= today_start,
        )
        .order_by(Reservation.created_at.desc())
        .first()
    )

    if not reservation:
        return None

    return _enrich_with_customer_detail(db, reservation)


def create_reservation(db: Session, user: User, data: ReservationCreate) -> dict:
    """สร้าง reservation ใหม่ + อัปเดต table status → onHold"""

    # ตรวจสอบว่า table_ids ทั้งหมดมีอยู่จริง
    for table_id in data.table_ids:
        table = db.query(Table).filter(Table.table_id == table_id).first()
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ไม่พบโต๊ะ ID {table_id}",
            )

    new_reservation = Reservation(
        customer_id=user.user_id,
        table_ids=data.table_ids,
        capacity=data.capacity,
        reservation_time=data.reservation_time,
        customer_amount=data.customer_amount,
        reservation_detail=data.reservation_detail,
        reservation_status="pending",
    )

    db.add(new_reservation)

    # อัปเดต table status → onHold
    _update_table_statuses(db, data.table_ids, "onHold")

    db.commit()
    db.refresh(new_reservation)

    return _enrich_with_customer_detail(db, new_reservation)


def update_reservation(
    db: Session, reservation_id: int, staff: User, data: ReservationUpdate
) -> dict:
    """อัปเดต reservation status + table status ตาม flow"""

    reservation = (
        db.query(Reservation)
        .filter(Reservation.reservation_id == reservation_id)
        .first()
    )

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการจอง",
        )

    # อัปเดต reservation fields
    reservation.reservation_status = data.reservation_status
    reservation.staff_id = staff.user_id

    if data.response_at is not None:
        reservation.response_at = data.response_at
    if data.finish_at is not None:
        reservation.finish_at = data.finish_at
    if data.cancel_detail is not None:
        reservation.cancel_detail = data.cancel_detail

    # อัปเดต table status ตาม flow
    new_table_status = TABLE_STATUS_MAP.get(data.reservation_status, "onHold")
    _update_table_statuses(db, reservation.table_ids, new_table_status)

    db.commit()
    db.refresh(reservation)

    return _enrich_with_customer_detail(db, reservation)
