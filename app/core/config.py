# File: app/core/config.py
import os
from typing import Optional, Dict, Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Collaborative Event Management API"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database - Using SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./collaborative_events.db")
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    
    # Redis for caching and rate limiting
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # This allows extra fields in the environment
    )


settings = Settings()