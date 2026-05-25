"""
应用配置 — 使用 pydantic-settings 从环境变量或 .env 文件加载。
"""
from pathlib import Path
from typing import Sequence

from pydantic_settings import BaseSettings


def _get_default_db_path() -> str:
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / "game_studio.db"
    return f"sqlite+aiosqlite:///{db_path}"


class Settings(BaseSettings):
    DATABASE_URL: str = _get_default_db_path()

    # LLM 提供商选择：deepseek | sensenova
    LLM_PROVIDER: str = "deepseek"

    # --- DeepSeek 配置（默认） ---
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"

    # --- SenseNova 配置 ---
    SENSENOVA_API_KEY: str = ""
    SENSENOVA_BASE_URL: str = "https://token.sensenova.cn/v1"
    SENSENOVA_MODEL: str = "sensenova-6.7-flash-lite"

    # --- 运行时 LLM 参数（根据提供商自动选择） ---
    @property
    def active_api_key(self) -> str:
        if self.LLM_PROVIDER == "sensenova":
            return self.SENSENOVA_API_KEY or self.LLM_API_KEY
        return self.LLM_API_KEY

    @property
    def active_base_url(self) -> str:
        if self.LLM_PROVIDER == "sensenova":
            return self.SENSENOVA_BASE_URL
        return self.LLM_BASE_URL

    @property
    def active_model(self) -> str:
        if self.LLM_PROVIDER == "sensenova":
            return self.SENSENOVA_MODEL
        return self.LLM_MODEL

    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 8192  # 增加到 8K，完整游戏代码需要更多 token

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    API_PREFIX: str = "/api"
    DEBUG: bool = False  # P1: 生产环境默认关闭调试模式
    CORS_ALLOWED_ORIGINS: Sequence[str] = []

    # Redis 配置（可选 — 用于生产环境状态持久化）
    REDIS_URL: str = ""  # 例如: redis://localhost:6379/0

    # JWT 认证配置（独立于 LLM_API_KEY，生产环境务必设置！）
    # ⚠️ 默认值仅用于开发，启动时校验 — 见 app/config/__init__.py
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 默认 7 天

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# 🔴 P0 安全修复：JWT_SECRET 默认值校验
# 生产环境（DEBUG=False）若未设置 JWT_SECRET 环境变量，应用拒绝启动
if not settings.DEBUG and settings.JWT_SECRET == "change-me-in-production":
    raise RuntimeError(
        "🔴 CRITICAL: JWT_SECRET is still the default value 'change-me-in-production'. "
        "Set the JWT_SECRET environment variable before running in production!"
    )
if settings.JWT_SECRET == "change-me-in-production":
    import warnings
    warnings.warn(
        "⚠️ JWT_SECRET is using the default value. "
        "Set JWT_SECRET environment variable for production use.",
        stacklevel=2,
    )
