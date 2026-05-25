"""构建端点。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import check_project_owner, get_current_user, require_current_user
from app.database import get_db
from app.models.build import Build
from app.models.project import Project
from app.models.user import User
from app.schemas.build import BuildCreate, BuildOut

router = APIRouter()


@router.get("/{project_id}/builds")
async def list_builds(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """列出项目构建（可选认证）。"""
    result = await db.execute(
        select(Build)
        .where(Build.project_id == project_id)
        .order_by(Build.created_at.desc())
    )
    builds = result.scalars().all()
    return [BuildOut.model_validate(b) for b in builds]


@router.post("/{project_id}/builds", response_model=BuildOut)
async def trigger_build(
    project_id: int,
    body: BuildCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """触发构建（需认证）。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    await check_project_owner(project_id, user, db)

    build = Build(
        project_id=project_id,
        platform=body.platform,
        status="pending",
    )
    db.add(build)
    await db.flush()
    await db.refresh(build)
    return BuildOut.model_validate(build)
