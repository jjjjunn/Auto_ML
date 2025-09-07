from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from utils.logger import logger
from database.database import get_db
from services.user_log_service import UserLogService
from models import schemas # Assuming ActivityLog schema will be added here

router = APIRouter()

user_log_service = UserLogService()

@router.get("/activities/", response_model=List[schemas.ActivityLog]) # Assuming schema
async def get_activities(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="조회할 사용자 ID (관리자용)"),
    activity_type: Optional[str] = Query(None, description="조회할 활동 유형"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    사용자 활동 로그를 조회합니다.
    """
    logger.info(f"Received request to get activities for user_id: {user_id}, type: {activity_type}")
    try:
        # In a real app, you'd add authentication/authorization here
        # to ensure only admins can view other users' logs, or users can only view their own.
        
        logs = user_log_service.get_user_activities(
            db=db,
            user_id=user_id,
            activity_type=activity_type,
            limit=limit,
            offset=offset
        )
        logger.info(f"Successfully retrieved {len(logs)} activity logs.")
        return logs
    except Exception as e:
        logger.error(f"Error getting activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"활동 로그 조회 중 오류가 발생했습니다: {e}")
