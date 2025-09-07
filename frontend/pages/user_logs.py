import streamlit as st
import requests
import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

st.set_page_config(page_title="사용자 로그", page_icon="📈")

def get_user_activities_from_backend(user_id: Optional[int] = None, activity_type: Optional[str] = None):
    """백엔드에서 사용자 활동 로그를 가져옵니다."""
    api_url = os.getenv("API_URL")
    if not api_url:
        st.error("API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    params = {}
    if user_id:
        params["user_id"] = user_id
    if activity_type:
        params["activity_type"] = activity_type

    try:
        response = requests.get(f"{api_url.rstrip('/')}/logs/activities/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"활동 로그를 가져오는 데 실패했습니다: {e}")
        logger.error(f"Failed to fetch activity logs from backend: {e}", exc_info=True)
        return None

def main():
    st.title("📈 사용자 활동 로그")
    st.markdown("시스템 및 사용자 활동 기록을 확인합니다.")

    if not st.session_state.get("logged_in"):
        st.warning("로그인 후 이용 가능한 페이지입니다. 로그인 페이지로 이동합니다.")
        st.session_state["page"] = "login"
        st.switch_page("_login")
        st.stop()

    current_user_id = st.session_state.get("user_id")
    
    st.subheader("내 활동 로그")
    
    # Filter options (can be expanded)
    activity_types = ["file_upload", "model_train", "chart_view", "login", "logout", "chat_query"] # Example types
    selected_activity_type = st.selectbox("활동 유형 필터", ["모두"] + activity_types)

    # Fetch logs
    if selected_activity_type == "모두":
        logs = get_user_activities_from_backend(user_id=current_user_id)
    else:
        logs = get_user_activities_from_backend(user_id=current_user_id, activity_type=selected_activity_type)

    if logs:
        log_df = pd.DataFrame(logs)
        log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
        log_df = log_df.sort_values(by="timestamp", ascending=False)
        
        # Display logs
        st.dataframe(log_df[["timestamp", "activity_type", "description"]])
    else:
        st.info("기록된 활동 로그가 없습니다.")

    st.markdown("---")
    st.subheader("관리자용: 전체 활동 로그 (구현 예정)")
    st.info("관리자 권한이 있는 경우, 모든 사용자의 활동 로그를 조회할 수 있는 기능이 여기에 추가될 예정입니다.")

if __name__ == "__main__":
    main()