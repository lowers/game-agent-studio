"""模块 Schema。"""
from pydantic import BaseModel, ConfigDict


class ModuleCreate(BaseModel):
    project_id: int
    name: str
    description: str | None = None
    order: int = 0


class ModuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    order: int | None = None


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str | None
    order: int
