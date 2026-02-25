"""
Auth Router

API endpoints สำหรับ authentication
- POST /auth/login - เข้าสู่ระบบ
- POST /auth/register - สมัครสมาชิก
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.auth import Token, LoginRequest, RegisterRequest, RegisterResponse
from app.services.auth_service import authenticate_user, register_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """เข้าสู่ระบบ — รับ username + password, คืน JWT token"""
    return authenticate_user(db, credentials.username, credentials.password)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """สมัครสมาชิก — สร้าง user ใหม่ (role = customer)"""
    return register_user(
        db,
        username=data.username,
        password=data.password,
        name=data.name,
        email=data.email,
        tel=data.tel,
    )
