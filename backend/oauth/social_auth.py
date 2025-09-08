"""
소셜 로그인 (OAuth) 구현
Google, Kakao, Naver 로그인을 지원합니다.
"""

import os
import logging
from typing import Optional, Dict, Any
from uuid import uuid4
import traceback
import time

import httpx
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

# 로컬 프로젝트 DB, 컨트롤러
from database.database import get_db
from controllers.users_controllers import create_or_update_social_user
from services.user_log_service import UserLogService

# 공통 함수 import
from utils.utils import verify_jwt_token, create_jwt_token
from utils.logger import logger  # 중앙집중 로거 사용

router = APIRouter()

# UserLogService 초기화
user_log_service = UserLogService()

logger.info(" Social Auth 모듈 초기화 시작")

# OAuth Endpoints URLs
OAUTH_ENDPOINTS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token", 
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
    },
    "kakao": {
        "auth_url": "https://kauth.kakao.com/oauth/authorize",
        "token_url": "https://kauth.kakao.com/oauth/token",
        "userinfo_url": "https://kapi.kakao.com/v2/user/me"
    },
    "naver": {
        "auth_url": "https://nid.naver.com/oauth2.0/authorize", 
        "token_url": "https://nid.naver.com/oauth2.0/token",
        "userinfo_url": "https://openapi.naver.com/v1/nid/me"
    }
}

# 환경변수 로드 및 검증
class OAuthConfig:
    """OAuth 설정 관리 클래스"""
    def __init__(self):
        logger.info(" OAuth 환경변수 로드 시작")
        
        # Google OAuth
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
        
        # Kakao OAuth  
        self.kakao_client_id = os.getenv("KAKAO_CLIENT_ID", "")  # REST API Key
        self.kakao_client_secret = os.getenv("KAKAO_CLIENT_SECRET", "")
        self.kakao_redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8001/auth/kakao/callback")
        
        # Naver OAuth
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self.naver_redirect_uri = os.getenv("NAVER_REDIRECT_URI", "http://localhost:8001/auth/naver/callback")
        
        # JWT 및 기타
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here-please-change-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.streamlit_app_url = os.getenv("STREAMLIT_APP_URL", "http://localhost:8501")
        
        # 환경변수 검증 및 로깅
        self._validate_and_log_config()
    
    def _validate_and_log_config(self):
        """환경변수 검증 및 상세 로깅"""
        logger.info(" OAuth 환경변수 상세 검증:")
        
        providers_status = {}
        
        # Google 설정 검증
        google_valid = all([self.google_client_id, self.google_client_secret])
        providers_status["google"] = google_valid
        logger.info(f"   Google: {' 설정완료' if google_valid else ' 설정필요'}")
        logger.info(f"    - Client ID: {' 있음' if self.google_client_id else ' 없음'}")
        logger.info(f"    - Client Secret: {' 있음' if self.google_client_secret else ' 없음'}")
        logger.info(f"    - Redirect URI: {self.google_redirect_uri}")
        
        # Kakao 설정 검증
        kakao_valid = all([self.kakao_client_id, self.kakao_client_secret])
        providers_status["kakao"] = kakao_valid
        logger.info(f"  🟡 Kakao: {' 설정완료' if kakao_valid else ' 설정필요'}")
        logger.info(f"    - Client ID: {' 있음' if self.kakao_client_id else ' 없음'}")
        logger.info(f"    - Client Secret: {' 있음' if self.kakao_client_secret else ' 없음'}")
        logger.info(f"    - Redirect URI: {self.kakao_redirect_uri}")
        
        # Naver 설정 검증
        naver_valid = all([self.naver_client_id, self.naver_client_secret])
        providers_status["naver"] = naver_valid
        logger.info(f"  🟢 Naver: {' 설정완료' if naver_valid else ' 설정필요'}")
        logger.info(f"    - Client ID: {' 있음' if self.naver_client_id else ' 없음'}")
        logger.info(f"    - Client Secret: {' 있음' if self.naver_client_secret else ' 없음'}")
        logger.info(f"    - Redirect URI: {self.naver_redirect_uri}")
        
        # JWT 및 기타 설정
        logger.info(f"   JWT Secret Key: {' 설정됨' if self.jwt_secret_key != 'your-jwt-secret-key-here-please-change-in-production' else '️ 기본값 사용'}")
        logger.info(f"   Streamlit URL: {self.streamlit_app_url}")
        
        # HTTPS 경고
        for provider, uri in [
            ("Google", self.google_redirect_uri),
            ("Kakao", self.kakao_redirect_uri), 
            ("Naver", self.naver_redirect_uri)
        ]:
            if uri and not uri.startswith('https://') and 'localhost' not in uri:
                logger.warning(f"️ {provider} redirect URI가 HTTPS가 아닙니다: {uri}")
        
        # 활성화된 제공업체 수 요약
        active_count = sum(providers_status.values())
        logger.info(f" OAuth 제공업체 활성화 현황: {active_count}/3개 활성화")
        
        if active_count == 0:
            logger.warning("️ 활성화된 OAuth 제공업체가 없습니다!")
        
        return providers_status
    
    def get_provider_config(self, provider: str) -> Dict[str, str]:
        """특정 제공업체 설정 반환"""
        configs = {
            "google": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "redirect_uri": self.google_redirect_uri
            },
            "kakao": {
                "client_id": self.kakao_client_id,
                "client_secret": self.kakao_client_secret,
                "redirect_uri": self.kakao_redirect_uri
            },
            "naver": {
                "client_id": self.naver_client_id,
                "client_secret": self.naver_client_secret,
                "redirect_uri": self.naver_redirect_uri
            }
        }
        return configs.get(provider, {})

