"""项目表。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="项目名称")
    description: Mapped[str | None] = mapped_column(Text, comment="项目描述")
    status: Mapped[str] = mapped_column(
        String(20), default="draft", comment="状态: draft / active / archived"
    )
    complexity: Mapped[str] = mapped_column(
        String(20), default="medium", comment="复杂度: simple / medium / complex"
    )
    # 🔴 P0 安全修复：资源级授权 — 项目归属用户
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="项目所有者"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关系
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    modules: Mapped[list["Module"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    builds: Mapped[list["Build"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    memories: Mapped[list["AgentMemory"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    agent_results: Mapped[list["AgentResult"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    llm_wiki_entries: Mapped[list["LlmWikiEntry"]] = relationship(
        "LlmWikiEntry", back_populates="project", cascade="all, delete-orphan"
    )
