"""项目 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    auto_start_workflow: bool = False  # 🔴 新增：创建后自动启动多专家工作流


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    complexity: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    complexity: str
    owner_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListOut(BaseModel):
    """分页项目列表响应。🔴 P2 修复"""

    items: list[ProjectOut]
    total: int
    page: int
    page_size: int
    total_pages: int
