"""
Users Router

API endpoints สำหรับ users
- GET /users/me — ดูข้อมูลตัวเอง
- PUT /users/me — แก้ไขข้อมูล (ต้องยืนยัน password)
- GET /users/ — ดูรายการ users ทั้งหมด (admin only)
- GET /users/{id} — ดูข้อมูล user ตาม ID (admin only)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.services.user_service import (
    get_user_profile,
    update_user_profile,
    get_all_users,
    get_user_by_id,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_my_profile(current_user: User = Depends(get_current_user)):
    """ดูข้อมูลตัวเอง — ต้อง login"""
    return get_user_profile(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """แก้ไขข้อมูลตัวเอง — ต้องยืนยัน password ปัจจุบัน"""
    return update_user_profile(db, current_user, data)


@router.get("/", response_model=list[UserListResponse])
def list_users(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """ดูรายการ users ทั้งหมด — admin only"""
    return get_all_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """ดูข้อมูล user ตาม ID — admin only"""
    return get_user_by_id(db, user_id)
