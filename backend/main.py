from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import logging

from routes import auth_routes, data_routes, ml_routes, chat_routes, task_routes, user_log_routes
from database.database import init_db
from utils.env_loader import load_env
from config import settings

# 환경 변수 로드
load_env()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler('logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Auto ML API",
    description="CSV 파일을 업로드하여 머신러닝 모델 학습 및 RAG 챗봇 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit
        "http://localhost:8001",  # FastAPI
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8001",
        # settings.streamlit_app_url if settings.streamlit_app_url else "http://localhost:8501"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 세션 미들웨어 (OAuth state 관리용)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="app_session",
    max_age=3600,
    same_site="lax",
    https_only=False  # 개발환경에서는 False
)

# 라우터 등록
app.include_router(auth_routes.router, prefix="/api/auth", tags=["authentication"])
app.include_router(user_log_routes.router, prefix="/api/logs", tags=["user activity logs"])
app.include_router(data_routes.router, prefix="/api/data", tags=["data management"])
app.include_router(ml_routes.router, prefix="/api/ml", tags=["machine learning"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["chat & RAG"])
app.include_router(task_routes.router, prefix="/api/tasks", tags=["async tasks"])

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작시 실행"""
    logger.info("🚀 Auto ML API 시작")
    init_db()
    logger.info("✅ 데이터베이스 초기화 완료")

@app.get("/")
async def root():
    return {
        "message": "Auto ML API is running",
        "version": "1.0.0",
        "features": [
            "CSV 데이터 업로드 및 분석",
            "자동 머신러닝 모델 학습",
            "분류, 회귀, 군집, 추천, 시계열 예측",
            "RAG 기반 챗봇",
            "소셜 로그인 (Google, Kakao, Naver)"
        ]
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": "2025-09-07"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)