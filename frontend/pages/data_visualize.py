import streamlit as st
import requests
import os
import pandas as pd
import logging
import plotly.express as px
from typing import List, Optional, Dict, Any
import base64
from datetime import datetime
from backend.services.report_service import generate_pdf_report_on_backend, send_email_on_backend


logger = logging.getLogger(__name__)

st.set_page_config(page_title="데이터 분석 (EDA)", page_icon="📊")

def get_data_info_from_backend(file_path: str):
    """백엔드에서 데이터 정보를 가져옵니다."""
    api_url = os.getenv("API_URL")
    if not api_url:
        st.error("API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    # file_path needs to be converted to file_name for the API call
    file_name = os.path.basename(file_path)
    
    try:
        response = requests.get(f"{api_url.rstrip('/')}/data/data-info/{file_name}")
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"백엔드에서 데이터 정보를 가져오는 데 실패했습니다: {e}")
        logger.error(f"Failed to fetch data info from backend: {e}", exc_info=True)
        return None

def get_column_unique_values_from_backend(file_path: str, column_name: str):
    """백엔드에서 특정 컬럼의 고유 값을 가져옵니다."""
    api_url = os.getenv("API_URL")
    if not api_url:
        st.error("API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    file_name = os.path.basename(file_path)
    
    try:
        response = requests.get(f"{api_url.rstrip('/')}/data/column-unique-values/{file_name}/{column_name}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"백엔드에서 컬럼 고유 값을 가져오는 데 실패했습니다: {e}")
        logger.error(f"Failed to fetch column unique values from backend: {e}", exc_info=True)
        return None

def get_correlation_matrix_from_backend(file_path: str):
    """백엔드에서 상관관계 행렬을 가져옵니다."""
    api_url = os.getenv("API_URL")
    if not api_url:
        st.error("API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    file_name = os.path.basename(file_path)
    
    try:
        response = requests.get(f"{api_url.rstrip('/')}/data/correlation-matrix/{file_name}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"백엔드에서 상관관계 행렬을 가져오는 데 실패했습니다: {e}")
        logger.error(f"Failed to fetch correlation matrix from backend: {e}", exc_info=True)
        return None

def get_feature_importance_from_backend(
    file_path: str,
    target_column: str,
    model_type: str,
    features: Optional[List[str]] = None
):
    """백엔드에서 특성 중요도를 가져옵니다."""
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
        response = requests.post(f"{api_url.rstrip('/')}/data/feature-importance/", json=payload, timeout=120) # Increased timeout
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"백엔드에서 특성 중요도를 가져오는 데 실패했습니다: {e}")
        logger.error(f"Failed to fetch feature importance from backend: {e}", exc_info=True)
        return None

def main():
    st.title("📊 데이터 분석 (EDA)")
    st.markdown("업로드된 CSV 파일의 데이터를 탐색하고 시각화합니다.")

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

    st.write(f"현재 분석 중인 파일: **{os.path.basename(st.session_state.current_dataframe_path)}**")

    data_info = get_data_info_from_backend(st.session_state.current_dataframe_path)

    if data_info:
        st.subheader("데이터 개요")
        st.write(f"행: {data_info['shape'][0]}, 열: {data_info['shape'][1]}")
        
        st.subheader("컬럼 정보")
        col_info_df = pd.DataFrame({
            "컬럼명": data_info['columns'],
            "데이터 타입": [data_info['data_types'][col] for col in data_info['columns']],
            "결측치 수": [data_info['missing_values'][col] for col in data_info['columns']],
            "고유 값 수": [data_info['unique_values_count'][col] for col in data_info['columns']]
        })
        st.dataframe(col_info_df)

        st.subheader("데이터 미리보기 (상위 5행)")
        st.dataframe(pd.DataFrame(data_info['head']))

        st.subheader("기본 통계")
        st.dataframe(pd.DataFrame(data_info['description']))

        st.subheader("컬럼별 상세 분석 및 시각화")
        selected_column = st.selectbox("상세 분석할 컬럼을 선택하세요", data_info['columns'])
        
        if selected_column:
            col_type = data_info['data_types'][selected_column]
            st.write(f"선택된 컬럼: **{selected_column}** (타입: {col_type})")

            # 고유 값 빈도
            unique_values_data = get_column_unique_values_from_backend(st.session_state.current_dataframe_path, selected_column)
            if unique_values_data:
                st.write(f"**'{selected_column}' 컬럼 고유 값 빈도:**")
                st.write(unique_values_data['unique_values'])
                
                # 시각화: 범주형 데이터 (막대 그래프)
                if col_type == 'categorical':
                    df_unique = pd.DataFrame(list(unique_values_data['unique_values'].items()), columns=['Value', 'Count'])
                    fig = px.bar(df_unique, x='Value', y='Count', title=f"'{selected_column}' 컬럼 빈도")
                    st.plotly_chart(fig, use_container_width=True)
                # 시각화: 수치형 데이터 (히스토그램)
                elif col_type in ['int64', 'float64']:
                    # Need to load the actual dataframe to plot histogram
                    try:
                        df_full = pd.read_parquet(st.session_state.current_dataframe_path)
                        fig = px.histogram(df_full, x=selected_column, title=f"'{selected_column}' 컬럼 분포")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"히스토그램 생성 중 오류 발생: {e}")
                        logger.warning(f"Histogram creation error: {e}", exc_info=True)
            else:
                st.info("선택된 컬럼의 상세 정보를 가져올 수 없습니다.")
        
        st.markdown("---")
        st.subheader("상관관계 분석")
        correlation_data = get_correlation_matrix_from_backend(st.session_state.current_dataframe_path)
        if correlation_data and "correlation_matrix" in correlation_data:
            corr_df = pd.DataFrame(correlation_data["correlation_matrix"])
            st.dataframe(corr_df)
            fig = px.imshow(corr_df, text_auto=True, aspect="auto", title="컬럼 간 상관관계")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("상관관계 행렬을 계산할 수 있는 수치형 데이터가 없거나 오류가 발생했습니다.")

        st.markdown("---")
        st.subheader("특성 중요도 분석")
        if st.session_state.get("trained_model_info"):
            model_info = st.session_state.trained_model_info
            if model_info.get("model_path") and model_info.get("target_column") and model_info.get("model_type") in ["Classification", "Regression"]:
                st.info(f"학습된 모델 ({model_info['model_type']})을 기반으로 특성 중요도를 계산합니다.")
                
                # Get features from the trained model info
                features_from_model = model_info.get("features") # Assuming features are stored in model_info
                if not features_from_model: # Fallback if not explicitly stored
                    # Try to infer from data_info if target is known
                    if model_info.get("target_column") and data_info.get("columns"):
                        features_from_model = [col for col in data_info["columns"] if col != model_info["target_column"]]
                    else:
                        st.warning("특성 중요도를 계산할 특성 목록을 가져올 수 없습니다.")
                        features_from_model = []

                if features_from_model:
                    feature_importance_data = get_feature_importance_from_backend(
                        file_path=st.session_state.current_dataframe_path,
                        target_column=model_info["target_column"],
                        model_type=model_info["model_type"],
                        features=features_from_model
                    )
                    if feature_importance_data and "feature_importance" in feature_importance_data:
                        imp_df = pd.DataFrame(
                            list(feature_importance_data["feature_importance"].items()),
                            columns=["Feature", "Importance"]
                        ).sort_values(by="Importance", ascending=False)
                        
                        fig = px.bar(imp_df, x="Importance", y="Feature", orientation='h', title="특성 중요도")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("특성 중요도를 가져오는 데 실패했습니다.")
                else:
                    st.warning("특성 중요도를 계산할 특성 목록이 없습니다.")
            else:
                st.info("특성 중요도 계산을 위한 학습된 분류 또는 회귀 모델 정보가 없습니다.")
        else:
            st.info("특성 중요도 분석을 위해서는 먼저 '모델 학습' 페이지에서 모델을 학습시켜야 합니다.")

    else:
        st.error("데이터 정보를 가져오는 데 실패했습니다. '홈' 페이지에서 CSV 파일을 다시 업로드해주세요.")

    # PDF Download and Email Section
    st.markdown("---")
    st.subheader("보고서 생성 및 공유")
    
    # Get the last generated Plotly figure (if any)
    # This is a simplified way; in a real app, you'd manage figures more robustly
    last_fig = None
    if st.session_state.get("last_plotly_fig"):
        last_fig = st.session_state.last_plotly_fig
    
    if last_fig:
        col_pdf, col_email = st.columns(2)
        
        with col_pdf:
            if st.button("PDF 보고서 다운로드", type="primary", use_container_width=True):
                with st.spinner("PDF 보고서 생성 중..."):
                    # Convert Plotly figure to image bytes
                    img_bytes = last_fig.to_image(format="png", scale=2) # scale for higher resolution
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                    report_data = {
                        "file_name": os.path.basename(st.session_state.current_dataframe_path),
                        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "model_type": st.session_state.get("trained_model_info", {}).get("model_type", "N/A"),
                        "description": "데이터 분석 결과 보고서"
                    }
                    
                    pdf_result = generate_pdf_report_on_backend(img_base64, report_data)
                    if pdf_result and pdf_result.get("pdf_path"):
                        st.success(f"PDF 보고서가 성공적으로 생성되었습니다: {os.path.basename(pdf_result['pdf_path'])}")
                        # Provide a download link (requires backend to serve the file)
                        # For local testing, user can manually retrieve from 'generated_reports' folder
                        st.info(f"생성된 PDF는 서버의 '{os.path.basename(os.path.dirname(pdf_result['pdf_path']))}' 폴더에서 확인하실 수 있습니다.")
                        st.session_state.last_generated_pdf_path = pdf_result['pdf_path'] # Store the path
                    else:
                        st.error("PDF 보고서 생성에 실패했습니다.")
        
        with col_email:
            with st.expander("이메일로 보고서 공유"):
                recipient = st.text_input("받는 사람 이메일 주소", key="email_recipient")
                email_subject = st.text_input("이메일 제목", value=f"Auto_ML 분석 보고서: {os.path.basename(st.session_state.current_dataframe_path)}", key="email_subject")
                email_body = st.text_area("이메일 내용", value="첨부된 PDF 보고서를 확인해주세요.", key="email_body")
                
                if st.button("이메일 발송", type="secondary", use_container_width=True):
                    if not recipient:
                        st.error("받는 사람 이메일 주소를 입력해주세요.")
                    else:
                        with st.spinner("이메일 발송 중..."):
                            # Assuming PDF was just generated and its path is known
                            pdf_path_for_email = st.session_state.get("last_generated_pdf_path") # Store this after PDF generation
                            
                            email_result = send_email_on_backend(
                                recipient_email=recipient,
                                subject=email_subject,
                                body=email_body,
                                attachment_path=pdf_path_for_email
                            )
                            if email_result:
                                st.success("이메일이 성공적으로 발송되었습니다!")
                            else:
                                st.error("이메일 발송에 실패했습니다.")
    else:
        st.info("보고서 생성 및 공유를 위해서는 먼저 차트를 생성해주세요.")

if __name__ == "__main__":
    main()
