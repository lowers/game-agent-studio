"""模块端点 — 项目下的功能模块 CRUD。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import check_project_owner, get_current_user, require_current_user
from app.database import get_db
from app.models.module import Module
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleOut, ModuleUpdate

router = APIRouter()


@router.get("/project/{project_id}")
async def list_modules(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
):
    """列出项目下的模块（可选认证）。"""
    # P2: 添加分页
    result = await db.execute(
        select(Module)
        .where(Module.project_id == project_id)
        .order_by(Module.order)
        .offset(skip)
        .limit(limit)
    )
    modules = result.scalars().all()
    return [ModuleOut.model_validate(m) for m in modules]


@router.post("/", response_model=ModuleOut)
async def create_module(
    body: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """创建模块（需认证）。"""
    await check_project_owner(body.project_id, user, db)
    module = Module(**body.model_dump())
    db.add(module)
    await db.flush()
    await db.refresh(module)
    return ModuleOut.model_validate(module)


@router.get("/{module_id}", response_model=ModuleOut)
async def get_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """获取模块详情（可选认证）。"""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    return ModuleOut.model_validate(module)


@router.patch("/{module_id}", response_model=ModuleOut)
async def update_module(
    module_id: int,
    body: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """更新模块（需认证）。"""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    await check_project_owner(module.project_id, user, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(module, key, value)
    await db.flush()
    await db.refresh(module)
    return ModuleOut.model_validate(module)


@router.delete("/{module_id}")
async def delete_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_current_user),
):
    """删除模块（需认证）。"""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    await check_project_owner(module.project_id, user, db)
    await db.delete(module)
    return {"detail": "已删除"}
