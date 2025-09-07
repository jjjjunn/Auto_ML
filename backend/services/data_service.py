import pandas as pd
import os
import aiofiles # For async file writing
from utils.logger import logger
from typing import Dict, Any, Optional, List # Keep Optional, Dict, Any, List

UPLOAD_DIR = "uploaded_data" # Directory to save uploaded files

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def process_uploaded_csv(df: pd.DataFrame, filename: str, target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    업로드된 CSV 데이터를 처리하고 저장합니다.
    """
    file_base, file_ext = os.path.splitext(filename)
    save_path = os.path.join(UPLOAD_DIR, f"{file_base}.parquet")

    try:
        df.to_parquet(save_path, index=False)
        logger.info(f"DataFrame saved to {save_path}")

        return {
            "message": f"파일 '{filename}'이 성공적으로 업로드 및 처리되었습니다.",
            "file_path": save_path,
        }
    except Exception as e:
        logger.error(f"Failed to process and save DataFrame for {filename}: {e}", exc_info=True)
        raise

def get_dataframe_info(file_path: str) -> Dict[str, Any]:
    """
    저장된 Parquet 파일에서 DataFrame 정보를 로드하고 기본 통계를 반환합니다.
    이 기능은 사용자가 업로드한 데이터의 전반적인 특성을 빠르게 파악하는 데 도움을 줍니다.
    """
    logger.info(f"Loading DataFrame info from {file_path}")
    try:
        df = pd.read_parquet(file_path)

        info = {
            "columns": df.columns.tolist(),
            "data_types": {col: str(df[col].dtype) for col in df.columns},
            "shape": df.shape,
            "head": df.head().to_dict(orient="records"),
            "description": df.describe(include='all').to_dict(), # Basic statistics
            "missing_values": df.isnull().sum().to_dict(),
            "unique_values_count": {col: df[col].nunique() for col in df.columns}
        }
        logger.info(f"DataFrame info extracted for {file_path}")
        return info
    except Exception as e:
        logger.error(f"Failed to get DataFrame info from {file_path}: {e}", exc_info=True)
        raise

def get_column_unique_values(file_path: str, column_name: str, top_n: int = 20) -> Dict[str, Any]:
    """
    특정 컬럼의 고유 값과 빈도수를 반환합니다.
    범주형 변수의 분포를 이해하는 데 유용합니다.
    """
    logger.info(f"Getting unique values for column '{column_name}' from {file_path}")
    try:
        df = pd.read_parquet(file_path)
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame.")

        unique_values = df[column_name].value_counts().nlargest(top_n).to_dict()
        logger.info(f"Unique values extracted for column '{column_name}'.")
        return {"column_name": column_name, "unique_values": unique_values}
    except Exception as e:
        logger.error(f"Failed to get unique values for column '{column_name}' from {file_path}: {e}", exc_info=True)
        raise


import numpy as np # Added for correlation
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor # For feature importance
from sklearn.inspection import permutation_importance # For permutation importance

def get_correlation_matrix(file_path: str) -> Dict[str, Any]:
    """
    저장된 Parquet 파일에서 수치형 컬럼들의 상관관계 행렬을 계산합니다.
    변수들 간의 선형 관계 강도와 방향을 파악하는 데 유용합니다.
    """
    logger.info(f"Calculating correlation matrix for {file_path}")
    try:
        df = pd.read_parquet(file_path)
        numeric_df = df.select_dtypes(include=np.number)
        if numeric_df.empty:
            return {"message": "수치형 데이터가 없어 상관관계 행렬을 계산할 수 없습니다."}
        
        corr_matrix = numeric_df.corr().to_dict()
        logger.info(f"Correlation matrix calculated for {file_path}")
        return {"correlation_matrix": corr_matrix}
    except Exception as e:
        logger.error(f"Error calculating correlation matrix for {file_path}: {e}", exc_info=True)
        raise

def get_feature_importance(
    file_path: str,
    target_column: str,
    model_type: str,
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    지정된 데이터와 모델 유형을 사용하여 특성 중요도를 계산합니다.
    어떤 변수가 타겟 변수를 예측하는 데 가장 큰 영향을 미치는지 파악하는 데 도움을 줍니다.
    """
    logger.info(f"Calculating feature importance for {file_path} with target {target_column} and model type {model_type}")
    try:
        df = pd.read_parquet(file_path)
        
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame.")

        if features:
            X = df[features]
        else:
            X = df.drop(columns=[target_column])
        y = df[target_column]

        if model_type == "Classification":
            model = RandomForestClassifier(random_state=42)
        elif model_type == "Regression":
            model = RandomForestRegressor(random_state=42)
        else:
            raise ValueError(f"Unsupported model type for feature importance: {model_type}. Only Classification and Regression are supported.")

        # Train a temporary model for importance calculation
        model.fit(X, y)

        # Use permutation importance for robustness
        result = permutation_importance(model, X, y, n_repeats=10, random_state=42, n_jobs=-1)
        sorted_idx = result.importances_mean.argsort()

        feature_importance = {
            X.columns[i]: result.importances_mean[i] for i in sorted_idx
        }
        logger.info(f"Feature importance calculated for {file_path}")
        return {"feature_importance": feature_importance}
    except Exception as e:
        logger.error(f"Error calculating feature importance for {file_path}: {e}", exc_info=True)
        raise