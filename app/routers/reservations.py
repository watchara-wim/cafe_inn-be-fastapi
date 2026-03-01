"""
Reservations Router

API endpoints สำหรับ reservations
- GET /reservations/ — ดูรายการจองทั้งหมดวันนี้ (staff/admin)
- GET /reservations/me — ดูการจองของตัวเองวันนี้ (ทุก role)
- GET /reservations/{id} — ดูรายการจองเดี่ยว (staff/admin)
- POST /reservations/ — สร้างการจอง (ทุก role)
- PATCH /reservations/{id} — อัปเดต status (staff/admin)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.reservation import ReservationResponse, ReservationCreate, ReservationUpdate
from app.services.reservation_service import (
    get_all_reservations,
    get_reservation_by_id,
    get_reservation_by_user,
    create_reservation,
    update_reservation,
)

router = APIRouter()


# === Authenticated endpoints (ทุก role) ===

@router.get("/me")
def my_reservation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ดูการจองของตัวเองวันนี้"""
    reservation = get_reservation_by_user(db, current_user.user_id)
    if reservation is None:
        return {"reservation": None}
    return reservation


@router.post("/", response_model=ReservationResponse, status_code=201)
def add_reservation(
    data: ReservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """สร้างการจองใหม่ — ทุก role"""
    return create_reservation(db, current_user, data)


# === Staff/Admin endpoints ===

@router.get("/")
def list_reservations(
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ดูรายการจองทั้งหมดวันนี้ — staff/admin only"""
    return get_all_reservations(db)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def read_reservation(
    reservation_id: int,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """ดูรายการจองเดี่ยว — staff/admin only"""
    return get_reservation_by_id(db, reservation_id)


@router.patch("/{reservation_id}", response_model=ReservationResponse)
def edit_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    current_user: User = Depends(require_role(["staff", "admin"])),
    db: Session = Depends(get_db),
):
    """อัปเดต status การจอง — staff/admin only"""
    return update_reservation(db, reservation_id, current_user, data)
