"""
AI 游戏工坊 (Game Agent Studio) — FastAPI 入口
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Sequence

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app.database import Base, engine

logger = logging.getLogger(__name__)


def _get_cors_origins() -> Sequence[str]:
    """根据环境返回合适的 CORS origins。"""
    if settings.DEBUG:
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:63342",  # PyCharm 内置服务器
            "http://localhost:8000",
            "http://localhost:8001",
            "http://localhost:8002",
            "null",  # 允许 file:// 直接打开 HTML
        ]
    allowed = settings.CORS_ALLOWED_ORIGINS
    if not allowed:
        logger.warning("CORS_ALLOWED_ORIGINS not set in production, using localhost only")
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:63342",
            "http://localhost:8080",
            "http://localhost:8000",
            "http://localhost:8001",
            "http://localhost:8002",
            "null",
        ]
    return allowed


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 初始化 StateStore（自动选择 Redis 或 InMemory）
    from app.services.state_store import get_state_store
    get_state_store()
    # 初始化 EventBus → WebSocket 桥接
    from app.services.ws_bridge import init_ws_bridge
    init_ws_bridge()
    yield
    # 优雅关闭：断开 Redis 连接
    from app.services.state_store import _store
    import asyncio
    if _store is not None and hasattr(_store, "_redis") and _store._redis is not None:
        try:
            await asyncio.wait_for(_store._redis.aclose(), timeout=3.0)
            logger.info("RedisStateStore disconnected")
        except asyncio.TimeoutError:
            logger.warning("Redis close timeout, force closing")
    await engine.dispose()


app = FastAPI(
    title="Game Agent Studio API",
    description="AI 游戏工坊 — 让 AI 帮你做游戏",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True if not settings.DEBUG else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# P1: 登录限流中间件
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# P1: 使用共享的 limiter 模块
from app.utils.limiter import login_limiter

limiter = login_limiter  # 保持兼容
app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router, prefix=settings.API_PREFIX)

# WebSocket 端点统一通过 api_router 路由（已在 endpoints/websocket.py 中定义）
# 避免在 main.py 中重复注册，保持代码单一来源


# P1: 限流异常处理
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理，生产环境不泄露敏感信息。"""
    if settings.DEBUG:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

# 静态文件服务：提供游戏构建输出
# 🔴 P0 安全修复：添加 CSP sandbox 响应头，防止 LLM 生成内容执行 JS（存储型 XSS）
_output_dir = Path(__file__).parent.parent / "output"
_output_dir.mkdir(exist_ok=True)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest


class OutputCSPMiddleware(BaseHTTPMiddleware):
    """为 /output/ 路径下的静态文件添加 Content-Security-Policy: sandbox 响应头。

    LLM 生成的 HTML 可能包含 <script> 标签，形成存储型 XSS。
    CSP sandbox 禁止脚本执行、表单提交、弹窗等，同时允许基本展示。
    """

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/output"):
            response.headers["Content-Security-Policy"] = (
                "sandbox allow-scripts 'none' allow-same-origin; "
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'none';"
            )
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response


app.add_middleware(OutputCSPMiddleware)

app.mount("/output", StaticFiles(directory=str(_output_dir)), name="output")
