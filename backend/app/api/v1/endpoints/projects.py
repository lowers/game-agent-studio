"""项目 CRUD 端点。"""
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_current_user
from app.api.v1.endpoints.websocket import broadcast
from app.database import get_db
from app.models.module import Module
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectListOut, ProjectOut, ProjectUpdate
from app.schemas.task import TaskOut

router = APIRouter()


async def _check_project_owner(project: Project, user: User) -> None:
    """🔴 P0 安全修复：校验项目归属。仅所有者或管理员可修改/删除。"""
    if project.owner_id is not None and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")


@router.get("/", response_model=ProjectListOut)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """列出项目（可选认证）。已登录用户仅看到自己的项目，未登录看到全部。

    🔴 P2 修复：返回分页元数据（total / page / page_size / total_pages）。
    """
    # 基础查询（不含分页）
    base_query = select(Project).order_by(Project.created_at.desc())

    # 🔴 P0 安全修复：已认证用户只看自己的项目
    if user:
        base_query = base_query.where(Project.owner_id == user.id)

    # 获取总数：用 count() 子查询
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar()

    # 分页数据
    paged_query = base_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(paged_query)
    projects = result.scalars().all()

    return ProjectListOut(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.post("/")
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """创建项目（需认证）。自动绑定当前用户为所有者。

    🔴 新增：支持 auto_start_workflow 参数，创建后自动启动多专家工作流。
    """
    # 🔴 P0 安全修复：创建时自动绑定 owner_id
    project_data = body.model_dump()
    auto_start_wf = project_data.pop('auto_start_workflow', False)
    project = Project(**project_data, owner_id=user.id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    out = ProjectOut.model_validate(project)

    # 🔴 广播项目创建事件，前端可据此跳转到工作台并自动启动工作流
    broadcast_data = out.model_dump()
    broadcast_data['auto_start_workflow'] = auto_start_wf
    await broadcast(project.id, {"type": "project_created", "data": broadcast_data})
    return out


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """获取项目详情（可选认证）。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    # 🔴 P0 安全修复：私有项目仅所有者可查看
    if project.owner_id is not None and user is None:
        raise HTTPException(status_code=401, detail="需要登录查看此项目")
    if project.owner_id is not None and user and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看此项目")
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """更新项目（需认证 + 所有者校验）。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    # 🔴 P0 安全修复：校验归属
    await _check_project_owner(project, user)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await db.flush()
    await db.refresh(project)
    out = ProjectOut.model_validate(project)
    await broadcast(project_id, {"type": "project_updated", "data": out.model_dump()})
    return out


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """删除项目（需认证 + 所有者校验）。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    # 🔴 P0 安全修复：校验归属
    await _check_project_owner(project, user)
    await db.delete(project)
    await broadcast(project_id, {"type": "project_deleted", "data": {"id": project_id}})
    return {"detail": "已删除项目"}


class TaskListOut(BaseModel):
    """任务列表响应。"""
    items: list[TaskOut]
    total: int


@router.get("/{project_id}/tasks", response_model=TaskListOut)
async def get_project_tasks(
    project_id: int,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """获取项目下的任务（可选认证）。"""
    # 🔴 P0 安全修复：先检查项目可见性
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.owner_id is not None and user is None:
        raise HTTPException(status_code=401, detail="需要登录查看此项目")
    if project.owner_id is not None and user and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看此项目")

    query = (
        select(Task)
        .join(Module, Task.module_id == Module.id)
        .where(Module.project_id == project_id)
    )
    if status:
        query = query.where(Task.status == status)
    query = query.order_by(Task.priority.desc(), Task.id)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return TaskListOut(items=[TaskOut.model_validate(t) for t in tasks], total=len(tasks))
