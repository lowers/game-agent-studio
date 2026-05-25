"""WebSocket 端点 — 推送 Agent 状态变化和任务更新。

扩展支持：
- agent_output: Agent 输出流（打字机效果）
- agent_progress: Agent 进度更新
- agent_blocked: Agent 阻塞/解锁通知
- agent_question: Agent 向用户提问
- agent_feedback: 用户对 Agent 问题的响应
- pause/resume/interrupt: 工作流控制
- token 认证: 连接时通过 ?token=xxx 传递 JWT
"""
import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.config import settings
from app.services.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

# 连接池: {project_id: {websocket, ...}}
_connections: dict[int, set[WebSocket]] = {}
# Chat 模式连接池（无 project_id）
_chat_connections: set[WebSocket] = set()

# 最大 WebSocket 连接数限制
MAX_CONNECTIONS_PER_PROJECT = 100
MAX_TOTAL_CONNECTIONS = 1000

# Agent 角色枚举
AGENT_ROLES = {"planner", "architect", "programmer", "qa", "security", "devops"}


async def _verify_ws_token(token: str | None) -> bool:
    """验证 WebSocket 连接的 JWT token。返回是否认证成功。

    🔴 P0 安全修复：生产环境必须提供有效 token。
    - token=None: 仅 DEBUG 模式允许（降级兼容开发阶段）
    - token=无效: 始终拒绝
    """
    if token is None:
        # 无 token：仅开发环境允许连接（降级模式）
        if not settings.DEBUG:
            return False
        return True
    token_data = decode_access_token(token)
    return token_data is not None


@router.websocket("/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: Optional[str] = Query(default=None),
):
    """WebSocket 连接端点，支持双向消息通信和 token 认证。"""
    # 先 accept 再验证，避免 WebSocket 403 兼容问题
    await websocket.accept()

    if not await _verify_ws_token(token):
        await websocket.send_json({
            "type": "auth_error",
            "data": {"message": "Invalid or expired token"},
        })
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # 认证成功通知
    if token:
        await websocket.send_json({"type": "auth_ok", "data": {"authenticated": True}})

    # 🔴 P0 安全修复：连接数限制
    total_conns = sum(len(s) for s in _connections.values()) + len(_chat_connections)
    if total_conns >= MAX_TOTAL_CONNECTIONS:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Too many connections"},
        })
        await websocket.close(code=1013, reason="Max connections reached")
        return

    if len(_connections.get(project_id, set())) >= MAX_CONNECTIONS_PER_PROJECT:
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Too many connections for project {project_id}"},
        })
        await websocket.close(code=1013, reason="Max project connections reached")
        return

    if project_id not in _connections:
        _connections[project_id] = set()
    _connections[project_id].add(websocket)

    try:
        while True:
            raw_message = await websocket.receive_text()
            await _handle_message(websocket, project_id, raw_message)
    except WebSocketDisconnect:
        _connections[project_id].discard(websocket)
        if not _connections[project_id]:
            del _connections[project_id]
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
        _connections[project_id].discard(websocket)


async def _handle_message(websocket: WebSocket, project_id: int, raw_message: str) -> None:
    """处理客户端发送的消息。"""
    try:
        message = json.loads(raw_message)
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Invalid JSON format"},
        })
        return

    message_type = message.get("type")
    data = message.get("data", {})

    if message_type == "ping":
        await websocket.send_json({"type": "pong", "data": {}})

    elif message_type == "chat":
        await _handle_chat(websocket, project_id, data)

    elif message_type == "subscribe":
        await websocket.send_json({
            "type": "subscribed",
            "data": {"project_id": project_id},
        })

    elif message_type == "agent_feedback":
        await _handle_agent_feedback(websocket, project_id, data)

    elif message_type == "pause_workflow":
        await _handle_workflow_control(websocket, project_id, data, "pause")

    elif message_type == "resume_workflow":
        await _handle_workflow_control(websocket, project_id, data, "resume")

    elif message_type == "interrupt_workflow":
        await _handle_workflow_control(websocket, project_id, data, "interrupt")

    else:
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"},
        })


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
):
    """WebSocket 连接端点，用于聊天模式（无 project_id），支持 token 认证。"""
    await websocket.accept()

    if not await _verify_ws_token(token):
        await websocket.send_json({
            "type": "auth_error",
            "data": {"message": "Invalid or expired token"},
        })
        await websocket.close(code=4001, reason="Authentication failed")
        return

    if token:
        await websocket.send_json({"type": "auth_ok", "data": {"authenticated": True}})

    # 🔴 P0 安全修复：连接数限制
    total_conns = sum(len(s) for s in _connections.values()) + len(_chat_connections)
    if total_conns >= MAX_TOTAL_CONNECTIONS:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Too many connections"},
        })
        await websocket.close(code=1013, reason="Max connections reached")
        return

    _chat_connections.add(websocket)

    try:
        while True:
            raw_message = await websocket.receive_text()
            await _handle_chat_message(websocket, raw_message)
    except WebSocketDisconnect:
        _chat_connections.discard(websocket)
    except Exception as e:
        logger.error(f"WebSocket chat error: {e}")
        _chat_connections.discard(websocket)


