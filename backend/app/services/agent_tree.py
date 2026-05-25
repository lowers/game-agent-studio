"""Agent 树形结构管理"""
import asyncio
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import AgentStatus


class AgentNode(BaseModel):
    id: str
    name: str
    role: str  # "master", "planner", "architect", "programmer", "qa"
    agent_type: str  # "parent", "child"
    status: AgentStatus = AgentStatus.IDLE
    parent_id: Optional[str] = None
    children: list[str] = []
    current_task: str = ""
    output: str = ""
    progress: int = 0

class AgentTree:
    """Agent 树管理单例"""
    _instance: Optional['AgentTree'] = None

    def __init__(self):
        self.nodes: dict[str, AgentNode] = {}
        self.lock = asyncio.Lock()
        self._callbacks: list[callable] = []

    @classmethod
    def get_instance(cls) -> 'AgentTree':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_callback(self, cb: callable):
        self._callbacks.append(cb)

    async def add_node(self, node: AgentNode):
        async with self.lock:
            self.nodes[node.id] = node
            await self._notify()

    async def update_node(self, node_id: str, **updates):
        async with self.lock:
            if node_id in self.nodes:
                for k, v in updates.items():
                    if hasattr(self.nodes[node_id], k):
                        setattr(self.nodes[node_id], k, v)
                await self._notify()

    async def _notify(self):
        for cb in self._callbacks:
            await cb(self.get_tree_data())

    def get_tree_data(self) -> dict:
        return {
            "nodes": [n.model_dump() for n in self.nodes.values()],
            "root_ids": [n.id for n in self.nodes.values() if n.parent_id is None]
        }

    def reset(self):
        """重置树状态"""
        self.nodes.clear()
        self._callbacks.clear()
