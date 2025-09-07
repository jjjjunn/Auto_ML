from fastapi import APIRouter
from tasks import get_task_status, cancel_task
from typing import Dict, Any

router = APIRouter()

@router.get("/status/{task_id}")
async def get_task_status_endpoint(task_id: str) -> Dict[str, Any]:
    """태스크 상태 조회"""
    return get_task_status(task_id)

@router.post("/cancel/{task_id}")
async def cancel_task_endpoint(task_id: str) -> Dict[str, bool]:
    """태스크 취소"""
    success = cancel_task(task_id)
    return {"success": success}