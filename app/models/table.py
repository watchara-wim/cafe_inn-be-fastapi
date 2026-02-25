"""
Table Model

เทียบเท่า models/Tables.js
"""

from sqlalchemy import Column, Integer, String, DateTime

from app.models.base import Base, TimestampMixin


class Table(Base, TimestampMixin):
    """Tables table - โต๊ะในร้าน"""
    __tablename__ = "tables"

    table_id = Column(Integer, primary_key=True, autoincrement=True)
    table_number = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(255), nullable=False, default="empty")  # 'empty', 'onHold', 'reserved', 'full'
    last_update = Column(DateTime, nullable=True)
