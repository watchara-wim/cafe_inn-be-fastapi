"""
User Model

เทียบเท่า models/Users.js + models/User_Informations.js
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Users table - สำหรับ authentication"""
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

    reservations_as_customer = relationship("Reservation", foreign_keys="Reservation.customer_id", back_populates="customer")
    reservations_as_staff = relationship("Reservation", foreign_keys="Reservation.staff_id", back_populates="staff")
    orders_as_customer = relationship("Order", foreign_keys="Order.customer_id", back_populates="customer")
    orders_as_staff = relationship("Order", foreign_keys="Order.staff_id", back_populates="staff")
