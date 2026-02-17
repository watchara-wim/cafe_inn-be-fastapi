from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_role = Column(String(20), nullable=False)  # 'customer', 'staff', 'admin'
    is_verified = Column(Boolean, default=False)

    # ข้อมูลส่วนตัว
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    tel = Column(String(20), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    point = Column(Integer, default=0)

    # Password reset
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
