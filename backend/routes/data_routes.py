from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form # Add Form
from typing import List, Optional, Dict, Any # Add Optional, Dict, Any
import pandas as pd
import io # Added for BytesIO
import os
from utils.logger import logger
from services.data_service import process_uploaded_csv, get_dataframe_info, get_column_unique_values, UPLOAD_DIR
from services.auto_ml import AutoMLService # Add this import

router = APIRouter()

# Initialize AutoMLService
auto_ml_service = AutoMLService()

@router.post("/upload")
@router.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...), target_column: Optional[str] = Form(None)):
    """
    CSV 파일을 업로드하여 머신러닝 분석을 위한 데이터를 준비하고,
    데이터에 기반한 모델 유형을 추천하며, AutoML 파이프라인을 실행합니다.
    """
    if not file.filename.endswith(".csv"):
        logger.warning(f"Invalid file upload attempt: {file.filename} is not a CSV.")
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드할 수 있습니다.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # Process the CSV and get file_path
        # This part now only saves the file and returns its path
        # Recommendations will be handled by AutoMLService
        processed_data_info = await process_uploaded_csv(df, file.filename, target_column)
        file_path = processed_data_info["file_path"]

        # Run AutoML pipeline
        auto_ml_results = await auto_ml_service.run_auto_ml_pipeline(
            file_path=file_path,
            target_column=target_column,
            # features=... # Features can be passed if selected by user in frontend
        )

        logger.info(f"CSV file '{file.filename}' uploaded and AutoML pipeline executed successfully.")
        
        # Combine results
        response_data = {
            "message": f"파일 '{file.filename}'이 성공적으로 업로드 및 AutoML 분석이 완료되었습니다.",
            "file_path": file_path,
            "auto_ml_results": auto_ml_results["results"] # Contains recommendations, training_result, predictions
        }
        return response_data
    except Exception as e:
        logger.error(f"Error processing CSV upload and AutoML for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"파일 처리 및 AutoML 실행 중 오류가 발생했습니다: {e}")

@router.get("/data-info/{file_name:path}")
async def get_data_info(file_name: str):
    """
    업로드된 데이터 파일의 기본 정보를 조회합니다.
    컬럼 목록, 데이터 타입, 데이터 크기, 결측치 정보 등 데이터의 전반적인 개요를 제공합니다.
    """
    file_path = os.path.join(UPLOAD_DIR, file_name) # UPLOAD_DIR needs to be imported or defined
    if not os.path.exists(file_path):
        logger.warning(f"Data info request for non-existent file: {file_name}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    try:
        info = get_dataframe_info(file_path)
        logger.info(f"Data info retrieved for {file_name}.")
        return info
    except Exception as e:
        logger.error(f"Error getting data info for {file_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"데이터 정보 조회 중 오류가 발생했습니다: {e}")

@router.get("/column-unique-values/{file_name:path}/{column_name}")
async def get_unique_values(file_name: str, column_name: str):
    """
    특정 컬럼의 고유 값과 각 값의 빈도수를 조회합니다.
    범주형 변수의 분포를 이해하고 데이터의 특성을 파악하는 데 유용합니다.
    """
    file_path = os.path.join(UPLOAD_DIR, file_name) # UPLOAD_DIR needs to be imported or defined
    if not os.path.exists(file_path):
        logger.warning(f"Unique values request for non-existent file: {file_name}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    try:
        unique_values = get_column_unique_values(file_path, column_name)
        logger.info(f"Unique values retrieved for column {column_name} in {file_name}.")
        return unique_values
    except ValueError as ve:
        logger.warning(f"Column not found for unique values request: {column_name} in {file_name}. Error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting unique values for {column_name} in {file_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"컬럼 고유 값 조회 중 오류가 발생했습니다: {e}")

from services.data_service import get_correlation_matrix, get_feature_importance # Add these imports
from pydantic import BaseModel # Already imported, but ensure it's there

class FeatureImportanceRequest(BaseModel):
    file_path: str
    target_column: str
    model_type: str
    features: Optional[List[str]] = None

@router.get("/correlation-matrix/{file_name:path}")
async def get_correlation(file_name: str):
    """
    업로드된 데이터 파일의 수치형 컬럼들 간의 상관관계 행렬을 조회합니다.
    """
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        logger.warning(f"Correlation matrix request for non-existent file: {file_name}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    try:
        correlation_data = get_correlation_matrix(file_path)
        logger.info(f"Correlation matrix retrieved for {file_name}.")
        return correlation_data
    except Exception as e:
        logger.error(f"Error getting correlation matrix for {file_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"상관관계 행렬 조회 중 오류가 발생했습니다: {e}")

@router.post("/feature-importance/")
async def get_feature_imp(request: FeatureImportanceRequest):
    """
    지정된 데이터와 모델 유형을 사용하여 특성 중요도를 계산합니다.
    """
    logger.info(f"Received request for feature importance for {request.file_path}")
    try:
        feature_importance_data = get_feature_importance(
            file_path=request.file_path,
            target_column=request.target_column,
            model_type=request.model_type,
            features=request.features
        )
        logger.info(f"Feature importance calculated for {request.file_path}.")
        return feature_importance_data
    except Exception as e:
        logger.error(f"Error during feature importance API call for {request.file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"특성 중요도 계산 중 오류가 발생했습니다: {e}")

from services.report_service import ReportService # Add this import

# Initialize ReportService
report_service = ReportService()

class ReportRequest(BaseModel):
    file_path: str
    report_data: Dict[str, Any]
    chart_image_path: str # Path to a temporary image file of the chart

class EmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str
    attachment_path: Optional[str] = None

@router.post("/generate-report/")
async def generate_report(request: ReportRequest):
    """
    데이터 분석 결과를 PDF 보고서로 생성합니다.
    """
    logger.info(f"Received request to generate report for {request.file_path}")
    try:
        pdf_path = report_service.generate_pdf_report(
            chart_image_path=request.chart_image_path,
            report_data=request.report_data
        )
        logger.info(f"Report generated at {pdf_path}")
        return {"message": "PDF 보고서가 성공적으로 생성되었습니다.", "pdf_path": pdf_path}
    except Exception as e:
        logger.error(f"Error generating report for {request.file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF 보고서 생성 중 오류가 발생했습니다: {e}")

@router.post("/send-email/")
async def send_report_email(request: EmailRequest):
    """
    생성된 보고서를 이메일로 발송합니다.
    """
    logger.info(f"Received request to send email to {request.recipient_email}")
    try:
        report_service.send_email_with_attachment(
            recipient_email=request.recipient_email,
            subject=request.subject,
            body=request.body,
            attachment_path=request.attachment_path
        )
        logger.info(f"Email sent to {request.recipient_email}.")
        return {"message": "이메일이 성공적으로 발송되었습니다."}
    except Exception as e:
        logger.error(f"Error sending email to {request.recipient_email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"이메일 발송 중 오류가 발생했습니다: {e}")