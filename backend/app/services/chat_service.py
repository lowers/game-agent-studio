"""统一聊天服务 — 对外提供 chat() 单入口。

- ChatService 对外提供统一 chat() 接口
- 内部使用 ProactiveConversationService 做状态机+问询
- 通过 EventBus 广播消息（替代直接 WebSocket 调用）
- 会话状态通过 StateStore 管理（支持持久化切换）
"""
import logging
import uuid
from typing import Optional

from app.services.event_bus import Event, event_bus
from app.services.state_store import get_state_store

logger = logging.getLogger(__name__)

# 会话默认 TTL：2 小时
SESSION_TTL = 7200

# StateStore key 前缀
SESSION_PREFIX = "chat_session:"


class ChatSession:
    """统一聊天会话。"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.conversation_history: list[dict] = []
        self.state: str = "clarifying"  # clarifying → confirming → confirmed
        self.project_summary: Optional[dict] = None

    def add_user_message(self, message: str):
        self.conversation_history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str):
        self.conversation_history.append({"role": "assistant", "content": message})

    def to_dict(self) -> dict:
        """序列化为可存储的字典。"""
        return {
            "session_id": self.session_id,
            "conversation_history": self.conversation_history,
            "state": self.state,
            "project_summary": self.project_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        """从字典反序列化。"""
        session = cls(data["session_id"])
        session.conversation_history = data.get("conversation_history", [])
        session.state = data.get("state", "clarifying")
        session.project_summary = data.get("project_summary")
        return session


class ChatService:
    """统一聊天服务 — 单入口，对外提供 chat()。

    内部委托 ProactiveConversationService 做业务逻辑。
    会话状态通过 StateStore 管理，支持未来切换到 Redis。
    """

    def _session_key(self, session_id: str) -> str:
        """生成 StateStore key。"""
        return f"{SESSION_PREFIX}{session_id}"

    async def _get_session(self, session_id: str) -> ChatSession:
        """从 StateStore 获取或创建会话。"""
        store = get_state_store()
        key = self._session_key(session_id)
        data = await store.get(key)
        if data is not None:
            return ChatSession.from_dict(data)
        return ChatSession(session_id)

    async def _save_session(self, session: ChatSession) -> None:
        """保存会话到 StateStore。"""
        store = get_state_store()
        key = self._session_key(session.session_id)
        await store.set(key, session.to_dict(), ttl=SESSION_TTL)

    async def chat(self, user_message: str, session_id: Optional[str] = None, project_id: Optional[int] = None) -> dict:
        """处理用户消息，返回统一格式响应。

        Args:
            user_message: 用户消息内容
            session_id: 会话ID（不传则自动生成）
            project_id: 关联的项目ID（用于广播项目隔离）

        优先使用 ProactiveConversationService（状态机驱动），
        LLM API Key 未配置时退化为简单模式。
        """
        from app.config import settings

        # 创建或获取会话
        # 🔴 P0 安全修复：使用完整 UUID4（128 bit），不再截断为 8 字符
        if not session_id:
            session_id = uuid.uuid4().hex
        session = await self._get_session(session_id)
        session.add_user_message(user_message)

        if settings.active_api_key:
            # 使用 ProactiveConversationService
            result = await self._chat_with_proactive(session_id, user_message)
        else:
            # 简单退化模式
            result = await self._chat_simple(session, user_message)

        # 添加助手消息到历史
        session.add_assistant_message(result.get("reply", ""))

        # 更新会话状态
        if result.get("is_complete"):
            session.state = "confirmed"
            session.project_summary = result.get("design_doc")

        # 持久化会话
        await self._save_session(session)

        # 通过 EventBus 广播（替代直接 WebSocket 调用）
        # 🔴 P2 修复：添加 project_id 实现项目隔离广播
        await event_bus.emit(Event(
            type="chat_message",
            data={
                "agent": "master",
                "content": result.get("reply", ""),
                "session_id": session_id,
            },
            project_id=project_id,
            source="chat_service",
        ))

        return {
            "session_id": session_id,
            "response": result.get("reply", ""),
            "state": session.state,
            "project_summary": result.get("design_doc") if result.get("is_complete") else None,
            "design_doc": result.get("design_doc"),
            "is_complete": result.get("is_complete", False),
            "evaluation": result.get("evaluation"),
            "conversation_history": session.conversation_history,
        }

    async def _chat_with_proactive(self, session_id: str, user_message: str) -> dict:
        """使用 ProactiveConversationService 进行状态机对话。"""
        from app.services.conversation import conversation_service

        return await conversation_service.chat(session_id, user_message)

    async def _chat_simple(self, session: ChatSession, user_message: str) -> dict:
        """无 LLM API Key 时的简单退化对话。"""
        msg_count = len([m for m in session.conversation_history if m["role"] == "user"])

        if msg_count == 1:
            reply = (
                "你好！请描述一下你想做的游戏。比如：\n"
                "- 游戏类型（平台跳跃、RPG、射击等）\n"
                "- 主角是谁？\n"
                "- 核心玩法是什么？"
            )
        elif msg_count == 2:
            reply = "好的，能再描述一下游戏的核心玩法和胜利条件吗？"
        elif msg_count == 3:
            reply = "明白了！敌人或收集物有哪些？有什么特殊机制吗？"
        else:
            reply = "感谢你的描述！我已经收集到足够的信息，正在生成游戏设计文档..."
            from app.schemas.game_design_doc import GameDesignDoc
            doc = GameDesignDoc(
                game_type="未指定",
                protagonist="未指定",
                core_gameplay=" ".join(m["content"] for m in session.conversation_history if m["role"] == "user"),
                enemies_collectibles="未指定",
                win_condition="未指定",
            )
            return {"reply": reply, "design_doc": doc.model_dump(), "is_complete": True}

        return {"reply": reply, "is_complete": False}

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话。"""
        store = get_state_store()
        key = self._session_key(session_id)
        data = await store.get(key)
        if data is not None:
            return ChatSession.from_dict(data)
        return None

    async def delete_session(self, session_id: str) -> bool:
        """删除会话。"""
        store = get_state_store()
        key = self._session_key(session_id)
        return await store.delete(key)

    async def reset_session(self, session_id: str):
        """重置会话（清空对话历史）。"""
        session = await self.get_session(session_id)
        if session:
            session.conversation_history.clear()
            session.state = "clarifying"
            await self._save_session(session)

    async def list_sessions(self) -> list[str]:
        """列出所有会话 ID。"""
        store = get_state_store()
        all_keys = await store.keys(f"{SESSION_PREFIX}*")
        return [k.removeprefix(SESSION_PREFIX) for k in all_keys]


# 全局单例
chat_service = ChatService()
