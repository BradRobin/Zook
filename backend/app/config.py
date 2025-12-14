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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Long-lived refresh tokens
    TOKEN_BLACKLIST_TTL_HOURS: int = 24  # Redis TTL for blacklisted tokens
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"  # Brute-force protection
    RATE_LIMIT_REGISTER: str = "3/minute"  # Registration spam
    RATE_LIMIT_REFRESH: str = "10/minute"  # Token refresh abuse
    RATE_LIMIT_DEFAULT: str = "100/minute"  # General API protection
    
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
    
    # HTTPS & Production Configuration
    USE_HTTPS: bool = False
    ENFORCE_HTTPS_REDIRECT: bool = False
    CLOUDFLARE_TUNNEL_ENABLED: bool = False
    PRODUCTION_URL: Optional[str] = None
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    # Database Security
    DATABASE_SSL_MODE: str = "prefer"  # prefer | require | verify-full
    
    # Monitoring Configuration
    METRICS_ENABLED: bool = True
    METRICS_PREFIX: str = "zook"
    SLOW_DETECTION_THRESHOLD_MS: int = 30
    STORAGE_ALERT_THRESHOLD_PERCENT: int = 80
    METRICS_SAMPLE_RATE: float = 0.1  # Sample 10% of high-frequency metrics


# Global settings instance
settings = Settings()


