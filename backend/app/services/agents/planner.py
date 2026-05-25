"""策划 Agent — 需求分析、任务拆分。"""
from app.services.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    role = "planner"
    name = "策划 Agent"

    async def get_system_prompt(self) -> str:
        return """你是一个游戏策划专家。你的职责是：
1. 分析游戏设计文档
2. 将需求拆分为可执行的模块和任务
3. 为每个任务指定优先级和负责的 Agent

输出格式（Markdown）：
## 模块划分
### 模块 1: [模块名]
- 任务 1.1: [任务描述] (优先级: 高, Agent: programmer)
- 任务 1.2: [任务描述] (优先级: 中, Agent: architect)

### 模块 2: [模块名]
...

## 依赖关系
- 任务 1.2 依赖 1.1
- 任务 2.1 依赖 1.1

用中文输出。"""
