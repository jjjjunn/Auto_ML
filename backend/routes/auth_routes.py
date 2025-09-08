"""
일반 인증 라우트
JWT 토큰 검증, 로그아웃, 사용자 정보 조회 등을 담당합니다.
소셜 로그인은 oauth/social_auth.py에서 처리됩니다.
"""

from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.database import get_db
from services.user_log_service import UserLogService
from utils.utils import verify_jwt_token, create_jwt_token
from utils.logger import logger
from config import settings

router = APIRouter()

# UserLogService 초기화
user_log_service = UserLogService()

logger.info(" Auth Routes 모듈 초기화 시작")


@router.get("/me")
async def get_current_user(
    request: Request,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """현재 로그인한 사용자 정보 조회"""
    logger.info(" 사용자 정보 조회 요청")
    logger.info(f" 요청 정보:")
    logger.info(f"  - Client IP: {request.client.host if request.client else 'Unknown'}")
    
    # Authorization 헤더에서 토큰 추출
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # "Bearer " 제거
        logger.info(f"  - Token from Header: {token[:20]}...{token[-20:] if len(token) > 40 else token}")
    
    # URL 파라미터에서도 토큰 확인 (fallback)
    if not token:
        token = request.query_params.get("token")
        if token:
            logger.info(f"  - Token from Query: {token[:20]}...{token[-20:] if len(token) > 40 else token}")
    
    if not token:
        logger.warning(" JWT 토큰이 제공되지 않았습니다")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다"
        )
    
    try:
        # JWT 토큰 검증
        logger.info(" JWT 토큰 검증 시작")
        payload = verify_jwt_token(token)
        
        logger.info(" JWT 토큰 검증 성공:")
        logger.info(f"  - User ID: {payload.get('user_id')}")
        logger.info(f"  - Provider: {payload.get('provider')}")
        logger.info(f"  - Email: {payload.get('email')}")
        
        return JSONResponse({
            "id": payload.get("user_id"),
            "provider_id": payload.get("provider_id"),
            "name": payload.get("nickname"),
            "email": payload.get("email"),
            "provider": payload.get("provider")
        })
        
    except HTTPException as e:
        logger.error(f" JWT 토큰 검증 실패: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f" 사용자 정보 조회 예외: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다"
        )


@router.post("/logout")
async def logout(
    request: Request, 
    db: Session = Depends(get_db)
):
    """로그아웃 처리 및 활동 로그 기록"""
    logger.info(" 로그아웃 요청")
    logger.info(f" 요청 정보:")
    logger.info(f"  - Client IP: {request.client.host if request.client else 'Unknown'}")
    
    # 세션에서 사용자 정보 확인
    user_id = request.session.get("user_id")
    username = request.session.get("username", "Unknown User")
    
    logger.info(f" 세션 정보:")
    logger.info(f"  - User ID: {user_id}")
    logger.info(f"  - Username: {username}")
    
    # 사용자 활동 로그 기록
    if user_id:
        try:
            user_log_service.record_activity(
                db=db,
                user_id=user_id,
                activity_type="logout",
                description=f"사용자 {username} 로그아웃"
            )
            logger.info(f" 로그아웃 활동 로그 기록 완료")
        except Exception as e:
            logger.warning(f"️ 활동 로그 기록 실패: {str(e)}")
    
    # 세션 정리
    try:
        session_keys_before = list(request.session.keys())
        logger.info(f" 세션 정리 시작: {session_keys_before}")
        
        request.session.clear()
        
        logger.info(f" 세션 정리 완료")
    except Exception as e:
        logger.warning(f"️ 세션 정리 중 경고: {str(e)}")
    
    logger.info(" 로그아웃 처리 완료")
    
    return JSONResponse({
        "success": True,
        "message": "로그아웃되었습니다"
    })


