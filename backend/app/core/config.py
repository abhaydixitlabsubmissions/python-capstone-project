from typing import List
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "BookMind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "bookmind-dev-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3003,http://127.0.0.1:3003"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bookmind:bookmind_password@localhost:5432/bookmind_db"
    DATABASE_URL_SYNC: str = "postgresql://bookmind:bookmind_password@localhost:5432/bookmind_db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Storage
    STORAGE_BACKEND: str = "local"  # 'local' or 's3'
    STORAGE_LOCAL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")

    # S3 (optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "bookmind-documents"
    S3_ENDPOINT_URL: str = ""

    # AI / LLM
    LLM_PROVIDER: str = "openai"  # openai, gemini, or mock
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Embedding config
    EMBEDDING_PROVIDER: str = "openai"  # openai, gemini, or mock
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # Chat & Summary Models
    CHAT_MODEL: str = "gpt-4o-mini"
    SUMMARY_MODEL: str = "gpt-4o-mini"

    # Auth
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
