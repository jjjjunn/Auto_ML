import pandas as pd
import os
import joblib # For saving/loading models
from utils.logger import logger
from typing import Dict, Any, Optional, List
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, silhouette_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans

# Directory to save trained models
MODELS_DIR = "trained_models"
os.makedirs(MODELS_DIR, exist_ok=True)

def train_model(
    file_path: str,
    target_column: str,
    model_type: str,
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    업로드된 데이터를 사용하여 지정된 머신러닝 모델을 학습시킵니다.
    사용자가 선택한 데이터와 모델 유형에 따라 적절한 모델을 선택하고 훈련합니다.

    - **file_path:** 학습에 사용할 데이터 파일의 경로.
    - **target_column:** 예측하고자 하는 타겟 변수의 이름.
    - **model_type:** 학습할 모델의 유형 (예: "Classification", "Regression", "Clustering").
    - **features:** 모델 학습에 사용할 특성(독립 변수) 목록. 지정하지 않으면 타겟을 제외한 모든 컬럼 사용.
    """
    logger.info(f"Starting model training for {file_path} with target {target_column} and model type {model_type}")
    try:
        df = pd.read_parquet(file_path)

        if features:
            X = df[features]
        else:
            X = df.drop(columns=[target_column])

        if model_type in ["Classification", "Regression"]:
            y = df[target_column]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            if model_type == "Classification":
                model = RandomForestClassifier(random_state=42)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                metrics = {"accuracy": accuracy_score(y_test, y_pred)}
                explanation = "분류 모델이 성공적으로 학습되었습니다. 정확도는 모델이 올바르게 예측한 비율을 나타냅니다."
            elif model_type == "Regression":
                model = RandomForestRegressor(random_state=42)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                metrics = {"mse": mean_squared_error(y_test, y_pred)}
                explanation = "회귀 모델이 성공적으로 학습되었습니다. MSE(평균 제곱 오차)는 예측 값과 실제 값의 차이를 나타냅니다."
        elif model_type == "Clustering":
            model = KMeans(n_clusters=3, random_state=42, n_init=10) # Example: 3 clusters
            model.fit(X)
            labels = model.labels_
            metrics = {"silhouette_score": silhouette_score(X, labels)}
            explanation = "군집 분석 모델이 성공적으로 학습되었습니다. 실루엣 점수는 군집이 얼마나 잘 분리되었는지 나타냅니다."
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        model_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_{model_type}_model.joblib"
        model_save_path = os.path.join(MODELS_DIR, model_filename)
        joblib.dump(model, model_save_path)
        logger.info(f"Model saved to {model_save_path}")

        return {
            "message": f"{model_type} 모델 학습이 성공적으로 완료되었습니다.",
            "model_path": model_save_path,
            "metrics": metrics,
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error during model training for {file_path}: {e}", exc_info=True)
        raise

def load_model(model_path: str):
    """
    저장된 머신러닝 모델을 로드합니다.
    """
    logger.info(f"Loading model from {model_path}")
    try:
        model = joblib.load(model_path)
        logger.info(f"Model loaded from {model_path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}", exc_info=True)
        raise


def predict_with_model(
    model_path: str,
    data_to_predict: pd.DataFrame
) -> List[Any]:
    """
    저장된 모델을 로드하여 새로운 데이터에 대한 예측을 수행합니다.
    """
    logger.info(f"Starting prediction with model from {model_path}")
    try:
        model = load_model(model_path)
        predictions = model.predict(data_to_predict)
        logger.info(f"Prediction completed for {len(data_to_predict)} samples.")
        return predictions.tolist()
    except Exception as e:
        logger.error(f"Error during prediction with model from {model_path}: {e}", exc_info=True)
        raise