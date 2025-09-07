from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from utils.logger import logger
from services.rag_service import RAGService

router = APIRouter()

# Initialize RAGService
rag_service = RAGService()

class ChatRequest(BaseModel):
    user_query: str
    dataframe_path: str
    model_path: Optional[str] = None
    trained_model_info: Optional[Dict[str, Any]] = None

@router.post("/chat/")
async def chat_with_model(request: ChatRequest):
    """
    CSV 파일 데이터와 훈련된 모델을 기반으로 챗봇과 대화합니다.
    """
    logger.info(f"Received chat request for query: '{request.user_query}'")
    try:
        response = await rag_service.get_rag_response(
            user_query=request.user_query,
            dataframe_path=request.dataframe_path,
            model_path=request.model_path,
            trained_model_info=request.trained_model_info
        )
        logger.info("Chat response generated.")
        return {"response": response}
    except Exception as e:
        logger.error(f"Error during chat API call for query '{request.user_query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {e}")