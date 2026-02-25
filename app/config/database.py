"""
Database Configuration

เทียบเท่า config/database.js ใน Sequelize
- สร้าง SQLAlchemy engine
- สร้าง SessionLocal สำหรับ database sessions
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

# SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency สำหรับ inject database session เข้า route handlers

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
