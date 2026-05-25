"""Agent 执行结果 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentResultCreate(BaseModel):
    project_id: int
    agent_role: str = Field(description="Agent 角色: planner/architect/programmer/qa")
    task: str = Field(description="执行的任务描述")
    result: str = Field(description="Agent 执行结果")
    status: str = Field(default="done", description="执行状态: done/error")
    execution_order: int = Field(description="执行顺序")
    workflow_id: str | None = Field(default=None, description="工作流 ID，用于关联同一轮执行")


class AgentResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    agent_role: str
    task: str
    result: str
    status: str
    execution_order: int
    workflow_id: str | None
    created_at: datetime
