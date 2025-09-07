import streamlit as st
import requests
import os
import pandas as pd
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

st.set_page_config(page_title="모델 학습", page_icon="🧠")

def get_columns_from_dataframe_path(file_path: str) -> List[str]:
    """Parquet 파일에서 컬럼 목록을 가져옵니다."""
    try:
        df = pd.read_parquet(file_path)
        return df.columns.tolist()
    except Exception as e:
        logger.error(f"Failed to read parquet file for columns: {e}", exc_info=True)
        st.error(f"데이터 파일을 읽는 데 실패했습니다: {e}")
        return []

def train_model_on_backend(
    file_path: str,
    target_column: str,
    model_type: str,
    features: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """백엔드 API를 호출하여 모델 학습을 시작합니다."""
    api_url = os.getenv("API_URL")
    if not api_url:
        st.error("API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    payload = {
        "file_path": file_path,
        "target_column": target_column,
        "model_type": model_type,
        "features": features
    }
    
    try:
        response = requests.post(f"{api_url.rstrip('/')}/ml/train-model/", json=payload, timeout=300) # Increased timeout
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"모델 학습 요청에 실패했습니다: {e}")
        logger.error(f"Failed to request model training from backend: {e}", exc_info=True)
        return None

def main():
    st.title("🧠 머신러닝 모델 학습")
    st.markdown("업로드된 데이터를 사용하여 다양한 머신러닝 모델을 학습시킵니다.")

    if not st.session_state.get("logged_in"):
        st.warning("로그인 후 이용 가능한 페이지입니다. 로그인 페이지로 이동합니다.")
        st.session_state["page"] = "login"
        st.switch_page("_login")
        st.stop()

    if not st.session_state.get("csv_analysis_complete") or not st.session_state.get("current_dataframe_path"):
        st.info("먼저 '홈' 페이지에서 CSV 파일을 업로드하고 분석을 완료해주세요.")
        st.session_state["page"] = "main_app" # Redirect to main app to upload CSV
        st.switch_page("app")
        st.stop()

    st.write(f"현재 학습에 사용할 파일: **{os.path.basename(st.session_state.current_dataframe_path)}**")

    # 데이터프레임 컬럼 가져오기
    all_columns = get_columns_from_dataframe_path(st.session_state.current_dataframe_path)
    if not all_columns:
        st.error("데이터 파일에서 컬럼 정보를 가져올 수 없습니다.")
        st.stop()

    st.subheader("모델 학습 설정")

    # 타겟 변수 선택
    target_column = st.selectbox(
        "예측하고자 하는 타겟 변수를 선택하세요",
        options=["선택 안 함"] + all_columns,
        key="ml_target_selector"
    )

    # 분석 변수 선택
    feature_columns = st.multiselect(
        "모델 학습에 사용할 분석 변수들을 선택하세요",
        options=[col for col in all_columns if col != target_column and col != "선택 안 함"],
        default=[col for col in all_columns if col != target_column and col != "선택 안 함"],
        key="ml_feature_selector"
    )

    # AI 추천 모델 유형 표시
    recommended_model_types = st.session_state.get("model_recommendations", {}).get("model_types", [])
    recommended_explanation = st.session_state.get("model_recommendations", {}).get("explanation", "")

    st.markdown("---")
    st.subheader("AI 추천 모델 유형")
    if recommended_model_types:
        st.info(f"**추천 모델 유형:** {', '.join(recommended_model_types)}")
        st.write(recommended_explanation)
    else:
        st.warning("AI 모델 추천 결과가 없습니다. '홈' 페이지에서 CSV 분석을 다시 실행해주세요.")

    # 사용자 모델 유형 선택
    st.markdown("---")
    st.subheader("모델 유형 선택")
    model_type_options = ["Classification", "Regression", "Clustering"]
    if "Time Series Forecasting" in recommended_model_types:
        model_type_options.append("Time Series Forecasting") # Add if recommended
    if "Recommendation" in recommended_model_types:
        model_type_options.append("Recommendation") # Add if recommended

    selected_model_type = st.selectbox(
        "학습할 모델 유형을 선택하세요",
        options=model_type_options,
        key="model_type_selector"
    )

    st.markdown("---")
    if st.button("🚀 모델 학습 시작", type="primary", use_container_width=True):
        if target_column == "선택 안 함" and selected_model_type in ["Classification", "Regression"]:
            st.error("분류 또는 회귀 모델 학습을 위해서는 타겟 변수를 선택해야 합니다.")
        elif not feature_columns and selected_model_type in ["Classification", "Regression", "Clustering"]:
            st.error("모델 학습을 위해서는 분석 변수를 하나 이상 선택해야 합니다.")
        else:
            with st.spinner(f"{selected_model_type} 모델 학습 중..."):
                result = train_model_on_backend(
                    file_path=st.session_state.current_dataframe_path,
                    target_column=target_column if target_column != "선택 안 함" else None,
                    model_type=selected_model_type,
                    features=feature_columns
                )
                if result:
                    st.success("모델 학습이 성공적으로 완료되었습니다!")
                    st.json(result) # Display full result for now
                    st.session_state.trained_model_info = result # Store model info
                else:
                    st.error("모델 학습에 실패했습니다.")

    # 학습된 모델 정보 표시
    if st.session_state.get("trained_model_info"):
        st.markdown("---")
        st.subheader("학습된 모델 정보")
        st.json(st.session_state.trained_model_info)

if __name__ == "__main__":
    main()
