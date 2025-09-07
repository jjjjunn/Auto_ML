import frontend.utils.env_loader
frontend.utils.env_loader.load_environment_variables()

import streamlit as st
import pandas as pd
import time
import os
import tempfile
import json
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from pathlib import Path
import jwt
import requests

# 페이지 설정
st.set_page_config(
    page_title="Auto_ML Platform", # Updated project name
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# utils 모듈 가져오기 (adjusted path)
from frontend.utils.utils import initialize_app
from frontend.utils.app_classes import (
    AnalysisHistoryManager,
    IngredientsDisplayer,
    SessionStateManager,
    ImageProcessor,
    ChatbotAnalyzer
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 상수 정의
MAX_IMAGE_SIZE = 2048
MAX_HISTORY_SIZE = 10
SUPPORTED_TYPES = ["jpg", "jpeg", "png", "jfif", "webp"]

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


def create_sidebar() -> Dict[str, Any]:
    """사이드바 생성 및 설정 관리"""
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # 설정 옵션들
        settings = {
            'show_progress': st.checkbox("진행률 표시", value=st.session_state.show_progress),
            'auto_clean': st.checkbox("자동 성분 정리", value=st.session_state.auto_clean,
                                    help="의미없는 텍스트 자동 제거"),
            'use_rag': st.checkbox("RAG 기능 사용", value=st.session_state.use_rag,
                                 help="논문 데이터베이스 활용")
        }
        
        # 세션 상태 업데이트
        st.session_state.update(settings)
        st.markdown("---")
        
        # 분석 기록
        AnalysisHistoryManager.display_sidebar_history()
        st.markdown("---")
        
        # 사용 팁
        with st.expander("💡 사용 팁"):
            st.markdown("""
            **이미지 품질**
            - 고해상도, 선명한 이미지
            - 충분한 조명, 정면 촬영
            - 배경과 글자의 명확한 대비
            
            **성분표 형태**
            - "성분:", "원재료명:" 등 명확한 키워드
            - 기울어지지 않은 수평/수직 정렬
            """)
        
        # 로그아웃 구현
        if st.button("🚪 로그아웃"):
            logger.info(f"[Streamlit] 로그아웃 버튼 클릭 - 사용자: {st.session_state.get('username')}")
            for key in ["logged_in", "username", "jwt_token", "user_id"]: # Clear all relevant session state
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["page"] = "login" # Redirect to login page
            st.rerun()
        
        return settings


# 홈페이지 콘텐츠
def show_home_content():
    """홈페이지 메인 콘텐츠"""
    if not st.session_state.get("logged_in"):
        show_guest_home()
    else:
        show_user_home()

# --- JWT 토큰 검증 및 로그인 처리 ---
def verify_and_login_user():
    """URL의 JWT 토큰을 검증하고, 유효하면 로그인 상태를 업데이트."""
    query_params = st.query_params
    jwt_token = query_params.get("token")

    if jwt_token and not st.session_state.get("logged_in"):
        try:
            # 토큰 디코딩
            payload = jwt.decode(jwt_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Streamlit 세션 상태 업데이트
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = payload.get("sub")  # JWT의 sub 필드가 사용자 ID
            st.session_state["username"] = payload.get("nickname", "사용자")
            st.session_state["jwt_token"] = jwt_token # JWT 토큰을 세션에 저장

            st.success(f"✅ 로그인 성공! 환영합니다, {st.session_state['username']}님.")
            st.balloons()
            
            # URL에서 토큰 제거
            st.query_params.clear()
            st.rerun()

        except jwt.InvalidTokenError:
            st.error("❌ 유효하지 않은 로그인 토큰입니다.")
            logger.error("유효하지 않은 로그인 토큰입니다.", exc_info=True)
        except Exception as e:
            st.error(f"❌ 로그인 처리 중 오류가 발생했습니다: {e}")
            logger.error(f"로그인 처리 중 오류가 발생했습니다: {e}", exc_info=True)


def show_guest_home():
    """비로그인 사용자용 홈페이지"""
    st.title("🔍 Auto_ML Platform") # Updated project name
    st.markdown("CSV 파일을 업로드하여 머신러닝 모델을 구현하고 분석합니다.") # Updated description
    
    st.info("👈 왼쪽 사이드바에서 로그인 후 모든 기능을 이용하세요!")
             
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🌟 주요 기능
        - **자동 머신러닝**: CSV 업로드로 모델 자동 구현
        - **AI 모델 추천**: 데이터에 맞는 최적 모델 추천
        - **EDA**: 탐색적 데이터 분석
        - **RAG 챗봇**: 모델에 대한 질문 답변
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 사용법
        1. CSV 파일 업로드
        2. 타겟 변수 및 분석 변수 선택
        3. AI 모델 추천 확인
        4. 모델 학습 및 분석
        """)

def show_user_home():
    """로그인 사용자용 메인 기능"""
    st.title("🔍 Auto_ML Platform") # Updated project name
    st.markdown("업로드한 CSV 파일을 분석하고 머신러닝 모델을 학습합니다.") # Updated description

    st.write(f"환영합니다, {st.session_state.get('username', '사용자')}님!")
    
    # 디버그 정보 표시 (개발용)
    with st.expander("🔧 디버그 정보", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**로그인 상태:**", st.session_state.get('logged_in', False))
            st.write("**사용자 ID:**", st.session_state.get('user_id', 'None'))
            st.write("**사용자명:**", st.session_state.get('username', 'None'))
        with col2:
            st.write("**JWT 토큰:**", "있음" if st.session_state.get('jwt_token') else "없음")
            st.write("**API URL:**", os.getenv("API_URL", "설정되지 않음"))
            st.write("**마지막 저장된 로그 ID:**", st.session_state.get('last_saved_log_id', 'None'))
    
    # 사이드바 설정
    settings = create_sidebar()

    # ✅ 이미지 분석이 완료된 상태인지 확인 (CSV 분석으로 변경)
    if st.session_state.get('csv_analysis_complete', False) and st.session_state.get('current_dataframe_path'):
        # 분석 완료 후 상태
        st.markdown("### 📋 분석 결과")
        # IngredientsDisplayer.display_complete_analysis( # This needs to be adapted for CSV
        #     st.session_state.current_ingredients,
        #     prefix_key="current_"
        # )
        st.info("CSV 분석 결과 표시 영역 (EDA, 모델 추천 등)")
        
        st.markdown("---")
        st.subheader("🤖 AI 분석")
        if st.session_state.get("current_dataframe_path"):
            ChatbotAnalyzer.display_analysis_section(st.session_state.current_dataframe_path)
        else:
            st.info("CSV 파일을 업로드하고 분석을 완료하면 챗봇을 사용할 수 있습니다.")
        
        # 새로운 분석 시작 버튼
        st.markdown("---")
        if st.button("🔄 새로운 CSV 분석", type="secondary"):
            # 상태 초기화
            logger.info("[Streamlit] '새로운 CSV 분석' 버튼 클릭 - 세션 상태 초기화")
            st.session_state.csv_analysis_complete = False
            st.session_state.current_dataframe_path = None
            SessionStateManager.reset_chatbot() # Still relevant for chatbot
            st.rerun()
    
    else:
        # CSV 업로드 및 분석 단계
        st.subheader("📊 CSV 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "머신러닝 분석을 위한 CSV 파일을 선택하세요",
            type=["csv"],
            help="지원 형식: CSV",
            key="csv_uploader"
        )

        if uploaded_file is not None:
            st.success(f"파일 '{uploaded_file.name}'이 성공적으로 업로드되었습니다.")
            
            # 타겟 변수 및 분석 변수 선택 (placeholder)
            st.markdown("---")
            st.subheader("변수 선택")
            
            # Read a sample of the CSV to get columns
            try:
                df_sample = pd.read_csv(uploaded_file, nrows=5)
                all_columns = df_sample.columns.tolist()
                uploaded_file.seek(0) # Reset file pointer after reading sample
            except Exception as e:
                st.error(f"CSV 파일 읽기 오류: {e}")
                logger.error(f"CSV 파일 읽기 오류: {e}", exc_info=True)
                all_columns = []

            if all_columns:
                target_column = st.selectbox(
                    "예측하고자 하는 타겟 변수를 선택하세요 (종속 변수)",
                    options=["선택 안 함"] + all_columns,
                    key="target_selector"
                )
                
                feature_columns = st.multiselect(
                    "모델 학습에 사용할 분석 변수들을 선택하세요 (독립 변수)",
                    options=all_columns,
                    default=[col for col in all_columns if col != target_column and col != "선택 안 함"],
                    key="feature_selector"
                )
                
                st.markdown("---")
                if st.button("🚀 CSV 분석 및 모델 추천 시작", type="primary", use_container_width=True):
                    logger.info("[Streamlit] 'CSV 분석 및 모델 추천 시작' 버튼 클릭")
                    
                    # Call FastAPI endpoint for CSV upload and recommendation
                    api_url = os.getenv("API_URL")
                    if api_url:
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            data = {"target_column": target_column if target_column != "선택 안 함" else None}
                            
                            response = requests.post(
                                f"{api_url.rstrip('/')}/data/upload-csv/",
                                files=files,
                                data=data,
                                timeout=120 # Increased timeout for processing
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(result.get("message", "CSV 파일 처리 및 분석 완료!"))
                                st.session_state.csv_analysis_complete = True
                                st.session_state.current_dataframe_path = result.get("file_path")
                                st.session_state.model_recommendations = result.get("recommendations")
                                
                                # Display recommendations
                                if st.session_state.model_recommendations:
                                    st.subheader("✨ AI 모델 추천 결과")
                                    st.write(f"**추천 모델 유형:** {', '.join(st.session_state.model_recommendations.get('model_types', []))}")
                                    st.info(st.session_state.model_recommendations.get('explanation', ''))
                                
                                st.rerun() # Rerun to show analysis results
                            else:
                                st.error(f"CSV 분석 중 오류 발생: {response.status_code} - {response.text}")
                                logger.error(f"CSV 분석 API 호출 실패: {response.status_code} - {response.text}")
                        except Exception as e:
                            st.error(f"CSV 분석 중 예외 발생: {e}")
                            logger.error(f"CSV 분석 중 예외 발생: {e}", exc_info=True)
                    else:
                        st.error("API_URL이 설정되지 않았습니다.")
            else:
                st.warning("CSV 파일에서 컬럼 정보를 읽을 수 없습니다. 파일 형식을 확인해주세요.")
        else:
            st.info("👆 머신러닝 분석을 위해 CSV 파일을 업로드해주세요.")
            
            # 도움말 섹션
            with st.expander("📖 상세 사용법"):
                st.markdown("""
                ### 🎯 최적의 결과를 위한 팁
                
                **CSV 파일 형식**
                - 첫 행은 컬럼 헤더여야 합니다.
                - 데이터는 쉼표(,)로 구분되어야 합니다.
                - 텍스트 인코딩은 UTF-8을 권장합니다.
                
                **데이터 품질**
                - 결측치(비어있는 값)는 미리 처리하는 것이 좋습니다.
                - 이상치(극단적인 값)는 모델 성능에 영향을 줄 수 있습니다.
                
                **변수 선택**
                - **타겟 변수**: 예측하고자 하는 값 (예: 가격, 분류 라벨).
                - **분석 변수**: 타겟 변수를 예측하는 데 사용될 데이터 (예: 크기, 색상).
                """)
            
            # 시스템 상태
            with st.expander("🔧 시스템 상태"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if os.getenv('API_URL'):
                        st.success("✅ FastAPI 백엔드 연결됨")
                    else:
                        st.error("❌ FastAPI 백엔드 미설정")
                
                with col2:
                    # AI 서비스 준비 상태는 백엔드에서 확인해야 함
                    st.info("AI 서비스 상태는 백엔드 로그를 확인해주세요.")


def main():
    """메인 애플리케이션"""
    # ✅ 세션 상태 항상 초기화
    SessionStateManager.initialize()
    
    # 앱 초기화
    initialize_app()
    
    # API URL 확인
    API_URL = os.getenv("API_URL")
    if not API_URL:
        st.error("환경 변수 API_URL이 설정되지 않았습니다!")
        st.stop()

    # 네비게이션 설정
    if st.session_state.get("logged_in"):
        # 로그인한 사용자용 페이지
        pages = [
            st.Page(show_home_content, title="홈", icon="🏠"),
            st.Page("pages/user_logs.py", title="사용자 로그", icon="📈"),
            st.Page("pages/data_visualize.py", title="데이터 분석 (EDA)", icon="📊"), # New page
            st.Page("pages/ml_model_training.py", title="모델 학습", icon="🧠") # New page
        ]
    else:
        # 비로그인 사용자용 페이지
        pages = [
            st.Page(show_home_content, title="홈", icon="🏠"),
            st.Page("pages/_login.py", title="로그인", icon="🔑"),
        ]

    # 네비게이션 실행
    nav = st.navigation(pages)
    nav.run()

    # Footer
    st.markdown("---")
    st.caption("🚀 Powered by Streamlit by Recordian")


# 페이지 시작 시 로그인 상태 확인 함수 호출
verify_and_login_user()


# 앱 실행
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"애플리케이션 실행 오류: {e}")
        logger.error(f"앱 실행 오류: {e}", exc_info=True)
