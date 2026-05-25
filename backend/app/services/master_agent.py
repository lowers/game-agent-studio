"""主 Agent 调度服务 — 根据项目复杂度分配子 Agent。"""
import logging
import re
import uuid
from pathlib import Path

from app.schemas.game_design_doc import GameDesignDoc
from app.services.agents import get_agent
from app.services.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


def assess_complexity(doc: GameDesignDoc) -> str:
    """根据设计文档评估项目复杂度。"""
    score = 0
    text = f"{doc.game_type} {doc.core_gameplay} {doc.enemies_collectibles}"

    keywords_complex = ["多人", "网络", "3D", "物理", "AI", "程序生成", "开放世界"]
    keywords_simple = ["点击", "文字", "答题", "消消"]

    for kw in keywords_complex:
        if kw in text:
            score += 2
    for kw in keywords_simple:
        if kw in text:
            score -= 1

    if score >= 4:
        return "complex"
    elif score >= 1:
        return "medium"
    return "simple"


AGENT_COMBOS = {
    "simple": ["planner", "programmer"],
    "medium": ["planner", "architect", "programmer"],
    "complex": ["planner", "architect", "programmer", "qa", "security", "devops"],
}


async def run_workflow(
    project_id: int, doc: GameDesignDoc, db=None, *, workflow_id: str | None = None
) -> dict:
    """执行完整的 Agent 工作流。"""
    complexity = assess_complexity(doc)
    agent_roles = AGENT_COMBOS[complexity]
    # 🔴 P0 安全修复：使用完整 UUID4；支持外部传入 workflow_id
    if workflow_id is None:
        workflow_id = uuid.uuid4().hex

    await event_bus.emit(Event(
        type="workflow_started",
        project_id=project_id,
        data={"complexity": complexity, "agents": agent_roles, "workflow_id": workflow_id},
        source="master_agent",
    ))

    results = []
    previous_results = ""

    for idx, role in enumerate(agent_roles):
        agent = get_agent(role)
        task = _build_task_prompt(role, doc)
        context = {
            "design_doc": doc.model_dump(),
            "previous_results": previous_results,
        }

        try:
            result = await agent.run(project_id, task, context)
        except Exception as e:
            logger.exception(f"Agent {role} failed: {e}")
            result = {"agent": role, "status": "error", "result": str(e)}

        results.append(result)
        previous_results += f"\n\n[{agent.name} 结果]\n{result.get('result', '')}"

        if db is not None:
            from app.models.agent_result import AgentResult
            agent_result = AgentResult(
                project_id=project_id,
                agent_role=role,
                task=task,
                result=result.get("result", ""),
                status=result.get("status", "unknown"),
                execution_order=idx,
                workflow_id=workflow_id,
            )
            db.add(agent_result)
            await db.flush()

    # === 保存程序员生成的代码到文件 ===
    for result in results:
        if result.get("agent") == "programmer" and result.get("status") == "done":
            await _save_programmer_output(project_id, result.get("result", ""))
            break

    # === 创建任务（异步） ===
    if db is not None:
        try:
            await _create_tasks_from_results(project_id, results, doc, db)
        except Exception as e:
            logger.exception(f"Create tasks failed: {e}")

    await event_bus.emit(Event(
        type="workflow_completed",
        project_id=project_id,
        data={"complexity": complexity, "results": [r["agent"] for r in results], "workflow_id": workflow_id},
        source="master_agent",
    ))

    return {
        "complexity": complexity,
        "agents": agent_roles,
        "results": results,
        "workflow_id": workflow_id,
    }


