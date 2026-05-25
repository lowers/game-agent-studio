"""用户表 — JWT 认证。"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment="邮箱")
    name: Mapped[str] = mapped_column(String(100), default="", comment="用户名")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="哈希密码")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
