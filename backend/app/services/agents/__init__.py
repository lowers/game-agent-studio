from app.services.agents.architect import ArchitectAgent
from app.services.agents.devops import DevOpsAgent
from app.services.agents.planner import PlannerAgent
from app.services.agents.programmer import ProgrammerAgent
from app.services.agents.qa import QAAgent
from app.services.agents.security import SecurityAgent

AGENT_REGISTRY: dict[str, type] = {
    "planner": PlannerAgent,
    "architect": ArchitectAgent,
    "programmer": ProgrammerAgent,
    "qa": QAAgent,
    "security": SecurityAgent,
    "devops": DevOpsAgent,
}


def get_agent(role: str):
    """根据 role ID 获取一个 Agent 实例。"""
    cls = AGENT_REGISTRY.get(role)
    if not cls:
        raise ValueError(f"Unknown agent role: {role}")
    return cls()


async def get_agent_run_func(role: str):
    """获取 Agent 的 run 函数（异步），用于工作流运行时。

    使用场景：create_workflow_runner 需要 agent_map
    示例：agent_map[expert_id] = await get_agent_run_func(expert_id)
    """
    agent = get_agent(role)
    # 返回一个绑定了 project_id 和 context 的 async 函数
    async def run_func(project_id: int, task: str, context: dict | None = None) -> dict:
        return await agent.run(project_id, task, context)

    return run_func


def list_available_agents() -> list[dict]:
    """列出所有可用的 Agent。"""
    return [
        {"id": role, "name": cls.name}
        for role, cls in AGENT_REGISTRY.items()
    ]
