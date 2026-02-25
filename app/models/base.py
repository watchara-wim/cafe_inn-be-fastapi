"""
Base Model

Base class สำหรับ SQLAlchemy models ทั้งหมด
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin สำหรับ created_at timestamp"""
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
