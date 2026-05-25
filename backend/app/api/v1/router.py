"""
v1 路由汇总 — 注册所有子路由。
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    auth,
    builds,
    conversation,
    feedbacks,
    health,
    llm_config,
    modules,
    projects,
    tasks,
    websocket,
    wiki,
    workflow,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(modules.router, prefix="/modules", tags=["modules"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(builds.router, prefix="/projects", tags=["builds"])
api_router.include_router(feedbacks.router, prefix="/feedbacks", tags=["feedbacks"])
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(workflow.router, prefix="/workflows", tags=["多专家工作流"])
api_router.include_router(wiki.router, prefix="/wiki", tags=["wiki"])
api_router.include_router(llm_config.router, tags=["llm"])
