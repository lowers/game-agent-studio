"""
异步数据库引擎 & 会话工厂。
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import settings

# SQLite 配置：增加超时和连接池设置
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,  # 数据库锁定等待时间
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    poolclass=StaticPool,  # SQLite 使用单连接池
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
