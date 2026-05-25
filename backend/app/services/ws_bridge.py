"""Event Bus ↔ WebSocket 桥接适配器。

在应用启动时调用 init_ws_bridge()，将 EventBus 事件自动转发到 WebSocket 连接。

这样 Service 层只需 emit 事件，无需知道 WebSocket 的存在。
"""
import logging

from app.services.event_bus import Event, event_bus

logger = logging.getLogger(__name__)

_bridge_initialized = False


def _make_broadcast_handler():
    """创建一个将 Event 转为 WebSocket 推送的 handler。"""
    async def handler(event: Event) -> None:
        if event.project_id is None:
            return
        # 延迟导入避免循环依赖
        from app.api.v1.endpoints.websocket import broadcast
        await broadcast(event.project_id, {
            "type": event.type,
            "data": event.data,
        })
    return handler


def _make_chat_broadcast_handler():
    """创建一个将 Event 转为 Chat WebSocket 推送的 handler。

    🔴 P2 修复：实现项目隔离广播
    - 如果 event.project_id 非空 → 只广播到该项目的 WebSocket 连接
    - 如果 event.project_id 为空 → 广播到全局 chat 连接（兼容原有聊天模式）
    """
    async def handler(event: Event) -> None:

        from app.api.v1.endpoints.websocket import _chat_connections, _connections

        data = event.data

        if event.project_id is not None:
            # 🔴 P2 修复：有 project_id → 只广播到该项目
            conns = _connections.get(event.project_id, set())
            dead = []
            for ws in conns:
                try:
                    await ws.send_json({
                        "type": "chat_message",
                        "data": {
                            "agent": data.get("agent", ""),
                            "content": data.get("content", ""),
                            "session_id": data.get("session_id"),
                        }
                    })
                except Exception:
                    dead.append(ws)
            for ws in dead:
                conns.discard(ws)
        else:
            # 无 project_id → 广播到全局 chat 连接（兼容需求沟通等非项目场景）
            dead = []
            for ws in _chat_connections:
                try:
                    await ws.send_json({
                        "type": "chat_message",
                        "data": {
                            "agent": data.get("agent", ""),
                            "content": data.get("content", ""),
                            "session_id": data.get("session_id"),
                        }
                    })
                except Exception:
                    dead.append(ws)
            for ws in dead:
                _chat_connections.discard(ws)
    return handler


def _make_tree_broadcast_handler():
    """创建一个将 Agent Tree Event 推送的 handler。"""
    async def handler(event: Event) -> None:
        from app.api.v1.endpoints.websocket import broadcast_agent_tree
        await broadcast_agent_tree(event.data)
    return handler


def _make_file_change_handler():
    """创建一个将文件变更 Event 推送的 handler。"""
    async def handler(event: Event) -> None:
        from app.api.v1.endpoints.websocket import broadcast
        await broadcast(event.project_id, {
            "type": "file_change",
            "data": event.data,
        })
    return handler


def _make_browser_change_handler():
    """创建一个将浏览器变更 Event 推送的 handler。"""
    async def handler(event: Event) -> None:
        from app.api.v1.endpoints.websocket import broadcast
        await broadcast(event.project_id, {
            "type": "browser_change",
            "data": event.data,
        })
    return handler


def init_ws_bridge() -> None:
    """初始化 Event Bus → WebSocket 桥接。

    应在 FastAPI lifespan 启动时调用一次。
    """
    global _bridge_initialized
    if _bridge_initialized:
        return

    # 项目级事件 → 项目 WebSocket
    event_bus.subscribe("workflow_started", _make_broadcast_handler())
    event_bus.subscribe("workflow_completed", _make_broadcast_handler())
    event_bus.subscribe("workflow_paused", _make_broadcast_handler())
    event_bus.subscribe("workflow_resumed", _make_broadcast_handler())
    event_bus.subscribe("workflow_interrupted", _make_broadcast_handler())
    event_bus.subscribe("workflow_error", _make_broadcast_handler())
    event_bus.subscribe("workflow_status", _make_broadcast_handler())  # 并行工作流状态
    event_bus.subscribe("expert_status", _make_broadcast_handler())    # 专家状态更新
    event_bus.subscribe("project_updated", _make_broadcast_handler())
    event_bus.subscribe("project_created", _make_broadcast_handler())  # 🔴 新增：项目创建通知
    event_bus.subscribe("task_created", _make_broadcast_handler())
    event_bus.subscribe("agent_status", _make_broadcast_handler())
    event_bus.subscribe("agent_progress", _make_broadcast_handler())
    event_bus.subscribe("agent_output", _make_broadcast_handler())
    event_bus.subscribe("agent_blocked", _make_broadcast_handler())
    event_bus.subscribe("agent_unblocked", _make_broadcast_handler())
    event_bus.subscribe("agent_question", _make_broadcast_handler())
    # 🔴 新增：文件/浏览器实时变更推送
    event_bus.subscribe("file_change", _make_file_change_handler())
    event_bus.subscribe("browser_change", _make_browser_change_handler())

    # 聊天级事件 → Chat WebSocket
    event_bus.subscribe("chat_message", _make_chat_broadcast_handler())
    event_bus.subscribe("agent_tree_update", _make_tree_broadcast_handler())

    _bridge_initialized = True
    logger.info("EventBus → WebSocket bridge initialized")
