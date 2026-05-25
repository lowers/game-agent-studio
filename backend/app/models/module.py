"""模块表 — 项目下的功能模块划分。"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), comment="所属项目 ID"
    )
    name: Mapped[str] = mapped_column(String(100), comment="模块名称")
    description: Mapped[str | None] = mapped_column(Text, comment="模块描述")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序序号")

    project: Mapped["Project"] = relationship(back_populates="modules")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
