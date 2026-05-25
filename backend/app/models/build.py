"""构建表 — 记录项目的构建历史。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), comment="所属项目 ID"
    )
    version: Mapped[str | None] = mapped_column(String(20), comment="版本号")
    build_url: Mapped[str | None] = mapped_column(String(255), comment="构建产物 URL")
    platform: Mapped[str] = mapped_column(
        String(20), comment="目标平台: web / unity / unreal"
    )
    status: Mapped[str] = mapped_column(
        String(20), comment="构建状态: pending / success / failed"
    )
    log: Mapped[str | None] = mapped_column(Text, comment="构建日志")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    project: Mapped["Project"] = relationship(back_populates="builds")