# OAuth 설정 인스턴스 생성
oauth_config = OAuthConfig()

SUPPORTED_PROVIDERS = {"google", "kakao", "naver"}
logger.info(f" 지원 제공업체: {', '.join(SUPPORTED_PROVIDERS)}")


@router.get("/{provider}")
async def oauth_login(provider: str, request: Request):
    """OAuth 로그인 시작 - 상세 로깅 포함"""
    logger.info("=" * 60)
    logger.info(f" OAuth 로그인 요청 시작")
    logger.info(f" 요청 정보:")
    logger.info(f"  - Provider: {provider}")
    logger.info(f"  - Client IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"  - User Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    
    # 제공업체 검증
    if provider not in SUPPORTED_PROVIDERS:
        logger.error(f" 지원하지 않는 프로바이더: {provider}")
        logger.error(f" 지원 가능한 프로바이더: {', '.join(SUPPORTED_PROVIDERS)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 프로바이더: {provider}. 지원 가능: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    # 제공업체 설정 확인
    provider_config = oauth_config.get_provider_config(provider)
    if not provider_config.get("client_id") or not provider_config.get("client_secret"):
        logger.error(f" {provider} OAuth 설정이 불완전합니다")
        logger.error(f"  - Client ID: {'설정됨' if provider_config.get('client_id') else ' 없음'}")
        logger.error(f"  - Client Secret: {'설정됨' if provider_config.get('client_secret') else ' 없음'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{provider} OAuth 설정이 완료되지 않았습니다"
        )

    # OAuth state 생성 및 세션 저장
    state = str(uuid4())
    try:
        request.session["oauth_state"] = state
        request.session["oauth_provider"] = provider
        request.session["oauth_timestamp"] = str(int(time.time()))
        logger.info(f" OAuth 세션 정보 저장 완료:")
        logger.info(f"  - State: {state[:8]}...{state[-8:]}")
        logger.info(f"  - Provider: {provider}")
    except Exception as e:
        logger.error(f" 세션 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 저장 중 오류가 발생했습니다"
        )

    # OAuth URL 생성
    try:
        endpoints = OAUTH_ENDPOINTS[provider]
        auth_url = endpoints["auth_url"]
        
        if provider == "google":
            redirect_url = (
                f"{auth_url}?"
                f"client_id={provider_config['client_id']}&"
                f"redirect_uri={provider_config['redirect_uri']}&"
                f"response_type=code&"
                f"scope=openid%20email%20profile&"
                f"state={state}"
            )
        elif provider == "kakao":
            redirect_url = (
                f"{auth_url}?"
                f"client_id={provider_config['client_id']}&"
                f"redirect_uri={provider_config['redirect_uri']}&"
                f"response_type=code&"
                f"state={state}"
            )
        elif provider == "naver":
            redirect_url = (
                f"{auth_url}?"
                f"client_id={provider_config['client_id']}&"
                f"redirect_uri={provider_config['redirect_uri']}&"
                f"response_type=code&"
                f"state={state}"
            )
        
        logger.info(f" OAuth URL 생성 완료:")
        logger.info(f"  - Provider: {provider}")
        logger.info(f"  - Auth URL: {auth_url}")
        logger.info(f"  - Redirect URI: {provider_config['redirect_uri']}")
        logger.info(f"  - Full URL: {redirect_url[:100]}...")
        logger.info("=" * 60)
        
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        logger.error(f" OAuth URL 생성 실패: {str(e)}")
        logger.error(f" 에러 상세: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth URL 생성 중 오류가 발생했습니다"
        )


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """OAuth 콜백 처리 - 완전한 로깅 및 에러 처리"""
    logger.info("=" * 80)
    logger.info(f" OAuth 콜백 요청 수신")
    logger.info(f" 콜백 정보:")
    logger.info(f"  - Provider: {provider}")
    logger.info(f"  - Code: {' 있음' if code else ' 없음'}")
    logger.info(f"  - State: {state[:8] + '...' + state[-8:] if state else ' 없음'}")
    logger.info(f"  - Error: {error if error else '없음'}")
    logger.info(f"  - Error Description: {error_description if error_description else '없음'}")
    logger.info(f"  - Client IP: {request.client.host if request.client else 'Unknown'}")
    
    # OAuth 에러 확인
    if error:
        logger.error(f" OAuth 제공업체에서 에러 반환:")
        logger.error(f"  - Error: {error}")
        logger.error(f"  - Description: {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 인증 실패: {error} - {error_description}"
        )
    
    if not code:
        logger.error(f" 인증 코드가 없습니다")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth 인증 코드가 제공되지 않았습니다"
        )
    
    # 제공업체 검증
    if provider not in SUPPORTED_PROVIDERS:
        logger.error(f" 지원하지 않는 프로바이더: {provider}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 프로바이더: {provider}"
        )
    
    # 제공업체 설정 확인
    provider_config = oauth_config.get_provider_config(provider)
    if not provider_config.get("client_id") or not provider_config.get("client_secret"):
        logger.error(f" {provider} OAuth 설정이 불완전합니다")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{provider} OAuth 설정이 완료되지 않았습니다"
        )

    # State 검증
    saved_state = request.session.get("oauth_state")
    saved_provider = request.session.get("oauth_provider")
    saved_timestamp = request.session.get("oauth_timestamp")
    
    logger.info(f" State 및 세션 검증:")
    logger.info(f"  - 저장된 State: {saved_state[:8] + '...' + saved_state[-8:] if saved_state else ' 없음'}")
    logger.info(f"  - 받은 State: {state[:8] + '...' + state[-8:] if state else ' 없음'}")
    logger.info(f"  - 저장된 Provider: {saved_provider}")
    logger.info(f"  - 받은 Provider: {provider}")
    logger.info(f"  - 저장된 시간: {saved_timestamp}")
    
    if not saved_state or state != saved_state:
        logger.error(f" State 검증 실패")
        logger.error(f"  - 저장된: {saved_state}")
        logger.error(f"  - 받은: {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSRF 보호 - State 검증 실패"
        )
    
    if saved_provider != provider:
        logger.error(f" Provider 불일치: 저장됨={saved_provider}, 받음={provider}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider 불일치"
        )

    # 액세스 토큰 요청
    logger.info(f" 액세스 토큰 요청 시작")
    
    endpoints = OAUTH_ENDPOINTS[provider]
    token_url = endpoints["token_url"]
    
    token_data = {
        "code": code,
        "client_id": provider_config["client_id"],
        "client_secret": provider_config["client_secret"],
        "redirect_uri": provider_config["redirect_uri"],
        "grant_type": "authorization_code"
    }
    
    if provider == "naver":
        token_data["state"] = state  # Naver는 토큰 요청에도 state 필요
    
    logger.info(f" 토큰 요청 세부사항:")
    logger.info(f"  - URL: {token_url}")
    logger.info(f"  - Client ID: {provider_config['client_id'][:8]}...")
    logger.info(f"  - Redirect URI: {provider_config['redirect_uri']}")
    
    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "AutoML-Platform/1.0"
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f" 토큰 요청 전송 중...")
            
            token_response = await client.post(
                token_url,
                data=token_data,
                headers=headers
            )
            
            logger.info(f" 토큰 응답 수신:")
            logger.info(f"  - 상태 코드: {token_response.status_code}")
            logger.info(f"  - 응답 헤더: {dict(token_response.headers)}")
            
            if token_response.status_code != 200:
                error_text = token_response.text
                logger.error(f" 토큰 요청 실패:")
                logger.error(f"  - 상태 코드: {token_response.status_code}")
                logger.error(f"  - 응답: {error_text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth 토큰 획득 실패: {token_response.status_code}"
                )
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                logger.error(f" 토큰 응답에 access_token이 없습니다:")
                logger.error(f"  - 응답 키: {list(tokens.keys())}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="액세스 토큰을 찾을 수 없습니다"
                )
            
            logger.info(f" 액세스 토큰 획득 성공")
            logger.info(f"  - 토큰 길이: {len(access_token)}")
            
    except httpx.TimeoutException as e:
        logger.error(f"⏱️ 토큰 요청 타임아웃: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="OAuth 서버 응답 시간 초과"
        )
    except httpx.ConnectError as e:
        logger.error(f" 토큰 요청 연결 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OAuth 서버 연결 실패"
        )
    except Exception as e:
        logger.error(f" 토큰 요청 예외: {type(e).__name__}: {str(e)}")
        logger.error(f" 상세 추적: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 요청 중 예상치 못한 오류"
        )

    # 사용자 정보 요청
    logger.info(f" 사용자 정보 요청 시작")
    
    userinfo_url = endpoints["userinfo_url"]
    
    try:
        userinfo_headers = {"Authorization": f"Bearer {access_token}"}
        
        if provider == "naver":
            userinfo_headers.update({
                "X-Naver-Client-Id": provider_config["client_id"],
                "X-Naver-Client-Secret": provider_config["client_secret"]
            })
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f" 사용자 정보 요청 전송: {userinfo_url}")
            
            userinfo_response = await client.get(
                userinfo_url,
                headers=userinfo_headers
            )
            
            logger.info(f" 사용자 정보 응답:")
            logger.info(f"  - 상태 코드: {userinfo_response.status_code}")
            
            if userinfo_response.status_code != 200:
                error_text = userinfo_response.text
                logger.error(f" 사용자 정보 요청 실패:")
                logger.error(f"  - 상태 코드: {userinfo_response.status_code}")
                logger.error(f"  - 응답: {error_text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"사용자 정보 획득 실패: {userinfo_response.status_code}"
                )
            
            profile = userinfo_response.json()
            logger.info(f" 원본 프로필 데이터: {profile}")
            
            # 제공업체별 사용자 정보 추출
            if provider == "google":
                user_id = profile.get("id")
                nickname = profile.get("name", "Google User")
                email = profile.get("email")
                
            elif provider == "kakao":
                user_id = profile.get("id")
                nickname = profile.get("properties", {}).get("nickname", "Kakao User")
                email = profile.get("kakao_account", {}).get("email")
                
            elif provider == "naver":
                naver_response = profile.get("response", {})
                user_id = naver_response.get("id")
                nickname = naver_response.get("nickname", "Naver User")
                email = naver_response.get("email")
            
            logger.info(f" 사용자 정보 추출 완료:")
            logger.info(f"  - Provider: {provider}")
            logger.info(f"  - User ID: {user_id}")
            logger.info(f"  - Nickname: {nickname}")
            logger.info(f"  - Email: {email}")
            
            if not user_id:
                logger.error(f" 사용자 ID를 찾을 수 없습니다")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="사용자 ID를 찾을 수 없습니다"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" 사용자 정보 요청 예외: {type(e).__name__}: {str(e)}")
        logger.error(f" 상세 추적: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 요청 중 오류"
        )

    # 데이터베이스에 사용자 저장
    logger.info(f" 사용자 정보 데이터베이스 저장 시작")
    
    try:
        user = create_or_update_social_user(
            db=db,
            user_info={
                "provider_id": str(user_id),
                "email": email,
                "name": nickname
            },
            provider=provider,
            request=request,
            access_token=access_token
        )
        
        logger.info(f" 사용자 정보 데이터베이스 저장 완료:")
        logger.info(f"  - DB User ID: {user.id}")
        logger.info(f"  - Username: {user.username}")
        logger.info(f"  - Email: {user.email}")
        
        # 로그인 활동 기록
        user_log_service.record_activity(
            db=db,
            user_id=user.id,
            activity_type="login",
            description=f"소셜 로그인 성공 ({provider}): {nickname}"
        )
        
    except Exception as e:
        logger.error(f" 데이터베이스 저장 예외: {type(e).__name__}: {str(e)}")
        logger.error(f" 상세 추적: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 저장 실패"
        )

    # JWT 토큰 생성
    logger.info(f" JWT 토큰 생성 시작")
    
    try:
        jwt_payload = {
            "sub": str(user_id),
            "user_id": user.id,
            "provider_id": str(user_id),
            "nickname": nickname,
            "email": email,
            "provider": provider
        }
        
        jwt_token = create_jwt_token(jwt_payload)
        
        logger.info(f" JWT 토큰 생성 완료:")
        logger.info(f"  - 토큰 길이: {len(jwt_token)}")
        logger.info(f"  - 페이로드 키: {list(jwt_payload.keys())}")
        
    except Exception as e:
        logger.error(f" JWT 토큰 생성 예외: {type(e).__name__}: {str(e)}")
        logger.error(f" 상세 추적: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 토큰 생성 실패"
        )

    # 세션 정리
    try:
        request.session.pop("oauth_state", None)
        request.session.pop("oauth_provider", None)
        request.session.pop("oauth_timestamp", None)
        logger.info(f" OAuth 세션 정리 완료")
    except Exception as e:
        logger.warning(f"️ 세션 정리 중 경고: {str(e)}")

    # 최종 리디렉션
    redirect_url = f"{oauth_config.streamlit_app_url}?token={jwt_token}&login=success"
    
    logger.info(f" 최종 리디렉션:")
    logger.info(f"  - Streamlit URL: {oauth_config.streamlit_app_url}")
    logger.info(f"  - Full URL: {redirect_url[:100]}...")
    logger.info("=" * 80)
    
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER
    )


