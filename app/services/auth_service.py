"""
Auth Service

Business logic สำหรับ authentication
- login: ตรวจสอบ credentials + สร้าง JWT
- register: สร้าง user ใหม่ + validation
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token


def authenticate_user(db: Session, username: str, password: str) -> dict:
    """ตรวจสอบ username + password แล้วคืน JWT token"""

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.user_id), "username": user.username, "role": user.user_role}
    )

    return {"access_token": access_token, "token_type": "bearer"}


def register_user(db: Session, username: str, password: str, name: str | None = None,
                   email: str | None = None, tel: str | None = None) -> User:
    """สร้าง user ใหม่ (role = customer)"""

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ชื่อผู้ใช้นี้ถูกใช้งานแล้ว",
        )

    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="อีเมลนี้ถูกใช้งานแล้ว",
        )

    new_user = User(
        username=username,
        password=get_password_hash(password),
        user_role="customer",
        name=name,
        email=email,
        tel=tel,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
