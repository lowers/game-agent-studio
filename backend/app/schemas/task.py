"""任务 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    module_id: int
    name: str
    status: str = "todo"
    assigned_agent: str | None = None
    priority: int = 0
    dependencies: list[int] | None = []


class TaskUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    assigned_agent: str | None = None
    priority: int | None = None
    dependencies: list[int] | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    name: str
    status: str
    assigned_agent: str | None
    priority: int
    dependencies: list[int] | None
    created_at: datetime