async def _handle_chat_message(websocket: WebSocket, raw_message: str) -> None:
    """处理聊天消息。"""
    try:
        message = json.loads(raw_message)
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Invalid JSON format"},
        })
        return

    message_type = message.get("type")
    data = message.get("data", {})

    if message_type == "ping":
        await websocket.send_json({"type": "pong", "data": {}})

    elif message_type == "chat":
        content = data.get("content", "")
        if content:
            await websocket.send_json({
                "type": "chat_ack",
                "data": {"received": True, "content_length": len(content)},
            })

    elif message_type == "subscribe":
        await websocket.send_json({
            "type": "subscribed",
            "data": {"mode": "chat"},
        })

    else:
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"},
        })


async def _handle_chat(websocket: WebSocket, project_id: int, data: dict[str, Any]) -> None:
    """处理聊天消息。"""
    content = data.get("content", "")

    if not content:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Chat content is empty"},
        })
        return

    if len(content) > 5000:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Chat content exceeds maximum length (5000 chars)"},
        })
        return

    await websocket.send_json({
        "type": "chat_ack",
        "data": {"received": True, "content_length": len(content)},
    })


async def _handle_agent_feedback(
    websocket: WebSocket, project_id: int, data: dict[str, Any]
) -> None:
    """处理用户对 Agent 问题的反馈。"""
    agent = data.get("agent")
    answer = data.get("answer")
    question_id = data.get("question_id")

    if agent not in AGENT_ROLES:
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Invalid agent role: {agent}"},
        })
        return

    if not answer:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Answer is required"},
        })
        return

    from app.services.agent_coordinator import coordinator

    if question_id:
        success = await coordinator.submit_answer(question_id, answer)
    else:
        success = False
        for wf in coordinator.workflows.values():
            if wf.project_id == project_id and wf.current_question_id:
                success = await coordinator.submit_answer(wf.current_question_id, answer)
                break

    await websocket.send_json({
        "type": "agent_feedback_ack",
        "data": {
            "agent": agent,
            "answer": answer,
            "received": True,
            "workflow_resuming": success,
        },
    })

    if success:
        for wf in coordinator.workflows.values():
            if wf.project_id == project_id and wf.status.value == "waiting_user":
                asyncio.create_task(_resume_workflow_async(wf.workflow_id))
                break


async def _resume_workflow_async(workflow_id: str) -> None:
    """异步恢复工作流"""
    from app.services.agent_coordinator import coordinator
    try:
        await coordinator.resume_workflow(workflow_id)
    except Exception:
        logger.exception(f"Failed to resume workflow {workflow_id}")


async def _handle_workflow_control(
    websocket: WebSocket, project_id: int, data: dict, action: str
) -> None:
    """处理工作流控制命令（暂停/恢复/中断）。"""
    from app.services.agent_coordinator import coordinator

    workflow_id = data.get("workflow_id")

    success = False
    if action == "pause":
        success = await coordinator.pause_workflow(workflow_id)
    elif action == "resume":
        asyncio.create_task(_resume_workflow_async(workflow_id))
        success = True
    elif action == "interrupt":
        success = await coordinator.interrupt_workflow(workflow_id)

    await websocket.send_json({
        "type": f"workflow_{action}_ack",
        "data": {
            "workflow_id": workflow_id,
            "received": True,
            "success": success,
        },
    })


