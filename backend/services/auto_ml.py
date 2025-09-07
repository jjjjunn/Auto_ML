import pandas as pd
import os
from typing import Dict, Any, Optional, List
from utils.logger import logger
from .ai_recommendation_service import recommend_model_type
from .ml_service import train_model, predict_with_model

class AutoMLService:
    """
    CSV 파일을 업로드하면 파일 형태에 따라 자동으로 머신러닝을 수행(학습 및 예측)하는 서비스입니다.
    머신러닝을 모르는 사용자도 쉽게 사용할 수 있도록 자동화된 파이프라인을 제공합니다.
    """
    def __init__(self):
        logger.info("AutoMLService initialized.")

    async def run_auto_ml_pipeline(
        self,
        file_path: str,
        target_column: Optional[str] = None,
        features: Optional[List[str]] = None,
        predict_new_data: Optional[pd.DataFrame] = None # For future prediction
    ) -> Dict[str, Any]:
        """
        CSV 파일을 분석하고, AI 추천을 기반으로 모델을 학습하며, 필요시 예측을 수행하는 자동화된 파이프라인.
        """
        logger.info(f"Starting AutoML pipeline for file: {file_path}")
        results = {}

        try:
            df = pd.read_parquet(file_path)
            logger.info(f"DataFrame loaded from {file_path}. Shape: {df.shape}")

            # 1. AI 모델 추천
            recommendations = recommend_model_type(df, target_column)
            results["recommendations"] = recommendations
            logger.info(f"Model recommendations: {recommendations['model_types']}")

            # 2. 자동 모델 학습 (타겟 변수가 있고, 추천 모델 유형이 분류/회귀인 경우)
            if target_column and target_column in df.columns and \
               ("Classification" in recommendations["model_types"] or "Regression" in recommendations["model_types"]):
                
                # Use the first recommended supervised model type
                model_type_to_train = None
                if "Classification" in recommendations["model_types"]:
                    model_type_to_train = "Classification"
                elif "Regression" in recommendations["model_types"]:
                    model_type_to_train = "Regression"

                if model_type_to_train:
                    logger.info(f"Automatically training {model_type_to_train} model.")
                    train_result = train_model(
                        file_path=file_path,
                        target_column=target_column,
                        model_type=model_type_to_train,
                        features=features
                    )
                    results["training_result"] = train_result
                    logger.info(f"Model training completed: {train_result.get('model_path')}")

                    # 3. 자동 예측 (새로운 데이터가 제공된 경우)
                    if predict_new_data is not None and not predict_new_data.empty:
                        logger.info(f"Performing prediction on new data ({predict_new_data.shape[0]} samples).")
                        # Ensure prediction data has the same features as training data
                        if features:
                            predict_data_filtered = predict_new_data[features]
                        else: # If features were not explicitly selected, use all except target
                            predict_data_filtered = predict_new_data.drop(columns=[target_column], errors='ignore')
                        
                        predictions = predict_with_model(
                            model_path=train_result["model_path"],
                            data_to_predict=predict_data_filtered
                        )
                        results["predictions"] = predictions
                        logger.info("Prediction completed.")
                else:
                    logger.info("No suitable supervised model type recommended for automatic training.")
            else:
                logger.info("Target column not provided or not suitable for automatic supervised training.")

            return {"status": "success", "message": "AutoML 파이프라인 실행 완료", "results": results}

        except Exception as e:
            logger.error(f"Error in AutoML pipeline for {file_path}: {e}", exc_info=True)
            return {"status": "error", "message": f"AutoML 파이프라인 실행 중 오류 발생: {e}"}