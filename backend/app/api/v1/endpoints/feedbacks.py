"""反馈端点。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import check_project_owner, get_current_user, require_current_user
from app.database import get_db
from app.models.feedback import Feedback
from app.models.module import Module
from app.models.task import Task
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter()


@router.get("/task/{task_id}")
async def list_feedbacks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """列出任务反馈（可选认证）。"""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.task_id == task_id)
        .order_by(Feedback.created_at.desc())
    )
    feedbacks = result.scalars().all()
    return [FeedbackOut.model_validate(f) for f in feedbacks]


@router.post("/", response_model=FeedbackOut)
async def create_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """创建反馈（需认证）。"""
    result = await db.execute(select(Task).where(Task.id == body.task_id))
    task_db = result.scalar_one_or_none()
    if not task_db:
        raise HTTPException(status_code=404, detail="任务不存在")

    mod_result = await db.execute(select(Module).where(Module.id == task_db.module_id))
    mod = mod_result.scalar_one_or_none()
    if mod is not None:
        await check_project_owner(mod.project_id, user, db)

    feedback = Feedback(**body.model_dump())
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)
    return FeedbackOut.model_validate(feedback)
