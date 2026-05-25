"""Agent 记忆表 — 存储正负反馈模式，辅助 RAG 检索。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), comment="所属项目 ID"
    )
    trigger_keywords: Mapped[list | None] = mapped_column(
        JSON, default=None, nullable=True, comment="触发关键词，如 ['跳跃手感', '重力']"
    )
    positive_pattern: Mapped[str | None] = mapped_column(
        Text, comment="正向模式描述"
    )
    negative_pattern: Mapped[str | None] = mapped_column(
        Text, comment="负向模式描述"
    )
    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, comment="置信度 0-1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最近使用时间"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="使用次数"
    )

    project: Mapped["Project"] = relationship(back_populates="memories")
