from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from utils.logger import logger
from services.ml_service import train_model
from pydantic import BaseModel

router = APIRouter()

class TrainModelRequest(BaseModel):
    file_path: str
    target_column: str
    model_type: str
    features: Optional[List[str]] = None

@router.post("/train-model/")
async def train_ml_model(request: TrainModelRequest):
    """
    업로드된 데이터를 사용하여 머신러닝 모델을 학습시킵니다.
    사용자는 데이터 파일 경로, 타겟 변수, 모델 유형을 지정할 수 있습니다.
    """
    logger.info(f"Received request to train model: {request.model_type} for {request.file_path}")
    try:
        result = train_model(
            file_path=request.file_path,
            target_column=request.target_column,
            model_type=request.model_type,
            features=request.features
        )
        logger.info(f"Model training completed for {request.file_path}.")
        return result
    except Exception as e:
        logger.error(f"Error during model training API call for {request.file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"모델 학습 중 오류가 발생했습니다: {e}")

from services.ml_service import predict_with_model # Add this import
from pydantic import BaseModel, Field
import pandas as pd # For DataFrame conversion
import io # For BytesIO
import os
import glob

class PredictModelRequest(BaseModel):
    model_path: str = Field(..., description="예측에 사용할 학습된 모델의 경로")
    data_to_predict: List[Dict[str, Any]] = Field(..., description="예측할 데이터 (JSON 형식의 리스트)")

@router.post("/predict/")
async def predict_ml_model(request: PredictModelRequest):
    """
    학습된 모델을 사용하여 새로운 데이터에 대한 예측을 수행합니다.
    """
    logger.info(f"Received request to predict with model: {request.model_path}")
    try:
        # Convert list of dicts to DataFrame
        data_df = pd.DataFrame(request.data_to_predict)
        
        predictions = predict_with_model(
            model_path=request.model_path,
            data_to_predict=data_df
        )
        logger.info(f"Prediction completed for {len(data_df)} samples.")
        return {"predictions": predictions}
    except Exception as e:
        logger.error(f"Error during prediction API call for {request.model_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"예측 중 오류가 발생했습니다: {e}")

@router.get("/models")
async def get_models():
    """
    저장된 모델 목록을 조회합니다.
    """
    logger.info("Received request to get saved models")
    try:
        # models 디렉토리에서 저장된 모델 파일들 검색
        models_dir = "models"
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            return {"models": [], "message": "모델 디렉토리가 생성되었습니다. 학습된 모델이 없습니다."}
        
        # .pkl 또는 .joblib 파일들을 검색
        model_files = []
        for ext in ['*.pkl', '*.joblib']:
            model_files.extend(glob.glob(os.path.join(models_dir, ext)))
        
        models = []
        for model_file in model_files:
            model_info = {
                "name": os.path.basename(model_file),
                "path": model_file,
                "size": os.path.getsize(model_file),
                "created_time": os.path.getctime(model_file)
            }
            models.append(model_info)
        
        logger.info(f"Found {len(models)} models")
        return {"models": models, "total": len(models)}
    except Exception as e:
        logger.error(f"Error getting saved models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 중 오류가 발생했습니다: {e}")

@router.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """
    지정된 모델을 삭제합니다.
    """
    logger.info(f"Received request to delete model: {model_name}")
    try:
        models_dir = "models"
        model_path = os.path.join(models_dir, model_name)
        
        if not os.path.exists(model_path):
            logger.warning(f"Model not found: {model_name}")
            raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다.")
        
        os.remove(model_path)
        logger.info(f"Model deleted: {model_name}")
        return {"message": f"모델 '{model_name}'이 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"모델 삭제 중 오류가 발생했습니다: {e}")