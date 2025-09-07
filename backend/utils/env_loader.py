import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_env():
    """환경 변수 로드 - 로컬/클라우드 환경 대응"""
    
    # 현재 실행 환경 감지
    app_env = os.getenv("APP_ENV", "local").lower()
    
    if app_env == "local":
        # 로컬 환경: .env 파일들 순서대로 시도
        env_files = [".env.local", ".env.dev", ".env"]
        
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path, override=True)
                logger.info(f"Local environment variables loaded: {env_file}")
                break
        else:
            logger.warning("Local environment variable file not found.")
            
    elif app_env == "cloud":
        # 클라우드 환경: 시스템 환경 변수 사용
        logger.info("Cloud environment: using system environment variables")
        
        # 클라우드 환경에서 필수 환경 변수 체크
        cloud_required_vars = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "SESSION_SECRET_KEY"
        ]
        
        missing_vars = [var for var in cloud_required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables in cloud: {missing_vars}")
    
    # 필수 환경 변수 체크 및 기본값 설정
    _set_default_env_vars()
    
    # 환경 변수 검증
    _validate_env_vars()

def _set_default_env_vars():
    """필수 환경 변수 기본값 설정"""
    defaults = {
        "JWT_SECRET_KEY": "your-jwt-secret-key-here-please-change-in-production",
        "SESSION_SECRET_KEY": "your-session-secret-key-here-please-change-in-production",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "DATABASE_URL": "sqlite:///./automl.db",
        "STREAMLIT_APP_URL": "http://localhost:8501",
        "API_URL": "http://localhost:8001",
        "UPLOAD_DIR": "uploads",
        "MODEL_SAVE_DIR": "models",
        "VECTOR_DB_PATH": "vectordb",
        "MAX_FILE_SIZE": "104857600",  # 100MB
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "CHUNK_SIZE": "1000",
        "CHUNK_OVERLAP": "200"
    }
    
    for key, default_value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            if key in ["JWT_SECRET_KEY", "SESSION_SECRET_KEY"]:
                logger.warning(f"{key} using default value - please change in production!")

def _validate_env_vars():
    """환경 변수 유효성 검증"""
    validations = []
    
    # JWT 시크릿 키 검증
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if jwt_secret == "your-jwt-secret-key-here-please-change-in-production":
        validations.append("JWT_SECRET_KEY is using default value. Please change for security.")
    elif len(jwt_secret) < 32:
        validations.append("JWT_SECRET_KEY is too short. Minimum 32 characters recommended.")
    
    # 데이터베이스 URL 검증
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        validations.append("DATABASE_URL is not set.")
    
    # 소셜 로그인 설정 검증 (선택사항)
    social_providers = ["GOOGLE", "KAKAO", "NAVER"]
    for provider in social_providers:
        client_id = os.getenv(f"{provider}_CLIENT_ID")
        client_secret = os.getenv(f"{provider}_CLIENT_SECRET")
        if client_id and not client_secret:
            validations.append(f"{provider} CLIENT_ID exists but CLIENT_SECRET is missing.")
    
    # 검증 결과 로깅
    if validations:
        for validation in validations:
            logger.warning(f"WARNING: {validation}")
    else:
        logger.info("Environment variable validation completed")

def get_env_var(var_name: str, default_value: str = None, required: bool = False) -> str:
    """환경 변수 안전하게 가져오기"""
    value = os.getenv(var_name, default_value)
    
    if required and not value:
        raise ValueError(f"필수 환경 변수 '{var_name}'가 설정되지 않았습니다.")
    
    return value

def is_production() -> bool:
    """프로덕션 환경 여부 확인"""
    return os.getenv("APP_ENV", "local").lower() in ["production", "prod", "cloud"]

def is_development() -> bool:
    """개발 환경 여부 확인"""
    return os.getenv("APP_ENV", "local").lower() in ["development", "dev", "local"]