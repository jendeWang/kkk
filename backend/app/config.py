from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/iot_platform"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # MQTT
    MQTT_BROKER_URL: str = "mosquitto"
    MQTT_BROKER_PORT: int = 1883

    # Security
    SECRET_KEY: str = "your-production-secret-key-change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
