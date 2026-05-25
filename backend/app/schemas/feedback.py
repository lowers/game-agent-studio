"""反馈 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    task_id: int
    content: str
    type: str  # bug / suggestion / praise
    attachment: dict | None = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    content: str
    type: str
    attachment: dict | None
    created_at: datetime
