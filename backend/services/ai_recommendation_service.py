import pandas as pd
from utils.logger import logger
from typing import Dict, Any, List, Optional

def analyze_target_variable(series: pd.Series) -> str:
    """
    타겟 변수의 특성을 분석하여 모델 추천에 활용합니다.
    - 연속형 데이터 (회귀): 숫자로 이루어져 있고, 고유한 값의 개수가 많습니다.
    - 범주형 데이터 (분류): 고유한 값의 개수가 적고, 특정 카테고리를 나타냅니다.
    """
    if pd.api.types.is_numeric_dtype(series):
        # Heuristic for continuous vs. discrete numeric
        if series.nunique() > 0.05 * len(series) and len(series) > 20: # More than 5% unique values, and enough data points
            return "continuous" # Likely regression
        else:
            return "categorical" # Could be classification (e.g., 0/1, ratings)
    else:
        return "categorical" # Non-numeric, likely classification

def recommend_model_type(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    업로드된 CSV 데이터를 분석하여 적합한 머신러닝 모델 유형을 추천합니다.
    이 기능은 머신러닝에 익숙하지 않은 사용자도 데이터에 맞는 모델을 쉽게 선택할 수 있도록 돕습니다.

    - **분류 (Classification):** 타겟 변수가 '예/아니오', 'A/B/C'와 같이 정해진 범주 중 하나인 경우.
      예: 스팸 메일 분류, 질병 진단.
    - **회귀 (Regression):** 타겟 변수가 '집값', '온도'와 같이 연속적인 숫자 값인 경우.
      예: 주택 가격 예측, 판매량 예측.
    - **군집 분석 (Clustering):** 타겟 변수가 없고, 데이터 내의 유사한 그룹을 찾는 경우.
      예: 고객 세분화, 이미지 분할.
    - **추천 시스템 (Recommendation):** 사용자에게 관심 있을 만한 항목을 추천하는 경우.
      예: 영화 추천, 상품 추천.
    - **시계열 예측 (Time Series Forecasting):** 시간의 흐름에 따른 데이터의 변화를 예측하는 경우.
      예: 주가 예측, 날씨 예측.
    """
    logger.info(f"Starting model type recommendation for target: {target_column}")

    recommendations = {
        "model_types": [],
        "explanation": ""
    }

    if target_column and target_column in df.columns:
        target_series = df[target_column]
        target_type = analyze_target_variable(target_series)

        if target_type == "categorical":
            recommendations["model_types"].append("Classification")
            recommendations["explanation"] += (
                f"선택하신 '{target_column}' 변수는 범주형 데이터(예: '예/아니오', 'A/B/C')로 보입니다. "
                "따라서 **분류(Classification)** 모델이 가장 적합할 것으로 예상됩니다. "
                "분류 모델은 데이터를 미리 정의된 카테고리 중 하나로 예측하는 데 사용됩니다."
            )
        elif target_type == "continuous":
            recommendations["model_types"].append("Regression")
            recommendations["explanation"] += (
                f"선택하신 '{target_column}' 변수는 연속적인 숫자 데이터(예: '가격', '온도')로 보입니다. "
                "따라서 **회귀(Regression)** 모델이 가장 적합할 것으로 예상됩니다. "
                "회귀 모델은 연속적인 숫자 값을 예측하는 데 사용됩니다."
            )
        else:
            recommendations["explanation"] += "타겟 변수 분석에 어려움이 있어 일반적인 모델 유형을 추천합니다."
    else:
        recommendations["explanation"] += "타겟 변수가 지정되지 않았거나 데이터에 없습니다. "
        recommendations["explanation"] += "이 경우, 데이터 내의 숨겨진 패턴을 찾는 **군집 분석(Clustering)**이나, "
        recommendations["explanation"] += "사용자 행동 기반의 **추천 시스템(Recommendation)**을 고려할 수 있습니다."
        recommendations["model_types"].append("Clustering")
        recommendations["model_types"].append("Recommendation")

    # Always suggest time series if a date column is detected (simple heuristic)
    date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    if date_columns:
        recommendations["model_types"].append("Time Series Forecasting")
        recommendations["explanation"] += (
            f"\n데이터에 날짜/시간 정보({', '.join(date_columns)})가 포함되어 있어, "
            "시간의 흐름에 따른 패턴을 예측하는 **시계열 예측(Time Series Forecasting)** 모델도 고려할 수 있습니다."
        )

    if not recommendations["model_types"]:
        recommendations["model_types"].append("General Purpose")
        recommendations["explanation"] = "데이터 분석을 위한 일반적인 모델 유형을 추천합니다."

    logger.info(f"Model recommendation completed: {recommendations['model_types']}")
    return recommendations