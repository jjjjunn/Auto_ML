from sqlalchemy.orm import Session
from database.models import ActivityLog
from utils.logger import logger
from typing import Optional

class UserLogService:
    """
    사용자 활동 로그를 데이터베이스에 기록하고 조회하는 서비스입니다.
    """
    def __init__(self):
        logger.info("UserLogService initialized.")

    def record_activity(
        self,
        db: Session,
        user_id: Optional[int],
        activity_type: str,
        description: str
    ):
        """
        사용자 활동을 ActivityLog 테이블에 기록합니다.
        """
        try:
            log_entry = ActivityLog(
                user_id=user_id,
                activity_type=activity_type,
                description=description
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.info(f"Activity recorded: User {user_id}, Type: {activity_type}, Desc: {description[:50]}")
            return log_entry
        except Exception as e:
            logger.error(f"Failed to record activity for user {user_id}: {e}", exc_info=True)
            db.rollback()
            raise

    def get_user_activities(
        self,
        db: Session,
        user_id: Optional[int] = None,
        activity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        사용자 활동 로그를 조회합니다.
        """
        query = db.query(ActivityLog)
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)
        
        logs = query.order_by(ActivityLog.timestamp.desc()).offset(offset).limit(limit).all()
        logger.info(f"Retrieved {len(logs)} activity logs for user {user_id if user_id else 'all'}.")
        return logs
