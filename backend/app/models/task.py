"""任务表。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), comment="所属模块 ID"
    )
    name: Mapped[str] = mapped_column(String(200), comment="任务名称")
    status: Mapped[str] = mapped_column(
        String(20), default="todo", comment="状态: todo / in_progress / review / done"
    )
    assigned_agent: Mapped[str | None] = mapped_column(
        String(50), comment="负责 Agent: planner / architect / programmer / qa"
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级，数值越大越优先")
    dependencies: Mapped[list] = mapped_column(
        JSON, default=list, comment="依赖的任务 ID 列表"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    module: Mapped["Module"] = relationship(back_populates="tasks")
    feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
