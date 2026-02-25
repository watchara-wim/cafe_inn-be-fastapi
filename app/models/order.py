from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    staff_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reservation_id = Column(Integer, ForeignKey("reservations.reservation_id"), nullable=True)
    table_ids = Column(ARRAY(Integer), nullable=False, default=[])
    order_status = Column(String(50), nullable=False, default="pending")
    net_price = Column(Integer, nullable=False)
    finish_at = Column(DateTime, nullable=True)

    customer = relationship("User", foreign_keys=[customer_id], back_populates="orders_as_customer")
    staff = relationship("User", foreign_keys=[staff_id], back_populates="orders_as_staff")
    reservation = relationship("Reservation", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    sweetness = Column(String(50), nullable=True)
    milk_type = Column(String(50), nullable=True)
    product_type = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
