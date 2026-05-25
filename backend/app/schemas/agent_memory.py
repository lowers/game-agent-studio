"""Agent 记忆 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentMemoryCreate(BaseModel):
    project_id: int
    trigger_keywords: list[str]
    positive_pattern: str | None = None
    negative_pattern: str | None = None
    confidence: float = 0.5


class AgentMemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    trigger_keywords: list[str] | None
    positive_pattern: str | None
    negative_pattern: str | None
    confidence: float
    created_at: datetime
    last_used_at: datetime | None
    usage_count: int
