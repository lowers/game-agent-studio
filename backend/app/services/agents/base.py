"""Agent 基类 — 所有子 Agent 的公共逻辑。"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.event_bus import Event, event_bus


class BaseAgent:
    """子 Agent 基类。"""

    role: str = "base"
    name: str = "基础 Agent"

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.active_api_key,
            base_url=settings.active_base_url,
            model=settings.active_model,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            request_timeout=120,
        )

    def _get_status_label(self, status: str) -> str:
        """返回状态对应的可读文本标签，子类可重写。"""
        status_map = {
            "running": "Working on it",
            "done": "Completed",
            "error": "Error",
            "blocked": "Blocked",
        }
        return status_map.get(status, status.capitalize())

    async def get_system_prompt(self) -> str:
        """获取系统提示词，优先返回自定义提示词，否则返回默认提示词。"""
        from app.services.prompt_store import _prompt_store
        if _prompt_store is not None:
            custom = await _prompt_store.get_prompt(self.role) if hasattr(_prompt_store, 'get_prompt') else None
            if custom:
                return custom
        return self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """子类可重写此方法返回默认提示词。"""
        return ""

    async def run(self, project_id: int, task: str, context: dict | None = None) -> dict:
        """执行 Agent 任务 — 支持流式输出。"""
        # 发布开始状态
        status_text = f"{self._get_status_label('running')}... ({self.name})"
        await event_bus.emit(Event(
            type="agent_status",
            project_id=project_id,
            data={"agent": self.role, "agent_name": self.name, "status": "running", "task": task, "status_text": status_text},
        ))

        try:
            messages = [
                SystemMessage(content=await self.get_system_prompt()),
                HumanMessage(content=self._build_prompt(task, context)),
            ]

            # 使用 astream 逐 token 流式输出，emit agent_output
            full_content = []
            is_first = True
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_content.append(chunk.content)
                    # 逐 token 推送输出（统一字段名：chunk / is_final）
                    await event_bus.emit(Event(
                        type="agent_output",
                        project_id=project_id,
                        data={
                            "agent": self.role,
                            "chunk": chunk.content,
                            "is_final": False,
                        },
                    ))
                    is_first = False
            # 流结束，发送最终标记（便于前端确认流式结束）
            if not is_first:
                await event_bus.emit(Event(
                    type="agent_output",
                    project_id=project_id,
                    data={
                        "agent": self.role,
                        "chunk": "",
                        "is_final": True,
                    },
                ))

            result = "".join(full_content)

            # 发布完成状态
            status_text = f"{self._get_status_label('done')} ({self.name})"
            await event_bus.emit(Event(
                type="agent_status",
                project_id=project_id,
                data={"agent": self.role, "agent_name": self.name, "status": "done", "task": task, "status_text": status_text},
            ))

            return {"agent": self.role, "status": "done", "result": result}

        except Exception as e:
            status_text = f"{self._get_status_label('error')}: {str(e)[:100]} ({self.name})"
            await event_bus.emit(Event(
                type="agent_status",
                project_id=project_id,
                data={"agent": self.role, "agent_name": self.name, "status": "error", "task": str(e), "status_text": status_text},
            ))
            return {"agent": self.role, "status": "error", "result": str(e)}

    def _build_prompt(self, task: str, context: dict | None) -> str:
        parts = [f"任务：{task}"]
        if context:
            if context.get("design_doc"):
                parts.append(f"\n游戏设计文档：\n{context['design_doc']}")
            if context.get("previous_results"):
                parts.append(f"\n前置任务结果：\n{context['previous_results']}")
        return "\n".join(parts)
