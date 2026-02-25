"""
Reservation Model

เทียบเท่า models/Reservations.js
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Reservation(Base, TimestampMixin):
    """Reservations table - การจองโต๊ะ"""
    __tablename__ = "reservations"

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    table_ids = Column(ARRAY(Integer), nullable=False)
    capacity = Column(Integer, nullable=False)
    reservation_time = Column(DateTime, nullable=False)
    customer_amount = Column(Integer, nullable=False)
    reservation_detail = Column(String(255), nullable=True)
    cancel_detail = Column(String(255), nullable=True)
    reservation_status = Column(String(50), nullable=False, default="pending")
    response_at = Column(DateTime, nullable=True)
    finish_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="reservations_as_customer")
    staff = relationship("User", foreign_keys=[staff_id], back_populates="reservations_as_staff")
    orders = relationship("Order", back_populates="reservation")
