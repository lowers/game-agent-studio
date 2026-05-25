"""Agent 系统提示词存储 — 支持用户自定义修改 Agent 系统提示词。

使用 StateStore 作为后端，支持从内存切换到 Redis 等持久化存储。

使用方式：
    from app.services.prompt_store import get_prompt_store

    store = get_prompt_store()
    await store.set_prompt("planner", "自定义提示词")
    prompt = await store.get_prompt("planner")  # 返回自定义提示词或 None
"""
from typing import Optional

from app.services.state_store import StateStore, get_state_store


class PromptStore:
    """Agent 系统提示词存储层。"""

    def __init__(self, state_store: StateStore):
        self._store = state_store
        self._prefix = "agent:prompt:"

    async def get_prompt(self, agent_id: str) -> Optional[str]:
        """获取自定义提示词，不存在返回 None（使用默认）。"""
        result = await self._store.get(self._prefix + agent_id)
        return result

    async def set_prompt(self, agent_id: str, prompt: str) -> None:
        """设置自定义提示词（永不过期）。"""
        await self._store.set(self._prefix + agent_id, prompt, ttl=None)

    async def delete_prompt(self, agent_id: str) -> bool:
        """删除自定义提示词（恢复默认）。"""
        return await self._store.delete(self._prefix + agent_id)

    async def list_prompts(self) -> dict[str, str]:
        """列出所有已自定义的 Agent 提示词。"""
        keys = await self._store.keys(self._prefix + "*")
        result = {}
        for key in keys:
            agent_id = key[len(self._prefix):]
            prompt = await self._store.get(key)
            result[agent_id] = prompt
        return result


# === 全局单例 ===
_prompt_store: Optional[PromptStore] = None


def get_prompt_store() -> PromptStore:
    """获取全局 PromptStore 实例。"""
    global _prompt_store
    if _prompt_store is None:
        _prompt_store = PromptStore(get_state_store())
    return _prompt_store
