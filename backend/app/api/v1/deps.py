"""认证依赖注入 — 共享 FastAPI 依赖，供所有端点使用。"""
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """从 Bearer token 解析当前用户。未携带 token 时返回 None（可选认证）。"""
    if credentials is None:
        return None
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        return None
    stmt = select(User).where(User.id == token_data.user_id, User.is_active)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def require_current_user(
    user: User | None = Depends(get_current_user),
) -> User:
    """强制要求认证。未登录返回 401。"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
async def check_project_owner(
    project_id: int,
    user: User,
    db: AsyncSession,
) -> None:
    """Verify authenticated user owns the specified project."""
    from app.models.project import Project
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id is not None and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="No permission to operate on this project")

