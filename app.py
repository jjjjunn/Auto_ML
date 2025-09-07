"""
Auto ML Streamlit Frontend Application

이 애플리케이션은 사용자가 CSV 파일을 업로드하고 머신러닝 모델을 학습시킬 수 있는
웹 인터페이스를 제공합니다. 또한 RAG 기반 챗봇을 통해 AI와 대화할 수 있습니다.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
import json
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="Auto ML Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 기본 설정
API_BASE_URL = os.getenv("API_URL", "http://localhost:8001")

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.375rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.375rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .social-button {
        display: inline-block;
        width: 100%;
        padding: 0.75rem;
        margin: 0.5rem 0;
        text-align: center;
        text-decoration: none;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .google-btn {
        background-color: #4285f4;
        color: white;
    }
    .google-btn:hover {
        background-color: #3367d6;
    }
    .kakao-btn {
        background-color: #fee500;
        color: #3c1e1e;
    }
    .kakao-btn:hover {
        background-color: #fdd835;
    }
    .naver-btn {
        background-color: #03c75a;
        color: white;
    }
    .naver-btn:hover {
        background-color: #02b351;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_datasets' not in st.session_state:
    st.session_state.uploaded_datasets = []

def check_api_connection():
    """API 서버 연결 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def login_page():
    """로그인 페이지"""
    st.markdown('<div class="main-header">🤖 Auto ML Platform</div>', unsafe_allow_html=True)
    
    # API 연결 상태 확인
    if not check_api_connection():
        st.error("❌ API 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.")
        st.info("백엔드 서버 실행 방법:\n```bash\ncd backend\npython main.py\n```")
        return
    
    st.markdown("""
    <div class="login-container">
        <h2 style="text-align: center; margin-bottom: 2rem;">🔐 로그인</h2>
        <p style="text-align: center; color: #666; margin-bottom: 2rem;">
            소셜 계정으로 간편하게 로그인하세요
        </p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔵 Google 로그인", key="google_login"):
            st.markdown(f'<a href="{API_BASE_URL}/auth/google" target="_self" class="social-button google-btn">Google로 계속하기</a>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🟡 Kakao 로그인", key="kakao_login"):
            st.markdown(f'<a href="{API_BASE_URL}/auth/kakao" target="_self" class="social-button kakao-btn">Kakao로 계속하기</a>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🟢 Naver 로그인", key="naver_login"):
            st.markdown(f'<a href="{API_BASE_URL}/auth/naver" target="_self" class="social-button naver-btn">Naver로 계속하기</a>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 로그인 없이 체험하기 (제한된 기능)
    st.markdown("---")
    st.markdown("### 🎯 체험하기 (로그인 없음)")
    st.info("⚠️ 로그인하지 않으면 파일 저장 및 모델 학습 기록이 보관되지 않습니다.")
    
    if st.button("🔓 로그인 없이 체험하기", key="guest_mode"):
        st.session_state.authenticated = True
        st.session_state.user_data = {
            "id": "guest", 
            "name": "게스트", 
            "email": "guest@example.com",
            "provider": "guest"
        }
        st.rerun()

def data_upload_section():
    """데이터 업로드 섹션"""
    st.markdown('<div class="sub-header">📊 데이터 업로드</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "CSV 파일을 업로드하세요",
        type=["csv"],
        help="머신러닝 모델 학습에 사용할 데이터를 업로드하세요"
    )
    
    if uploaded_file is not None:
        try:
            # 파일 업로드 API 호출
            files = {"file": uploaded_file}
            response = requests.post(f"{API_BASE_URL}/api/data/upload", files=files)
            
            if response.status_code == 200:
                result = response.json()
                st.success("✅ 파일이 성공적으로 업로드되었습니다!")
                
                # 데이터 미리보기
                df = pd.read_csv(uploaded_file)
                st.markdown("#### 📋 데이터 미리보기")
                st.dataframe(df.head())
                
                # 기본 통계
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("행 수", f"{len(df):,}")
                with col2:
                    st.metric("열 수", len(df.columns))
                with col3:
                    st.metric("수치형 열", len(df.select_dtypes(include=['number']).columns))
                with col4:
                    st.metric("범주형 열", len(df.select_dtypes(include=['object']).columns))
                
                return result, df
            else:
                st.error(f"❌ 파일 업로드 실패: {response.text}")
                
        except Exception as e:
            st.error(f"❌ 파일 업로드 중 오류가 발생했습니다: {str(e)}")
    
    return None, None

def model_training_section(dataset_info: Dict, df: pd.DataFrame):
    """모델 학습 섹션"""
    st.markdown('<div class="sub-header">🤖 모델 학습 설정</div>', unsafe_allow_html=True)
    
    # 모델 유형 선택
    model_type = st.selectbox(
        "학습할 모델 유형을 선택하세요",
        ["Classification", "Regression", "Clustering", "Recommendation", "Time Series"],
        help="데이터의 특성에 맞는 모델 유형을 선택하세요"
    )
    
    # 타겟 변수 선택 (Clustering 제외)
    target_column = None
    if model_type != "Clustering":
        target_column = st.selectbox(
            "타겟 변수(예측하고자 하는 변수)를 선택하세요",
            df.columns.tolist(),
            help="모델이 예측해야 하는 목표 변수를 선택하세요"
        )
    
    # 특성 변수 선택
    available_features = [col for col in df.columns if col != target_column]
    selected_features = st.multiselect(
        "학습에 사용할 특성 변수들을 선택하세요",
        available_features,
        default=available_features[:min(10, len(available_features))],
        help="모델 학습에 사용할 입력 변수들을 선택하세요"
    )
    
    # 모델 설명
    model_descriptions = {
        "Classification": "📊 **분류 모델**: 범주형 데이터를 예측합니다. 예: 스팸 메일 분류, 고객 등급 분류",
        "Regression": "📈 **회귀 모델**: 연속형 수치 데이터를 예측합니다. 예: 집값 예측, 매출 예측",
        "Clustering": "🔍 **군집 모델**: 비슷한 특성을 가진 데이터를 그룹화합니다. 예: 고객 세분화, 상품 그룹화",
        "Recommendation": "💡 **추천 모델**: 사용자 취향에 맞는 아이템을 추천합니다. 예: 상품 추천, 콘텐츠 추천",
        "Time Series": "⏰ **시계열 모델**: 시간에 따른 데이터 변화를 예측합니다. 예: 주가 예측, 수요 예측"
    }
    
    st.info(model_descriptions[model_type])
    
    # 학습 시작 버튼
    if st.button("🚀 모델 학습 시작", key="start_training"):
        if not selected_features:
            st.error("❌ 최소 하나의 특성 변수를 선택해주세요.")
            return
        
        # 모델 학습 API 호출
        training_data = {
            "dataset_id": dataset_info["id"],
            "model_type": model_type,
            "target_column": target_column,
            "selected_features": selected_features,
            "model_name": f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/ml/train", json=training_data)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                
                # 진행 상황 모니터링
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                while True:
                    # 작업 상태 확인
                    status_response = requests.get(f"{API_BASE_URL}/api/tasks/status/{task_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data["status"] == "progress":
                            progress = status_data.get("progress", 0)
                            message = status_data.get("message", "처리 중...")
                            progress_bar.progress(progress / 100)
                            status_text.text(f"진행률: {progress}% - {message}")
                            
                        elif status_data["status"] == "success":
                            progress_bar.progress(100)
                            status_text.text("✅ 모델 학습 완료!")
                            
                            # 결과 표시
                            result_data = status_data["result"]
                            st.success(result_data["message"])
                            
                            # 성능 지표 표시
                            if "performance_metrics" in result_data:
                                st.markdown("#### 📈 모델 성능 지표")
                                metrics = result_data["performance_metrics"]
                                
                                cols = st.columns(len(metrics))
                                for i, (metric, value) in enumerate(metrics.items()):
                                    with cols[i]:
                                        st.metric(metric.upper(), f"{value:.4f}")
                            
                            break
                            
                        elif status_data["status"] == "failure":
                            st.error(f"❌ 모델 학습 실패: {status_data.get('error', '알 수 없는 오류')}")
                            break
                            
                        else:
                            status_text.text("대기 중...")
                    
                    time.sleep(2)  # 2초마다 상태 확인
                    
            else:
                st.error(f"❌ 모델 학습 요청 실패: {response.text}")
                
        except Exception as e:
            st.error(f"❌ 모델 학습 중 오류가 발생했습니다: {str(e)}")

def chat_section():
    """RAG 챗봇 섹션"""
    st.markdown('<div class="sub-header">💬 AI 챗봇과 대화하기</div>', unsafe_allow_html=True)
    st.markdown("데이터와 모델에 대해 궁금한 것을 물어보세요! AI가 도움을 드립니다.")
    
    # 채팅 히스토리 표시
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**🙋‍♂️ 사용자**: {message['content']}")
            else:
                st.markdown(f"**🤖 AI**: {message['content']}")
            st.markdown("---")
    
    # 채팅 입력
    user_input = st.text_input(
        "메시지를 입력하세요",
        key="chat_input",
        placeholder="예: '업로드한 데이터의 특징을 알려주세요', '어떤 모델이 가장 적합할까요?'"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("📤 전송", key="send_chat")
    with col2:
        if st.button("🗑️ 채팅 기록 지우기", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    if send_button and user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        try:
            # 챗봇 API 호출
            chat_data = {
                "message": user_input,
                "user_id": st.session_state.user_data["id"]
            }
            
            response = requests.post(f"{API_BASE_URL}/api/chat/message", json=chat_data)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["response"]
                
                # AI 응답 추가
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            else:
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": "죄송합니다. 현재 응답할 수 없습니다. 잠시 후 다시 시도해주세요."
                })
                
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"오류가 발생했습니다: {str(e)}"
            })
        
        st.rerun()

def main_app():
    """메인 애플리케이션"""
    st.markdown('<div class="main-header">🤖 Auto ML Platform</div>', unsafe_allow_html=True)
    
    # 사이드바 - 사용자 정보
    with st.sidebar:
        st.markdown("### 👤 사용자 정보")
        user_data = st.session_state.user_data
        st.write(f"**이름**: {user_data['name']}")
        st.write(f"**이메일**: {user_data['email']}")
        st.write(f"**로그인 방식**: {user_data['provider']}")
        
        st.markdown("---")
        
        if st.button("🔓 로그아웃"):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.chat_history = []
            st.rerun()
    
    # 메인 콘텐츠 탭
    tab1, tab2, tab3 = st.tabs(["📊 데이터 & 모델", "💬 AI 챗봇", "📈 모델 관리"])
    
    with tab1:
        # 데이터 업로드
        dataset_info, df = data_upload_section()
        
        if dataset_info and df is not None:
            st.markdown("---")
            # 모델 학습
            model_training_section(dataset_info, df)
    
    with tab2:
        chat_section()
    
    with tab3:
        st.markdown("### 📋 학습된 모델 목록")
        
        try:
            # 사용자의 모델 목록 조회
            response = requests.get(f"{API_BASE_URL}/api/ml/models")
            
            if response.status_code == 200:
                models = response.json()
                
                if models:
                    for model in models:
                        with st.expander(f"🤖 {model['name']} ({model['model_type']})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**생성일**: {model['created_at']}")
                                st.write(f"**상태**: {model['training_status']}")
                                st.write(f"**알고리즘**: {model.get('algorithm', 'N/A')}")
                            
                            with col2:
                                if model.get('performance_metrics'):
                                    st.write("**성능 지표**:")
                                    for metric, value in model['performance_metrics'].items():
                                        st.write(f"- {metric}: {value}")
                            
                            # 예측 기능
                            if model['training_status'] == 'completed':
                                if st.button(f"🔮 {model['name']} 예측하기", key=f"predict_{model['id']}"):
                                    st.info("예측 기능은 개발 중입니다.")
                else:
                    st.info("아직 학습된 모델이 없습니다. '데이터 & 모델' 탭에서 모델을 학습해보세요!")
            else:
                st.error("모델 목록을 불러올 수 없습니다.")
                
        except Exception as e:
            st.error(f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}")

def main():
    """메인 함수"""
    # URL 파라미터에서 인증 토큰 확인
    query_params = st.query_params
    if "token" in query_params and not st.session_state.authenticated:
        token = query_params.get("token", [""])[0]
        
        try:
            # 토큰으로 사용자 정보 조회
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{API_BASE_URL}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                st.session_state.authenticated = True
                st.session_state.user_data = user_data
                
                # URL 파라미터 제거 (새 방법으로는 자동으로 처리됨)
                st.rerun()
            else:
                st.error("인증에 실패했습니다. 다시 로그인해주세요.")
        except Exception as e:
            st.error(f"인증 처리 중 오류가 발생했습니다: {str(e)}")
    
    # 인증 상태에 따라 페이지 표시
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()