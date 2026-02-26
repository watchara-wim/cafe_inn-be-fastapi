"""
User Service

Business logic สำหรับ users endpoints
- get_user_profile: ดูข้อมูลตัวเอง
- update_user_profile: แก้ไขข้อมูล (ต้องยืนยัน password)
- get_all_users: ดูรายการ users ทั้งหมด (admin)
- get_user_by_id: ดูข้อมูล user ตาม ID (admin)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.schemas.user import UserUpdate


def get_user_profile(user: User) -> User:
    """คืน user object สำหรับ /me — ใช้ current_user ตรง ๆ"""
    return user


def update_user_profile(db: Session, user: User, data: UserUpdate) -> User:
    """แก้ไขโปรไฟล์ user — ต้องยืนยัน password ปัจจุบันก่อน"""

    # ตรวจสอบ password ปัจจุบัน
    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รหัสผ่านไม่ถูกต้อง",
        )

    if data.name is not None:
        user.name = data.name
    if data.tel is not None:
        user.tel = data.tel
    if data.email is not None:
        """ เช็ค email ซ้ำ """
        existing = db.query(User).filter(User.email == data.email, User.user_id != user.user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="อีเมลนี้ถูกใช้งานแล้ว",
            )
        user.email = data.email
    if data.new_password:
        user.password = get_password_hash(data.new_password)

    db.commit()
    db.refresh(user)

    return user


def get_all_users(db: Session) -> list[User]:
    """ดึง users ทั้งหมด (admin only)"""
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int) -> User:
    """ดึง user ตาม ID — 404 ถ้าไม่พบ (admin only)"""

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบผู้ใช้งาน",
        )

    return user