@router.get("/verify-token")
async def verify_token_endpoint(token: Optional[str] = None):
    """JWT 토큰 검증 엔드포인트 (디버깅용)"""
    logger.info(" 토큰 검증 엔드포인트 호출")
    logger.info(f" 토큰 정보:")
    logger.info(f"  - Token 제공: {' Yes' if token else ' No'}")
    logger.info(f"  - Token 길이: {len(token) if token else 0}")
    
    if not token:
        logger.warning(" 토큰이 제공되지 않았습니다")
        return JSONResponse({
            "valid": False,
            "error": "토큰이 제공되지 않았습니다",
            "debug_info": {
                "help": "URL 파라미터로 token을 제공해주세요",
                "example": "/api/auth/verify-token?token=YOUR_TOKEN_HERE"
            }
        })
    
    try:
        logger.info(" JWT 토큰 검증 시작")
        payload = verify_jwt_token(token)
        
        logger.info(" JWT 토큰 검증 성공")
        logger.info(f"  - Payload 키: {list(payload.keys())}")
        
        return JSONResponse({
            "valid": True,
            "user": payload,
            "debug_info": {
                "token_length": len(token),
                "algorithm": settings.JWT_ALGORITHM,
                "secret_key_configured": bool(settings.JWT_SECRET_KEY)
            }
        })
        
    except HTTPException as e:
        logger.error(f" JWT 토큰 검증 실패: {e.detail}")
        return JSONResponse({
            "valid": False,
            "error": e.detail,
            "debug_info": {
                "token_provided": True,
                "token_length": len(token),
                "algorithm": settings.JWT_ALGORITHM,
                "secret_key_configured": bool(settings.JWT_SECRET_KEY)
            }
        })
        
    except Exception as e:
        logger.error(f" 토큰 검증 예외: {type(e).__name__}: {str(e)}")
        return JSONResponse({
            "valid": False,
            "error": "토큰 검증 중 내부 오류",
            "debug_info": {
                "token_provided": True,
                "token_length": len(token),
                "algorithm": settings.JWT_ALGORITHM,
                "secret_key_configured": bool(settings.JWT_SECRET_KEY),
                "exception": str(e)
            }
        })


@router.get("/test-jwt")
async def test_jwt_creation():
    """JWT 토큰 생성 테스트용 엔드포인트"""
    logger.info(" JWT 토큰 생성 테스트 요청")
    
    try:
        test_payload = {
            "sub": "test-user-123",
            "user_id": 999,
            "email": "test@example.com",
            "nickname": "Test User",
            "provider": "test"
        }
        
        logger.info(f" 테스트 페이로드 생성: {test_payload}")
        
        # 토큰 생성 테스트
        token = create_jwt_token(test_payload)
        logger.info(f" 토큰 생성 성공: 길이={len(token)}")
        
        # 생성된 토큰 검증 테스트
        verified = verify_jwt_token(token)
        logger.info(f" 토큰 검증 성공: {list(verified.keys())}")
        
        return JSONResponse({
            "success": True,
            "token_created": True,
            "token_verified": True,
            "token_length": len(token),
            "original_payload": test_payload,
            "verified_payload": verified,
            "debug": {
                "secret_key_configured": settings.JWT_SECRET_KEY != "your-jwt-secret-key-here-please-change-in-production",
                "algorithm": settings.JWT_ALGORITHM,
                "expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
            }
        })
        
    except Exception as e:
        logger.error(f" JWT 테스트 예외: {type(e).__name__}: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "debug": {
                "secret_key_configured": settings.JWT_SECRET_KEY != "your-jwt-secret-key-here-please-change-in-production",
                "algorithm": settings.JWT_ALGORITHM,
                "expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
            }
        })


@router.get("/status")
async def get_auth_status(request: Request):
    """현재 인증 상태 확인 (세션 기반)"""
    logger.info(" 인증 상태 확인 요청")
    logger.info(f" 요청 정보:")
    logger.info(f"  - Client IP: {request.client.host if request.client else 'Unknown'}")
    
    # 세션 정보 확인
    session_data = dict(request.session)
    logger.info(f" 세션 데이터: {list(session_data.keys())}")
    
    is_logged_in = request.session.get('is_logged_in', False)
    
    if is_logged_in:
        user_info = {
            "logged_in": True,
            "user_id": request.session.get('user_id'),
            "name": request.session.get('name'),
            "email": request.session.get('email'),
            "provider": request.session.get('provider')
        }
        logger.info(f" 로그인 상태: {user_info}")
        return JSONResponse(user_info)
    else:
        logger.info(" 비로그인 상태")
        return JSONResponse({"logged_in": False})


@router.get("/health")
async def health_check():
    """일반 인증 시스템 헬스체크"""
    logger.info(" 일반 인증 헬스체크 요청")
    
    # JWT 설정 확인
    jwt_configured = settings.JWT_SECRET_KEY != "your-jwt-secret-key-here-please-change-in-production"
    
    # 기본 설정 상태 확인
    config_status = {
        "jwt_secret_configured": jwt_configured,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "session_secret_configured": bool(settings.SESSION_SECRET_KEY)
    }
    
    logger.info(f" 설정 상태: {config_status}")
    
    return JSONResponse({
        "status": "healthy",
        "service": "general_auth",
        "config": config_status,
        "endpoints": [
            "/me - 현재 사용자 정보",
            "/logout - 로그아웃",
            "/verify-token - JWT 토큰 검증",
            "/test-jwt - JWT 토큰 테스트",
            "/status - 인증 상태 확인",
            "/health - 헬스체크"
        ]
    })


logger.info(" Auth Routes 모듈 초기화 완료")