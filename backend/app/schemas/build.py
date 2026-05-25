"""构建 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BuildCreate(BaseModel):
    platform: str = "web"  # web / unity / unreal


class BuildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    version: str | None
    build_url: str | None
    platform: str
    status: str
    log: str | None
    created_at: datetime