# 헬스체크 및 유틸리티 엔드포인트
@router.get("/health")
async def health_check():
    """소셜 로그인 헬스체크"""
    logger.info(" 소셜 로그인 헬스체크 요청")
    
    # 각 제공업체 설정 상태 확인
    provider_status = {}
    for provider in SUPPORTED_PROVIDERS:
        config = oauth_config.get_provider_config(provider)
        provider_status[provider] = {
            "configured": bool(config.get("client_id") and config.get("client_secret")),
            "redirect_uri": config.get("redirect_uri", "")
        }
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": int(time.time()),
        "providers": provider_status,
        "supported_providers": list(SUPPORTED_PROVIDERS)
    })


@router.get("/debug/config")
async def debug_config():
    """디버깅용 설정 정보 (민감정보 제외)"""
    logger.info(" 디버그 설정 정보 요청")
    
    debug_info = {}
    for provider in SUPPORTED_PROVIDERS:
        config = oauth_config.get_provider_config(provider)
        debug_info[provider] = {
            "client_id_configured": bool(config.get("client_id")),
            "client_secret_configured": bool(config.get("client_secret")),
            "redirect_uri": config.get("redirect_uri", "")
        }
    
    return JSONResponse({
        "oauth_config": debug_info,
        "jwt_configured": oauth_config.jwt_secret_key != "your-jwt-secret-key-here-please-change-in-production",
        "streamlit_url": oauth_config.streamlit_app_url
    })


logger.info(" Social Auth 모듈 초기화 완료")