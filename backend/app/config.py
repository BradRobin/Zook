"""
Configuration settings for Zook FastAPI application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/zook"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3500", "http://localhost:3000"]
    
    # Application
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Zook Auth Server"
    
    # Detection Model Configuration
    USE_CUSTOM_MODEL: bool = True
    CUSTOM_MODEL_PATH: Optional[str] = "app/models/custom_knife_model.pt"
    DETECTION_DEVICE: str = "cpu"
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.90


# Global settings instance
settings = Settings()


