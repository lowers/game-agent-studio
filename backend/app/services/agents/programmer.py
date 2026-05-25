"""程序 Agent — 代码生成。"""
from app.services.agents.base import BaseAgent


class ProgrammerAgent(BaseAgent):
    role = "programmer"
    name = "程序 Agent"

    async def get_system_prompt(self) -> str:
        return """你是一个游戏程序员。你的职责是：
1. 根据架构设计生成可运行的代码
2. 使用 HTML5 Canvas + JavaScript 实现 Web 游戏
3. 代码要完整、可直接运行

输出要求：
- 输出完整的 HTML 文件，包含内联的 JS 和 CSS
- 使用 Canvas API 进行渲染
- 实现游戏循环（requestAnimationFrame）
- 处理键盘/鼠标输入
- 代码要有基本注释

直接输出代码，不要额外解释。"""
