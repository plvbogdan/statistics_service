from fastapi import APIRouter
from typing import Optional
from tasks import compute_device_analytics, compute_user_analytics
from schemas import TaskResponse, TaskResult
from celery.result import AsyncResult
from tasks import celery_app

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/device/{device_id}", response_model=TaskResponse)
async def analytics_by_device(
    device_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
):
    task = compute_device_analytics.delay(
        device_id=device_id,
        from_ts=from_ts,
        to_ts=to_ts
    )
    return TaskResponse(task_id=task.id, status="processing")


@router.post("/user/{user_id}", response_model=TaskResponse)
async def analytics_by_user(
    user_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
):
    task = compute_user_analytics.delay(
        user_id=user_id,
        from_ts=from_ts,
        to_ts=to_ts
    )
    return TaskResponse(task_id=task.id, status="processing")


@router.get("/result/{task_id}", response_model=TaskResult)
async def get_analytics_result(task_id: str):
   
    
    task = AsyncResult(task_id, app=celery_app)
    
    if task.failed():
        return TaskResult(task_id=task_id, status="failed", error=str(task.info))
    
    if task.ready():
        return TaskResult(task_id=task_id, status="completed", result=task.result)
    
    return TaskResult(task_id=task_id, status="pending")