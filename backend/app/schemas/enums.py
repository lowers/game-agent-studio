"""统一枚举定义 — 避免重复定义和值不一致。"""
from enum import Enum


class AgentStatus(str, Enum):
    """Agent 执行状态 — 统一来源，所有模块通过 `from app.schemas.enums import AgentStatus` 导入。"""
    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_USER = "waiting_user"  # Agent 等待用户确认
    DONE = "done"
    ERROR = "error"
