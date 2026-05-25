"""事件总线 — 解耦 Service 层对 API 层的直接依赖。

架构原则：
- Service 层只发事件，不关心谁消费
- API 层（WebSocket）订阅事件并推送
- 新增消费者只需订阅，无需修改 Service 代码

使用方式：
    from app.services.event_bus import event_bus, Event

    # 发布事件（Service 层）
    await event_bus.emit(Event("workflow_started", project_id=1, data={...}))

    # 订阅事件（API 层）
    async def on_workflow_started(event: Event):
        await broadcast(event.project_id, {"type": event.type, "data": event.data})
    event_bus.subscribe("workflow_started", on_workflow_started)
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """事件数据结构。"""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    project_id: int | None = None
    source: str = ""  # 发出事件的模块名，便于追踪


# 回调类型：接收 Event 的异步函数
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """进程内异步事件总线。

    特性：
    - 支持通配符订阅：subscribe("*", handler) 接收所有事件
    - 异常隔离：单个 handler 报错不影响其他 handler
    - 异步并发：同一事件的所有 handler 并行执行
    """

    def __init__(self):
        # {event_type: [handler, ...]}
        self._handlers: dict[str, list[EventHandler]] = {}
        # 通配符订阅
        self._wildcard_handlers: list[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件。

        Args:
            event_type: 事件类型，"*" 表示订阅所有事件
            handler: 异步回调函数
        """
        if event_type == "*":
            if handler not in self._wildcard_handlers:
                self._wildcard_handlers.append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅。"""
        if event_type == "*":
            self._wildcard_handlers = [h for h in self._wildcard_handlers if h is not handler]
        elif event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h is not handler]

    async def emit(self, event: Event) -> None:
        """发布事件，通知所有订阅者。"""
        handlers = list(self._handlers.get(event.type, [])) + list(self._wildcard_handlers)

        if not handlers:
            return

        # 并行执行所有 handler，异常隔离
        tasks = [self._safe_call(handler, event) for handler in handlers]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _safe_call(handler: EventHandler, event: Event) -> None:
        """安全调用 handler，异常不外泄。"""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "EventBus handler %s failed for event %s",
                getattr(handler, "__name__", repr(handler)),
                event.type,
            )

    def clear(self) -> None:
        """清空所有订阅（测试用）。"""
        self._handlers.clear()
        self._wildcard_handlers.clear()


# 全局单例
event_bus = EventBus()
