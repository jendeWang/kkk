from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database - use SQLite for testing
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./iot_platform.db")

    # Redis - optional for testing
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # MQTT
    MQTT_BROKER_URL: str = os.getenv("MQTT_BROKER_URL", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "test-secret-key-for-development-only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
