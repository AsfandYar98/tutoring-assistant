"""Production configuration management."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Production settings with enhanced security and monitoring."""
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Vector Database
    chroma_host: str = Field(..., env="CHROMA_HOST")
    chroma_port: int = Field(..., env="CHROMA_PORT")
    chroma_api_key: Optional[str] = Field(..., env="CHROMA_API_KEY")
    
    # Authentication (REQUIRED in production)
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # LLM Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    vllm_base_url: str = Field(..., env="VLLM_BASE_URL")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Object Storage (REQUIRED in production)
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(..., env="AWS_REGION")
    s3_bucket: str = Field(..., env="S3_BUCKET")
    
    # Security (REQUIRED in production)
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, env="RATE_LIMIT_BURST")
    
    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Production Security
    allowed_hosts: str = Field(..., env="ALLOWED_HOSTS")
    cors_origins: str = Field(..., env="CORS_ORIGINS")
    
    # Application
    app_name: str = "Tutoring Assistant"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    @property
    def allowed_hosts_list(self) -> list:
        """Get allowed hosts as a list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global production settings instance
production_settings = ProductionSettings()
