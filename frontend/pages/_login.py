import streamlit as st
import requests
import os
import time
import logging
from urllib.parse import urlencode, quote_plus, urlparse, parse_qs
from typing import Optional
import jwt # PyJWT library
from dotenv import load_dotenv
from uuid import uuid4 # For state generation

# Streamlit 페이지 설정을 위해 추가
st.set_page_config(
    page_title="로그인",
    page_icon="🔑",
    layout="centered",
)

# 로그 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드 (프로젝트 루트에 있다고 가정)
load_dotenv()

# --- 환경 변수 설정 ---
# FastAPI 백엔드 API URL
API_URL = os.getenv("API_URL", "http://localhost:8001") # Default to 8001
# Google OAuth2.0 클라이언트 ID
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# Kakao REST API 키
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID") # Renamed from KAKAO_REST_API_KEY for consistency
# Naver 클라이언트 ID
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")

# Redirect URIs (should match backend config)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{API_URL}/auth/google/callback")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", f"{API_URL}/auth/kakao/callback")
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI", f"{API_URL}/auth/naver/callback")

# JWT Secret Key and Algorithm (should match backend config)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not API_URL:
    st.error("API_URL 환경 변수가 설정되지 않았습니다!")
    logger.error("API_URL 환경 변수가 설정되지 않았습니다!")
    st.stop()

# --- 세션 상태 초기화 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None

# --- OAuth2.0 URL 생성 함수 ---
def create_oauth_url(provider: str):
    """OAuth2.0 인증 URL을 생성."""
    state = str(uuid4()) # Need uuid4
    st.session_state["oauth_state"] = state # Store state in session for callback validation

    if provider == "google":
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    elif provider == "kakao":
        params = {
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        return f"https://kauth.kakao.com/oauth/authorize?{urlencode(params)}"
    elif provider == "naver":
        params = {
            "client_id": NAVER_CLIENT_ID,
            "redirect_uri": NAVER_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        return f"https://nid.naver.com/oauth2.0/authorize?{urlencode(params)}"
    else:
        raise ValueError("Unsupported provider")

def handle_oauth_callback(token: str, login_status: str):
    """
    FastAPI에서 리디렉션된 JWT 토큰을 처리합니다.
    """
    if login_status == "success" and token:
        try:
            # JWT 토큰을 디코딩하여 사용자 정보 추출
            # JWT_SECRET_KEY와 JWT_ALGORITHM은 환경 변수에서 로드됨
            
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = decoded_token.get("sub")
            st.session_state["username"] = decoded_token.get("nickname", "Guest")
            st.session_state["jwt_token"] = token
            
            st.success(f"✅ 로그인 성공! 환영합니다, {st.session_state['username']}님.")
            st.balloons()
            logger.info(f"로그인 성공: {st.session_state['username']}, ID: {st.session_state['user_id']}")
            
            # URL의 쿼리 파라미터 제거 (Streamlit 1.10.0+에서 st.query_params.clear() 사용 가능)
            # 이전 버전에서는 수동으로 URL을 변경해야 할 수 있음
            st.query_params.clear()
            
            # 페이지 이동 (Streamlit 1.10.0+에서 st.switch_page 사용 가능)
            st.switch_page("app") # Assuming "app" is the main page name
        except Exception as e:
            st.error(f"❌ 토큰 처리 실패: {e}")
            logger.error(f"토큰 처리 실패: {e}")
    else:
        st.error("❌ 로그인 실패")
        logger.error("로그인 실패")

def main():
    """메인 로그인 페이지 UI를 렌더링합니다."""
    # 이미 로그인된 경우
    if st.session_state.get("logged_in", False):
        st.info("이미 로그인되어 있습니다. 👈 왼쪽 사이드바에서 원하는 메뉴를 선택해주세요.")
        logger.info(f"이미 로그인된 사용자: {st.session_state.get('username')}")
        time.sleep(1)
        st.switch_page("app") # Redirect to main app if already logged in
        st.stop()

    st.title("🔑 소셜 로그인")
    st.markdown("👋 소셜 로그인으로 한 번에 시작하기.")
    st.subheader("🔍 Auto_ML Platform") # Updated project name

    # 쿼리 파라미터에서 JWT 토큰과 로그인 상태 추출
    query_params = st.query_params
    token = query_params.get("token")
    login_status = query_params.get("login")
    
    # FastAPI에서 리디렉션된 JWT 토큰 처리
    if token and login_status:
        handle_oauth_callback(token, login_status)
        st.stop()

    # 로그인 버튼 UI
    st.write("---")
    
    # Google 로그인 버튼
    google_url = create_oauth_url("google")
    st.markdown(
        f'<a href="{google_url}" target="_self" style="text-decoration: none;">'
        '<button style="width: 100%; padding: 15px; font-size: 18px; border-radius: 5px; border: 1px solid #ccc; background-color: white; cursor: pointer;">'
        '<span><img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png" height="24" style="vertical-align: middle; margin-right: 10px;"></span>'
        '<span style="vertical-align: middle;">Google로 계속하기</span>'
        '</button></a>',
        unsafe_allow_html=True
    )
    
    st.write("") # 버튼 사이 간격
    
    # Kakao 로그인 버튼
    kakao_url = create_oauth_url("kakao")
    st.markdown(
        f'<a href="{kakao_url}" target="_self" style="text-decoration: none;">'
        '<button style="width: 100%; padding: 15px; font-size: 18px; border-radius: 5px; border: 1px solid #ccc; background-color: #FEE500; cursor: pointer;">'
        '<span style="vertical-align: middle; color: #3A1D1D;">카카오로 로그인</span>'
        '</button></a>',
        unsafe_allow_html=True
    )

    st.write("") # 버튼 사이 간격

    # Naver 로그인 버튼
    naver_url = create_oauth_url("naver")
    st.markdown(
        f'<a href="{naver_url}" target="_self" style="text-decoration: none;">'
        '<button style="width: 100%; padding: 15px; font-size: 18px; border-radius: 5px; border: 1px solid #ccc; background-color: #2DB400; cursor: pointer;">'
        '<span style="vertical-align: middle; color: white;">네이버로 로그인</span>'
        '</button></a>',
        unsafe_allow_html=True
    )

    st.write("---")

if __name__ == "__main__":
    main()