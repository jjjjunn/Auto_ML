import streamlit as st
import os
import logging

logger = logging.getLogger(__name__)

def initialize_app():
    """
    Streamlit 애플리케이션의 초기 설정을 수행합니다.
    세션 상태 변수들을 초기화하고, 필요한 경우 API 연결 상태를 확인합니다.
    """
    if "show_progress" not in st.session_state:
        st.session_state.show_progress = True
    if "auto_clean" not in st.session_state:
        st.session_state.auto_clean = True
    if "use_rag" not in st.session_state:
        st.session_state.use_rag = True
    if "current_ingredients" not in st.session_state:
        st.session_state.current_ingredients = []
    if "current_ocr_result" not in st.session_state:
        st.session_state.current_ocr_result = None
    if "image_analysis_complete" not in st.session_state:
        st.session_state.image_analysis_complete = False
    if "csv_analysis_complete" not in st.session_state: # Added for CSV
        st.session_state.csv_analysis_complete = False
    if "current_dataframe_path" not in st.session_state: # Added for CSV
        st.session_state.current_dataframe_path = None
    if "model_recommendations" not in st.session_state: # Added for CSV
        st.session_state.model_recommendations = None

    # API URL 확인 (backend connection)
    api_url = os.getenv("API_URL")
    if not api_url:
        logger.error("API_URL 환경 변수가 설정되지 않았습니다. 백엔드 연결에 문제가 있을 수 있습니다.")
        st.error("백엔드 API URL이 설정되지 않았습니다. `.env` 파일을 확인해주세요.")
