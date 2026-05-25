"""任务端点 — 完整 CRUD + WebSocket 广播。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import check_project_owner, get_current_user, require_current_user
from app.api.v1.endpoints.websocket import broadcast
from app.database import get_db
from app.models.module import Module
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate

router = APIRouter()


async def _get_project_id_for_task(db: AsyncSession, task: Task) -> int | None:
    result = await db.execute(select(Module.project_id).where(Module.id == task.module_id))
    row = result.scalar_one_or_none()
    return row


@router.post("/", response_model=TaskOut)
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """创建任务（需认证）。"""
    res = await db.execute(select(Module.project_id).where(Module.id == body.module_id))
    pid = res.scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=404, detail="模块不存在")
    await check_project_owner(pid, user, db)
    task = Task(**body.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    out = TaskOut.model_validate(task)
    project_id = await _get_project_id_for_task(db, task)
    if project_id:
        await broadcast(project_id, {"type": "task_created", "data": out.model_dump()})
    return out


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """获取任务详情（可选认证）。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """更新任务（需认证）。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    pid = await _get_project_id_for_task(db, task)
    if pid:
        await check_project_owner(pid, user, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.flush()
    await db.refresh(task)
    out = TaskOut.model_validate(task)
    project_id = await _get_project_id_for_task(db, task)
    if project_id:
        await broadcast(project_id, {"type": "task_updated", "data": out.model_dump()})
    return out


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """删除任务（需认证）。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    project_id = await _get_project_id_for_task(db, task)
    if project_id:
        await check_project_owner(project_id, user, db)
    await db.delete(task)
    if project_id:
        await broadcast(project_id, {"type": "task_deleted", "data": {"id": task_id}})
    return {"detail": "已删除"}


@router.get("/{task_id}/dependencies")
async def get_task_dependencies(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """获取任务依赖（可选认证）。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    dep_ids = task.dependencies or []
    if not dep_ids:
        return []
    dep_result = await db.execute(select(Task).where(Task.id.in_(dep_ids)))
    deps = dep_result.scalars().all()
    return [TaskOut.model_validate(d) for d in deps]
