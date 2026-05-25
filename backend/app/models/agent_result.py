"""Agent 执行结果表 — 存储 Agent 工作流执行结果。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentResult(Base):
    __tablename__ = "agent_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), comment="所属项目 ID"
    )
    agent_role: Mapped[str] = mapped_column(
        String(20), comment="Agent 角色: planner/architect/programmer/qa"
    )
    task: Mapped[str] = mapped_column(Text, comment="执行的任务描述")
    result: Mapped[str] = mapped_column(Text, comment="Agent 执行结果")
    status: Mapped[str] = mapped_column(
        String(20), default="done", comment="执行状态: done/error"
    )
    execution_order: Mapped[int] = mapped_column(Integer, comment="执行顺序")
    workflow_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="工作流 ID，用于关联同一轮执行"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    project: Mapped["Project"] = relationship(back_populates="agent_results")
