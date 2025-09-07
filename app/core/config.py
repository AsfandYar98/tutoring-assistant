"""Configuration management for the tutoring assistant."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration (SQLite for simplicity)
    database_url: str = Field(default="sqlite:///./tutoring_assistant.db", env="DATABASE_URL")
    
    # Authentication
    jwt_secret_key: str = Field(default="your-super-secret-jwt-key-here-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # App Configuration
    app_name: str = Field(default="AI Tutoring Assistant", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    encryption_key: str = Field(default="your-32-byte-encryption-key-here", env="ENCRYPTION_KEY")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()