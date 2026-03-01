"""
Dependencies

FastAPI dependencies สำหรับ inject เข้า route handlers
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# OAuth2 scheme สำหรับ JWT Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# OAuth2 scheme แบบ optional — ไม่ 401 ถ้าไม่มี token
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Dependency สำหรับดึง current user จาก JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user

def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    db: Session = Depends(get_db)
) -> User | None:
    """Dependency แบบ optional — คืน User ถ้ามี token ที่ valid, คืน None ถ้าไม่มี"""
    if token is None:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    return db.query(User).filter(User.user_id == int(user_id)).first()

def require_role(allowed_roles: list[str]):
    """Dependency factory สำหรับตรวจสอบ user role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
