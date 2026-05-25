"""反馈表 — 用户对任务的反馈。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), comment="关联任务 ID"
    )
    content: Mapped[str] = mapped_column(Text, comment="反馈内容")
    type: Mapped[str] = mapped_column(
        String(20), comment="反馈类型: bug / suggestion / praise"
    )
    attachment: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="附件：截图、日志等"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    task: Mapped["Task"] = relationship(back_populates="feedbacks")