# === 广播消息工具函数 ===

async def broadcast(project_id: int, data: dict) -> None:
    """向指定项目的所有连接广播消息。"""
    conns = _connections.get(project_id, set())
    dead: list[WebSocket] = []

    for ws in conns:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)

    for ws in dead:
        conns.discard(ws)


async def broadcast_agent_output(
    project_id: int, agent: str, chunk: str, is_final: bool = False
) -> None:
    """广播 Agent 输出流（打字机效果）。"""
    await broadcast(project_id, {
        "type": "agent_output",
        "data": {
            "agent": agent,
            "chunk": chunk,
            "is_final": is_final,
        }
    })


async def broadcast_agent_progress(
    project_id: int, agent: str, progress: int, message: str = ""
) -> None:
    """广播 Agent 进度更新。"""
    await broadcast(project_id, {
        "type": "agent_progress",
        "data": {
            "agent": agent,
            "progress": progress,
            "message": message,
        }
    })


async def broadcast_agent_status(project_id: int, agent_state: dict) -> None:
    """广播 Agent 状态更新。"""
    await broadcast(project_id, {
        "type": "agent_status",
        "data": agent_state,
    })


async def broadcast_agent_blocked(
    project_id: int, agent: str, blocked_by: str = None, reason: str = ""
) -> None:
    """广播 Agent 阻塞通知。"""
    await broadcast(project_id, {
        "type": "agent_blocked",
        "data": {
            "agent": agent,
            "blocked_by": blocked_by,
            "reason": reason,
        }
    })


async def broadcast_agent_unblocked(project_id: int, agent: str) -> None:
    """广播 Agent 解锁通知。"""
    await broadcast(project_id, {
        "type": "agent_unblocked",
        "data": {
            "agent": agent,
        }
    })


async def broadcast_agent_question(
    project_id: int, agent: str, question: str, options: list[str] = None
) -> None:
    """广播 Agent 向用户提问。"""
    await broadcast(project_id, {
        "type": "agent_question",
        "data": {
            "agent": agent,
            "question": question,
            "options": options or [],
        }
    })


async def broadcast_workflow_started(project_id: int, workflow_id: str) -> None:
    """广播工作流开始。"""
    await broadcast(project_id, {
        "type": "workflow_started",
        "data": {"workflow_id": workflow_id}
    })


async def broadcast_workflow_completed(project_id: int, workflow_id: str) -> None:
    """广播工作流完成。"""
    await broadcast(project_id, {
        "type": "workflow_completed",
        "data": {"workflow_id": workflow_id}
    })


async def broadcast_workflow_error(project_id: int, workflow_id: str, error: str) -> None:
    """广播工作流错误。"""
    await broadcast(project_id, {
        "type": "workflow_error",
        "data": {"workflow_id": workflow_id, "error": error}
    })


async def broadcast_chat_message(agent: str, content: str, session_id: str = None) -> None:
    """广播聊天消息到所有 chat 连接"""
    dead: list[WebSocket] = []

    for ws in _chat_connections:
        try:
            await ws.send_json({
                "type": "chat_message",
                "data": {
                    "agent": agent,
                    "content": content,
                    "session_id": session_id
                }
            })
        except Exception:
            dead.append(ws)

    for ws in dead:
        _chat_connections.discard(ws)


async def broadcast_agent_tree(tree_data: dict) -> None:
    """广播 Agent 树更新到所有 chat 连接"""
    dead: list[WebSocket] = []

    for ws in _chat_connections:
        try:
            await ws.send_json({
                "type": "agent_tree_update",
                "data": tree_data
            })
        except Exception:
            dead.append(ws)

    for ws in dead:
        _chat_connections.discard(ws)


async def broadcast_project_summary(summary: dict) -> None:
    """广播项目概要到所有 chat 连接"""
    dead: list[WebSocket] = []

    for ws in _chat_connections:
        try:
            await ws.send_json({
                "type": "project_summary",
                "data": summary
            })
        except Exception:
            dead.append(ws)

    for ws in dead:
        _chat_connections.discard(ws)
