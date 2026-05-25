"""Agent 端点。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.deps import get_current_user, require_current_user
from app.models.user import User
from app.schemas.game_design_doc import GameDesignDoc
from app.services.agents import AGENT_REGISTRY  # P3#23: 移至文件顶部
from app.services.chat_service import chat_service

router = APIRouter()


# === Typed Response Models ===
class AgentOut(BaseModel):
    """Agent 信息输出模型。"""
    id: str
    name: str
    description: str


class AgentListOut(BaseModel):
    """Agent 列表输出模型。"""
    items: list[AgentOut]
    total: int


class PromptUpdateOut(BaseModel):
    """提示词更新响应模型。"""
    detail: str
    agent_id: str
    is_customized: bool  # True 表示当前使用的是自定义提示词


class PromptGetOut(BaseModel):
    """获取提示词响应模型。"""
    agent_id: str
    is_customized: bool
    current_prompt: str  # 当前生效的提示词（自定义或默认）

AGENTS: list[dict[str, str]] = [
    {
        "id": "planner",
        "name": "策划 Agent",
        "description": "负责需求分析、任务拆分、生成游戏设计文档",
    },
    {
        "id": "architect",
        "name": "架构 Agent",
        "description": "负责技术选型、API 设计、系统架构",
    },
    {
        "id": "programmer",
        "name": "程序 Agent",
        "description": "负责代码生成、功能实现",
    },
    {
        "id": "qa",
        "name": "QA Agent",
        "description": "负责测试用例生成、质量检查",
    },
    {
        "id": "security",
        "name": "安全审查 Agent",
        "description": "安全漏洞扫描、代码审计、安全加固",
    },
    {
        "id": "devops",
        "name": "DevOps Agent",
        "description": "构建配置、部署脚本、CI/CD 管道生成",
    }
]


@router.get("/", response_model=AgentListOut)
async def list_agents(user: User | None = Depends(get_current_user)) -> AgentListOut:
    """列出所有 Agent（可选认证，登录后返回更多详情）。"""
    items = [AgentOut(id=a["id"], name=a["name"], description=a["description"]) for a in AGENTS]
    return AgentListOut(items=items, total=len(items))


class PromptUpdate(BaseModel):
    system_prompt: str


@router.put("/{agent_id}/prompt", response_model=PromptUpdateOut)
async def update_agent_prompt(
    agent_id: str,
    body: PromptUpdate,
    user: User = Depends(require_current_user),
) -> PromptUpdateOut:
    """更新 Agent 系统提示词（需认证）。"""
    from app.services.prompt_store import get_prompt_store

    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    prompt_store = get_prompt_store()
    await prompt_store.set_prompt(agent_id, body.system_prompt)

    return PromptUpdateOut(
        detail="已更新系统提示词",
        agent_id=agent_id,
        is_customized=True,
    )


@router.get("/{agent_id}/prompt", response_model=PromptGetOut)
async def get_agent_prompt(
    agent_id: str,
    user: User = Depends(require_current_user),
) -> PromptGetOut:
    """获取 Agent 当前系统提示词（需认证）。"""
    from app.services.prompt_store import get_prompt_store

    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    prompt_store = get_prompt_store()
    custom_prompt = await prompt_store.get_prompt(agent_id)
    agent_class = AGENT_REGISTRY[agent_id]
    default_prompt = agent_class()._get_default_system_prompt()

    return PromptGetOut(
        agent_id=agent_id,
        is_customized=custom_prompt is not None,
        current_prompt=custom_prompt if custom_prompt else default_prompt,
    )


@router.delete("/{agent_id}/prompt", response_model=PromptUpdateOut)
async def delete_agent_prompt(
    agent_id: str,
    user: User = Depends(require_current_user),
) -> PromptUpdateOut:
    """删除 Agent 自定义提示词，恢复默认（需认证）。"""
    from app.services.prompt_store import get_prompt_store

    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    prompt_store = get_prompt_store()
    existed = await prompt_store.delete_prompt(agent_id)

    return PromptUpdateOut(
        detail="已恢复默认提示词" if existed else "该 Agent 没有自定义提示词",
        agent_id=agent_id,
        is_customized=False,
    )


# 旧版工作流相关代码已迁移至 /workflows API
# ⚠️ 以下端点保留向后兼容，仅供过渡期使用


# === Chat Response Models ===
class ChatOut(BaseModel):
    session_id: str
    agent: str
    response: str
    state: str
    project_summary: str | None = None
    design_doc: GameDesignDoc | None = None
    is_complete: bool = False
    evaluation: str | None = None
    conversation_history: list[dict] = []


class ChatDeleteOut(BaseModel):
    status: str
    session_id: str


class ChatHistoryOut(BaseModel):
    session_id: str
    conversation_history: list[dict]
    state: str
    project_summary: str | None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    project_id: Optional[int] = None  # 🔴 P2 修复：用于广播项目隔离


@router.post("/chat", response_model=ChatOut)
async def chat_with_master(
    body: ChatRequest,
    user: User | None = Depends(get_current_user),
) -> ChatOut:
    """与 Master Agent 对话确认需求（可选认证）"""
    # 🔴 P2 修复：传递 project_id 实现广播项目隔离
    result = await chat_service.chat(body.message, body.session_id, body.project_id)

    return ChatOut(
        session_id=result["session_id"],
        agent="master",
        response=result["response"],
        state=result["state"],
        project_summary=result.get("project_summary"),
        design_doc=result.get("design_doc"),
        is_complete=result.get("is_complete", False),
        evaluation=result.get("evaluation"),
        conversation_history=result.get("conversation_history", []),
    )


@router.delete("/chat/{session_id}", response_model=ChatDeleteOut)
async def delete_chat_session(
    session_id: str,
    user: User = Depends(require_current_user),
) -> ChatDeleteOut:
    """删除聊天会话（需认证）"""
    success = await chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return ChatDeleteOut(status="deleted", session_id=session_id)


@router.get("/chat/{session_id}", response_model=ChatHistoryOut)
async def get_chat_history(
    session_id: str,
    user: User | None = Depends(get_current_user),
) -> ChatHistoryOut:
    """获取聊天历史（可选认证）"""
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return ChatHistoryOut(
        session_id=session.session_id,
        conversation_history=session.conversation_history,
        state=session.state,
        project_summary=session.project_summary,
    )
