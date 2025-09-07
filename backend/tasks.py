"""
비동기 작업을 위한 Celery 태스크 정의

이 모듈은 시간이 오래 걸리는 머신러닝 모델 훈련 작업을 비동기로 처리하여
사용자 경험을 향상시킵니다.
"""

from celery import Celery
from celery.result import AsyncResult
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging
import traceback
from typing import Dict, Any

from config import settings
from database.models import MLModel, Dataset
from services.ml_service import MLService
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Celery 앱 초기화
celery_app = Celery(
    "auto_ml_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "tasks.train_model_task": {"queue": "ml_training"},
        "tasks.generate_predictions_task": {"queue": "predictions"},
        "tasks.update_knowledge_base_task": {"queue": "rag_updates"}
    }
)

# 데이터베이스 세션 생성
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task(bind=True, name="tasks.train_model_task")
async def train_model_task(self, model_id: int) -> Dict[str, Any]:
    """
    머신러닝 모델 비동기 훈련 작업
    
    이 작업은 시간이 오래 걸리는 모델 훈련을 백그라운드에서 수행하며,
    진행 상황을 실시간으로 업데이트합니다.
    
    Args:
        model_id: 훈련할 모델의 데이터베이스 ID
        
    Returns:
        훈련 결과 딕셔너리 (모델 경로, 성능 지표 등)
    """
    db = SessionLocal()
    ml_service = MLService()
    
    try:
        # 모델과 데이터셋 정보 로드
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ValueError(f"모델 ID {model_id}를 찾을 수 없습니다")
        
        dataset = db.query(Dataset).filter(Dataset.id == model.dataset_id).first()
        if not dataset:
            raise ValueError(f"데이터셋 ID {model.dataset_id}를 찾을 수 없습니다")
        
        logger.info(f"🚀 모델 훈련 시작: {model.name} (ID: {model_id})")
        
        # 진행 상황 업데이트 (10%)
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "데이터 로드 및 전처리 중..."}
        )
        
        # 모델 훈련 실행
        training_result = await ml_service.train_model(model, dataset)
        
        # 진행 상황 업데이트 (70%)
        self.update_state(
            state="PROGRESS", 
            meta={"progress": 70, "message": "모델 훈련 완료, 성능 평가 중..."}
        )
        
        # 모델 정보 업데이트
        model.model_path = training_result["model_path"]
        model.performance_metrics = training_result["performance_metrics"]
        model.algorithm = training_result["algorithm_used"]
        model.training_status = "completed"
        model.training_log = training_result["training_log"]
        
        db.commit()
        
        # 진행 상황 업데이트 (90%)
        self.update_state(
            state="PROGRESS",
            meta={"progress": 90, "message": "지식베이스 업데이트 중..."}
        )
        
        # RAG 지식베이스에 모델 정보 추가
        try:
            rag_service = RAGService()
            await rag_service.add_model_knowledge(model)
        except Exception as e:
            logger.warning(f"지식베이스 업데이트 실패 (계속 진행): {e}")
        
        logger.info(f"✅ 모델 훈련 완료: {model.name}")
        
        return {
            "status": "completed",
            "model_id": model_id,
            "model_path": training_result["model_path"],
            "performance_metrics": training_result["performance_metrics"],
            "message": f"'{model.name}' 모델 훈련이 성공적으로 완료되었습니다!"
        }
        
    except Exception as e:
        # 에러 발생시 모델 상태 업데이트
        error_msg = f"모델 훈련 실패: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        
        if 'model' in locals():
            model.training_status = "failed"
            model.training_log = error_msg
            db.commit()
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "traceback": traceback.format_exc()}
        )
        
        raise Exception(error_msg)
        
    finally:
        db.close()

@celery_app.task(bind=True, name="tasks.generate_predictions_task")
async def generate_predictions_task(self, model_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    모델 예측 비동기 작업
    
    대용량 예측 요청을 백그라운드에서 처리합니다.
    
    Args:
        model_id: 예측에 사용할 모델 ID
        input_data: 예측할 데이터
        
    Returns:
        예측 결과 딕셔너리
    """
    db = SessionLocal()
    ml_service = MLService()
    
    try:
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ValueError(f"모델 ID {model_id}를 찾을 수 없습니다")
        
        logger.info(f"🔮 예측 작업 시작: 모델 {model.name}")
        
        # 진행 상황 업데이트
        self.update_state(
            state="PROGRESS",
            meta={"progress": 30, "message": "예측 수행 중..."}
        )
        
        # 예측 수행
        prediction_result = await ml_service.predict(model, input_data)
        
        logger.info(f"✅ 예측 완료: 모델 {model.name}")
        
        return {
            "status": "completed",
            "prediction": prediction_result.prediction,
            "confidence": prediction_result.confidence,
            "model_info": prediction_result.model_info
        }
        
    except Exception as e:
        error_msg = f"예측 실패: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg}
        )
        
        raise Exception(error_msg)
        
    finally:
        db.close()

# 유틸리티 함수들
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    태스크 상태 조회
    
    Args:
        task_id: Celery 태스크 ID
        
    Returns:
        태스크 상태 정보
    """
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state == "PENDING":
            return {
                "status": "pending",
                "message": "작업이 대기 중입니다"
            }
        elif result.state == "PROGRESS":
            return {
                "status": "progress",
                "progress": result.result.get("progress", 0),
                "message": result.result.get("message", "진행 중...")
            }
        elif result.state == "SUCCESS":
            return {
                "status": "success",
                "result": result.result
            }
        elif result.state == "FAILURE":
            return {
                "status": "failure",
                "error": str(result.result)
            }
        else:
            return {
                "status": result.state,
                "info": result.result
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": f"태스크 상태 조회 실패: {str(e)}"
        }

def cancel_task(task_id: str) -> bool:
    """
    실행 중인 태스크 취소
    
    Args:
        task_id: 취소할 태스크 ID
        
    Returns:
        취소 성공 여부
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"태스크 취소 완료: {task_id}")
        return True
    except Exception as e:
        logger.error(f"태스크 취소 실패: {e}")
        return False