"""
환경 설정 관리
소셜 로그인은 oauth/social_auth.py에서 직접 관리됩니다.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application Environment
    APP_ENV: str = "local"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./automl.db"
    
    # Security Keys
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here-please-change-in-production"
    SESSION_SECRET_KEY: str = "your-session-secret-key-here-please-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # URLs and Ports
    STREAMLIT_APP_URL: str = "http://localhost:8501"
    API_URL: str = "http://localhost:8001"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MODEL_SAVE_DIR: str = "models"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    
    # Vector Database and RAG
    VECTOR_DB_PATH: str = "vectordb"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Celery and Redis Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OpenAI API (Optional)
    OPENAI_API_KEY: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs.log"

# 설정 인스턴스 생성
settings = Settings()

# 환경변수 로더 함수 호출
from utils.env_loader import load_env
load_env()

# 설정 재로드 (환경변수 로드 후)
settings = Settings()