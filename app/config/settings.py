"""
Application Settings

เทียบเท่า dotenv config ใน Node.js
- ใช้ pydantic-settings สำหรับ type-safe configuration
- โหลดค่าจาก .env file อัตโนมัติ
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/cafe_inn"

    # JWT Authentication
    SECRET_KEY: str = "SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    # Email (for password reset)
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "test@example.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton instance
settings = Settings()