def _build_task_prompt(role: str, doc: GameDesignDoc) -> str:
    """为每个 Agent 构建具体任务提示。"""
    base = f"游戏类型：{doc.game_type}\n主角：{doc.protagonist}\n核心玩法：{doc.core_gameplay}\n敌人/收集物：{doc.enemies_collectibles}\n胜利条件：{doc.win_condition}"

    prompts = {
        "planner": f"请根据以下设计文档拆分模块和任务：\n{base}",
        "architect": f"请根据以下设计文档设计技术架构：\n{base}",
        "programmer": f"请根据以下设计文档，用HTML5 Canvas+JavaScript生成一个可直接运行的HTML文件。"
                     f"要求：完整可用、样式美观、有交互。只输出HTML代码，不要解释。\n{base}",
        "qa": f"请为以下游戏生成测试用例并检查代码质量：\n{base}",
        "security": f"请审计以下游戏代码的安全漏洞（XSS、注入、敏感信息泄露等）并提供修复方案：\n{base}",
        "devops": f"请为以下游戏项目生成构建配置、部署脚本和CI/CD管道：\n{base}",
    }
    return prompts.get(role, base)


def _extract_html(text: str) -> str:
    """从 LLM 输出中提取 HTML 代码。"""
    # 尝试提取 markdown 代码块中的 HTML
    match = re.search(r'```(?:html)?\s*\n?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 尝试提取完整的 HTML 文档
    match = re.search(r'<(!DOCTYPE|html).*?</html>', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0).strip()

    # 回退：整个文本作为 HTML
    if '<!DOCTYPE' in text or '<html' in text or '<canvas' in text:
        return text
    return ""


async def _save_programmer_output(project_id: int, code: str):
    """保存程序员生成的代码到项目输出目录。"""

    # 提取 HTML
    html = _extract_html(code)
    if not html:
        logger.warning(f"No HTML found in programmer output for project {project_id}")
        return

    # 输出目录：基于项目根目录的绝对路径，避免依赖进程工作目录
    project_root = Path(__file__).resolve().parents[2]  # app/services → app → backend
    output_dir = project_root / "output" / f"project_{project_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 写入 index.html
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    # 广播文件变更
    await event_bus.emit(Event(
        type="project_updated",
        project_id=project_id,
        data={
            "preview_url": f"/output/project_{project_id}/index.html",
            "files": [str(f.relative_to(output_dir.parent)) for f in output_dir.rglob("*") if f.is_file()],
        },
        source="master_agent",
    ))

    # 广播文件树更新
    await event_bus.emit(Event(
        type="task_created",
        project_id=project_id,
        data={
            "id": 0,
            "name": "生成游戏代码",
            "status": "done",
            "assigned_agent": "programmer",
        },
        source="master_agent",
    ))

    logger.info(f"Saved game code for project {project_id} to {index_path}")


async def _create_tasks_from_results(project_id: int, results: list, doc, db):
    """从 Agent 结果创建任务。

    使用 SQLAlchemy ORM 安全查询，防止 SQL 注入。
    """
    from sqlalchemy import select

    from app.models import Module, Task

    tasks_created = []

    for result_item in results:
        agent = result_item.get("agent", "")
        if not agent:
            continue

        # 创建模块
        module_names = {
            "planner": "需求规划",
            "architect": "系统架构",
            "programmer": "代码开发",
            "qa": "质量测试",
            "security": "安全审计",
            "devops": "构建部署",
        }
        module_name = module_names.get(agent, agent)

        # 查找或创建模块（使用 ORM 参数化查询，防止 SQL 注入）
        stmt = select(Module.id).where(
            Module.project_id == project_id,
            Module.name == module_name,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            module_id = existing
        else:
            module_obj = Module(
                project_id=project_id,
                name=module_name,
                description=f"由 {agent} Agent 自动创建",
            )
            db.add(module_obj)
            await db.flush()
            module_id = module_obj.id

        # 创建任务
        status_map = {
            "done": "done",
            "error": "todo",
            "running": "in_progress",
        }

        task_status = status_map.get(result_item.get("status", ""), "todo")
        task_obj = Task(
            module_id=module_id,
            name=f"{module_name} - {agent}",
            status=task_status,
            assigned_agent=agent,
        )
        db.add(task_obj)
        await db.flush()
        tasks_created.append(task_obj.id)

    await db.commit()

    if tasks_created:
        logger.info(f"Created {len(tasks_created)} tasks for project {project_id}")

        # 广播任务创建
        for tid in tasks_created:
            await event_bus.emit(Event(
                type="task_created",
                project_id=project_id,
                data={"id": tid, "status": "todo"},
                source="master_agent",
            ))
