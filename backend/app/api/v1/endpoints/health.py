"""
Health check endpoint — 返回系统健康状态和 LLM 配置状态
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """检查系统健康状态和 LLM 配置。"""
    from app.config.settings import settings

    llm_configured = bool(settings.SENSENOVA_API_KEY or settings.LLM_API_KEY)

    return {
        "status": "ok",
        "llm_configured": llm_configured,
        "version": "2.0",
    }
