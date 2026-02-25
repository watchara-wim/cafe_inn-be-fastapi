from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    sweetness_options = Column(ARRAY(String), default=[])
    milk_type_options = Column(ARRAY(String), default=[])
    type_options = Column(ARRAY(String), default=[])

    image = Column(String(255), nullable=True)

    order_items = relationship("OrderItem", back_populates="product")
