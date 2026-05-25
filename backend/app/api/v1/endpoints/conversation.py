"""对话需求采集端点 — 接入 ChatService。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.game_design_doc import GameDesignDoc

router = APIRouter()

MAX_MESSAGE_LENGTH = 2000
MAX_SESSION_MESSAGES = 10


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    session_id: str = Field(default="default", min_length=1, max_length=64)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")
        return stripped


class EvaluationInfo(BaseModel):
    """可行性评估信息"""
    complexity_score: int
    complexity_label: str
    risk_level: str
    is_feasible: bool
    issues: list[dict] = []
    warnings: list[str] = []
    suggestions: list[str] = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    state: str | None = None
    inquiry_topic: str | None = None
    evaluation: EvaluationInfo | None = None
    design_doc: dict | None = None
    is_complete: bool = False


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: User | None = Depends(get_current_user),
):
    """对话需求采集（可选认证）。"""
    from app.services.chat_service import chat_service

    result = await chat_service.chat(body.message, body.session_id)

    return ChatResponse(
        reply=result.get("response", ""),
        session_id=result.get("session_id", body.session_id),
        state=result.get("state"),
        inquiry_topic=result.get("inquiry_topic"),
        evaluation=EvaluationInfo(**result["evaluation"]) if result.get("evaluation") else None,
        design_doc=result.get("design_doc"),
        is_complete=result.get("is_complete", False),
    )


_fallback_sessions: dict[str, list[str]] = {}


async def _fallback_chat(body: ChatRequest) -> ChatResponse:
    session = _fallback_sessions.setdefault(body.session_id, [])

    if len(session) >= MAX_SESSION_MESSAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Session has reached maximum message limit ({MAX_SESSION_MESSAGES})",
        )

    session.append(body.message)

    if len(session) == 1:
        reply = (
            "你好！请描述一下你想做的游戏。比如：\n"
            "- 游戏类型（平台跳跃、RPG、射击等）\n"
            "- 主角是谁？\n"
            "- 核心玩法是什么？"
        )
    elif len(session) == 2:
        reply = "好的，能再描述一下游戏的核心玩法和胜利条件吗？"
    elif len(session) == 3:
        reply = "明白了！敌人或收集物有哪些？有什么特殊机制吗？"
    else:
        reply = "感谢你的描述！我已经收集到足够的信息，正在生成游戏设计文档..."
        doc = GameDesignDoc(
            game_type="未指定",
            protagonist="未指定",
            core_gameplay=" ".join(session),
            enemies_collectibles="未指定",
            win_condition="未指定",
        )
        return ChatResponse(
            reply=reply,
            session_id=body.session_id,
            design_doc=doc.model_dump(),
        )

    return ChatResponse(reply=reply, session_id=body.session_id)
