"""
Configuration settings for different environments.
Handles both local development and production configurations.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment-specific configurations."""

    # Environment
    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development

    # Email Configuration
    SMTP_SERVER: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = "mailtojaik@gmail.com"
    SMTP_PASSWORD: Optional[str] = "rdlopzsjsdnlnczn"
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "mailtojaik@gmail.com"

    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # WebRTC Configuration
    TURN_SERVER_URL: str = "turn:localhost:3478"
    TURN_USERNAME: str = "testuser"
    TURN_PASSWORD: str = "testpass"
    STUN_SERVER_URL: str = "stun:stun.l.google.com:19302"

    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    UPLOAD_DIR: str = "uploads"
    RECORDINGS_DIR: str = "recordings"

    # Meeting Configuration
    MAX_PARTICIPANTS_PER_MEETING: int = 100
    MAX_MEETING_DURATION_HOURS: int = 8
    DEFAULT_MEETING_DURATION_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    PROMETHEUS_METRICS: bool = True
    LOG_LEVEL: str = "INFO"

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        valid_envs = ["local", "development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(
                "Environment must be one of: local, development, staging, " "production"
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT == "local"

    class Config:
        env_file = ".env"
        case_sensitive = True


class LocalSettings(Settings):
    """Settings for local development."""

    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Local TURN server
    TURN_SERVER_URL: str = "turn:localhost:3478"
    TURN_USERNAME: str = "testuser"
    TURN_PASSWORD: str = "testpass"

    # Relaxed security for development
    SECRET_KEY: str = "local-dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for dev convenience


class ProductionSettings(Settings):
    """Settings for production deployment."""

    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Production database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/videoapp"

    # Stricter security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    RATE_LIMIT_PER_MINUTE: int = 30

    # Production CORS (should be your actual domain)
    CORS_ORIGINS: List[str] = ["https://yourdomain.com", "https://www.yourdomain.com"]


def get_settings() -> Settings:
    """Get settings based on environment."""
    environment = os.getenv("ENVIRONMENT", "local").lower()

    if environment == "production":
        return ProductionSettings()
    else:
        return LocalSettings()
