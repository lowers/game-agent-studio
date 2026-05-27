"""并行工作流运行时引擎 — 管理多专家并行执行全流程。

核心职责:
- 调度专家执行（依赖调度器）
- 处理 Agent 输出（P0: 流式输出）
- 处理用户提问与回答（P1: 问答闭环）
- 处理用户确认（确认开发）
- 状态持久化（StateStore）
- 事件广播（EventBus）

工作流程:
1. 初始化 -> 解析依赖 -> Kahn 拓扑排序
2. Round 0: 执行 planner
3. 用户确认需求（可选）
4. Round 1: 并行执行 architect + qa
5. Round 2: 执行 programmer + security
6. 用户确认开发
7. Round 3: 执行 devops
8. 完成

P1 新增：Agent 提问 → 暂停 → 用户回答 → 恢复
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from app.services.event_bus import Event  # runtime import for emit()

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.schemas.expert import ParallelWorkflowConfig
    from app.services.dag_scheduler import DAGScheduler


# === 工作流状态 ===
WORKFLOW_STATUS = {
    "idle": "空闲",
    "running": "运行中",
    "paused": "已暂停",
    "waiting_user": "等待用户确认",
    "completed": "已完成",
    "interrupted": "已中断",
    "error": "出错",
}


@dataclass
class WorkflowSession:
    """单次工作流执行会话。"""
    workflow_id: str
    project_id: int
    status: str = "idle"
    config: dict | None = None  # ParallelWorkflowConfig dict
    current_round: int = 0
    expert_results: dict[str, dict] = field(default_factory=dict)  # expert_id -> {status, output, ...}
    created_at: float = field(default_factory=lambda: asyncio.get_running_loop().time())
    updated_at: float = field(default_factory=lambda: asyncio.get_running_loop().time())
    error_message: str | None = None
    # P1: 当前待处理问题
    pending_question_id: str | None = None
    pending_question_agent: str | None = None


class WorkflowRunner:
    """并行工作流运行时。

    支持两种模式:
    - "parallel": 自动并行执行（默认）
    - "confirm": 关键节点等待用户确认
    """

    def __init__(
        self,
        config: "ParallelWorkflowConfig",
        dag_scheduler: "DAGScheduler",
        agent_map: dict[str, Callable],  # expert_id -> Agent.run function
        event_bus: object,
    ):
        """初始化工作流运行时。

        Args:
            config: 工作流配置
            dag_scheduler: 预构建好的 DAG 调度器
            agent_map: expert_id -> Agent 实例或 run 函数映射
            event_bus: EventBus 实例
        """
        self.config = config
        self.dag_scheduler = dag_scheduler
        self.agent_map = agent_map
        self.event_bus = event_bus

        # 会话状态
        self.session = WorkflowSession(
            workflow_id=f"wf-{uuid.uuid4().hex[:12]}",
            project_id=config.project_id,
            config=config.model_dump() if hasattr(config, 'model_dump') else config,
        )

        # 轮次控制
        self._round_lock = asyncio.Lock()
        self._current_task: asyncio.Task | None = None
        # P1: 当前待回答问题 {expert_id: question_id}
        self._current_question: dict[str, str | None] = {}

    async def run(self) -> dict:
        """执行完整工作流。

        Returns:
            最终执行结果摘要
        """
        if self.session.status == "running":
            return {"error": "工作流已在运行中"}

        # 初始化
        self.session.status = "running"
        await self._broadcast_status()

        # 执行 DAG 调度（同步方法）
        try:
            self.dag_scheduler.schedule()
        except ValueError as e:
            self.session.status = "error"
            self.session.error_message = str(e)
            await self._broadcast_status()
            return {"error": str(e)}

        # 逐轮执行
        while True:
            async with self._round_lock:
                next_round = self.dag_scheduler.get_next_round()

            if next_round is None:
                # 全部完成
                self.session.status = "completed"
                self.session.updated_at = asyncio.get_running_loop().time()
                await self._broadcast_status()
                return self._get_result()

            # 本轮专家
            current_round = self.session.current_round
            self.session.current_round = current_round + 1

            # 检查是否需要用户确认
            if self.config.mode == "confirm" and self._needs_confirmation(next_round):
                self.session.status = "waiting_user"
                self.session.updated_at = asyncio.get_running_loop().time()
                await self._broadcast_status()

                # 等待用户确认（通过外部接口恢复）
                return {
                    "action": "waiting_user",
                    "workflow_id": self.session.workflow_id,
                    "next_experts": next_round,
                    "message": f"专家 {', '.join(next_round)} 准备就绪，请确认是否继续",
                }

            # 执行本轮并行任务
            self.session.status = "running"
            await self._execute_round(next_round, current_round)

        # 意外退出
        self.session.status = "error"
        self.session.error_message = "工作流异常退出"
        await self._broadcast_status()
        return {"error": "工作流异常退出"}

    def _needs_confirmation(self, experts: list[str]) -> bool:
        """判断是否需要在执行前等待用户确认。"""
        # 简单规则：planner 完成后需要确认，programmer 开始前需要确认
        confirmation_experts = {"planner", "programmer"}
        return any(e in confirmation_experts for e in experts)

    async def _execute_round(self, experts: list[str], round_num: int) -> None:
        """执行一轮并行任务。

        Args:
            experts: 本轮可并行执行的专家ID列表
            round_num: 轮次编号
        """
        # 标记为运行中
        for eid in experts:
            self.dag_scheduler.mark_running(eid)
            await self._broadcast_expert_status(eid, "running", round_num)

        # 并行执行（使用 asyncio.gather）
        tasks = []
        for eid in experts:
            agent_func = self.agent_map.get(eid)
            if agent_func:
                task = asyncio.create_task(self._run_single_expert(eid, agent_func))
                tasks.append(task)

        # 等待所有任务完成
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for eid, result in zip(experts, results):
                if isinstance(result, Exception):
                    self.dag_scheduler.mark_error(eid, str(result))
                    self.session.expert_results[eid] = {
                        "status": "error",
                        "error": str(result),
                    }
                    # 🔴 Wiki 错误记录：任务执行失败时自动记录
                    await self._record_error_to_wiki(eid, str(result), round_num)
                    await self._broadcast_expert_status(eid, "error", round_num)
                elif isinstance(result, dict):
                    self.dag_scheduler.mark_done(eid)
                    self.session.expert_results[eid] = {
                        "status": "done",
                        "output": result.get("result", ""),
                    }
                    await self._broadcast_expert_status(eid, "done", round_num)
                else:
                    self.dag_scheduler.mark_done(eid)
                    self.session.expert_results[eid] = {
                        "status": "done",
                        "output": str(result) if result else "",
                    }
                    await self._broadcast_expert_status(eid, "done", round_num)

    async def _record_error_to_wiki(self, expert_id: str, error_msg: str, round_num: int) -> None:
        """记录错误到 LLM Wiki（失败时自动记录）。"""
        try:
            from sqlalchemy.ext.asyncio import AsyncSession

            from app.models.wiki import ErrorType
            from app.services.event_bus import Event
            from app.services.wiki_service import LlmWikiService

            # 从 EventBus 获取数据库（EventBus 持有 db_session）
            db = getattr(self.event_bus, 'db', None)

            if db is None or not isinstance(db, AsyncSession):
                logger.warning(f"[Wiki] 无法获取数据库 session，跳过错误记录: {error_msg}")
                # 降级：通过 EventBus 异步记录
                await self.event_bus.emit(Event(
                    type="wiki_error",
                    project_id=self.session.project_id,
                    data={
                        "expert_id": expert_id,
                        "error_msg": error_msg,
                        "round": round_num,
                        "workflow_id": self.session.workflow_id,
                    },
                ))
                return

            service = LlmWikiService(db)

            # 根据错误类型分类
            error_type = ErrorType.OTHER
            error_lower = error_msg.lower()
            if "syntax" in error_lower or "unexpected" in error_lower or "indent" in error_lower:
                error_type = ErrorType.SYNTAX
            elif "security" in error_lower or "vulnerability" in error_lower or "xss" in error_lower or "injection" in error_lower:
                error_type = ErrorType.SECURITY
            elif "timeout" in error_lower or "performance" in error_lower or "slow" in error_lower:
                error_type = ErrorType.PERFORMANCE
            elif "api" in error_lower or "endpoint" in error_lower or "http" in error_lower or "httperror" in error_lower:
                error_type = ErrorType.API_INTEGRATION
            elif "database" in error_lower or "sql" in error_lower or "query" in error_lower:
                error_type = ErrorType.DATABASE
            elif "logic" in error_lower or "wrong" in error_lower or "incorrect" in error_lower:
                error_type = ErrorType.LOGIC

            await service.record_error(
                error_title=f"[{expert_id.upper()}] R{round_num}: {error_msg[:80]}",
                error_description=error_msg[:500],
                fix_description="系统自动记录，建议检查错误日志并参考 Wiki 推荐修复方案。",
                error_type=error_type,
                related_agent=expert_id,
                related_workflow_id=self.session.workflow_id,
                project_id=self.session.project_id,
                tags=["auto-recorded", f"round-{round_num}"],
                severity_score=0.7,
            )
            logger.info(f"[Wiki] 已记录错误: {expert_id} | {error_msg[:60]}...")

        except Exception as e:
            logger.warning(f"[Wiki] 记录失败: {e}")
            # 即使 Wiki 记录失败也不影响工作流继续

    async def _run_single_expert(
        self,
        expert_id: str,
        agent_func: Callable,
    ) -> dict:
        """执行单个专家任务 — 支持提问/回答。"""
        # 获取项目上下文字典
        context = {
            "previous_results": {
                k: v.get("output", "")
                for k, v in self.session.expert_results.items()
            }
        }

        # P1: 存储当前待回答问题，用于回答接口
        self._current_question[expert_id] = None

        try:
            # 调用 Agent.run(project_id, task, context)
            if asyncio.iscoroutinefunction(agent_func):
                result = await agent_func(
                    project_id=self.config.project_id,
                    task=f"执行 {expert_id} 角色任务",
                    context=context,
                )
            else:
                result = agent_func(
                    project_id=self.config.project_id,
                    task=f"执行 {expert_id} 角色任务",
                    context=context,
                )

            return result

        except Exception as e:
            # P1: 捕获 UserQuestionError — Agent 需要用户回答
            from app.services.agent_coordinator import UserQuestionError

            if isinstance(e, UserQuestionError):
                return await self._handle_question(expert_id, context, e)

            raise

    # === P1: 问答处理 ===

    async def _handle_question(
        self,
        expert_id: str,
        context: dict,
        error: "UserQuestionError",
    ) -> dict:
        """处理 Agent 提问 — 暂停并广播问题。"""
        from app.services.agent_coordinator import PendingQuestions

        # 使用 error 中的 question_id，如果没有则创建新问题
        qid = error.question_id

        # 创建问题（如果还不存在）
        q = await PendingQuestions.get_question(qid)
        if q is None:
            # 从 error 中获取信息创建问题
            q = await PendingQuestions.create_question(
                self.session.workflow_id,
                expert_id,
                str(error),
                [],  # 默认无选项，前端可自定义
                context,
            )

        # 存储当前问题 ID，供 answer_question API 使用
        self._current_question[expert_id] = q.question_id

        # 暂停工作流
        self.session.status = "waiting_question"
        self.session.updated_at = asyncio.get_running_loop().time()
        await self._broadcast_status()

        # 广播问题到 WebSocket
        await self.event_bus.emit(Event(
            type="agent_question",
            project_id=self.session.project_id,
            data={
                "agent": expert_id,
                "question_id": q.question_id,
                "question": q.question,
                "options": q.options,
                "allow_custom": True,
            },
        ))

        # 等待用户回答（通过 submit_question API 触发）
        # 使用 long-poll 方式等待答案
        answer = await self._wait_for_answer(q.question_id, timeout=300)

        # 清理问题
        await PendingQuestions.cleanup(q.question_id)

        if answer is None:
            # 超时，使用默认答案
            answer = "默认"
            logger.warning(f"Question {q.question_id} timeout, using default")

        # 将答案注入上下文，继续执行
        context["user_answer"] = answer

        # 重新执行当前 Agent（带上用户答案）
        agent_func_wrapped = self.agent_map.get(expert_id)
        if agent_func_wrapped:
            result = await agent_func_wrapped(
                project_id=self.config.project_id,
                task=f"执行 {expert_id} 角色任务（已回答用户问题）",
                context=context,
            )
            return result

        return {"error": f"Agent {expert_id} not found after question"}

    async def resume(self) -> dict:
        """恢复工作流（用户确认后继续执行）。

        Returns:
            恢复后的执行结果或等待状态
        """
        if self.session.status != "waiting_user":
            return {"error": f"工作流状态不是等待用户确认: {self.session.status}"}

        self.session.status = "running"
        await self._broadcast_status()

        # 获取下一轮并继续
        async with self._round_lock:
            next_round = self.dag_scheduler.get_next_round()

        if next_round is None:
            self.session.status = "completed"
            await self._broadcast_status()
            return self._get_result()

        self.session.current_round += 1
        await self._execute_round(next_round, self.session.current_round - 1)
        return self._get_result()

    def pause(self) -> dict:
        """暂停工作流。"""
        self.session.status = "paused"
        self.session.updated_at = asyncio.get_running_loop().time()
        return {
            "action": "paused",
            "workflow_id": self.session.workflow_id,
            "message": "工作流已暂停",
        }

    def get_status(self) -> dict:
        """获取当前工作流状态。"""
        dag_summary = self.dag_scheduler.get_summary() if self.dag_scheduler else {}
        return {
            "workflow_id": self.session.workflow_id,
            "project_id": self.session.project_id,
            "status": self.session.status,
            "current_round": self.session.current_round,
            "expert_results": self.session.expert_results,
            "dag_summary": dag_summary,
            "created_at": self.session.created_at,
            "updated_at": self.session.updated_at,
        }

    async def _broadcast_status(self) -> None:
        """广播工作流状态更新。"""
        await self.event_bus.emit(Event(
            type="workflow_status",
            project_id=self.session.project_id,
            data={
                "workflow_id": self.session.workflow_id,
                "status": self.session.status,
                "current_round": self.session.current_round,
                "expert_results": self.session.expert_results,
            },
        ))

    async def _broadcast_expert_status(
        self,
        expert_id: str,
        status: str,
        round_num: int,
    ) -> None:
        """广播单个专家状态更新。"""
        await self.event_bus.emit(Event(
            type="expert_status",
            project_id=self.session.project_id,
            data={
                "expert_id": expert_id,
                "status": status,
                "round": round_num,
                "result": self.session.expert_results.get(expert_id, {}),
            },
        ),)

    def _get_result(self) -> dict:
        """获取最终执行结果。"""
        return {
            "workflow_id": self.session.workflow_id,
            "status": self.session.status,
            "total_rounds": self.session.current_round,
            "expert_results": self.session.expert_results,
        }


def create_workflow_runner(
    config: "ParallelWorkflowConfig",
    event_bus: object,
    agents: dict[str, Callable] | None = None,
    auto_inject_agents: bool = True,
) -> WorkflowRunner:
    """工厂函数：创建完整的工作流运行时。

    Args:
        config: 工作流配置
        event_bus: EventBus 实例
        agents: expert_id -> Agent 的 run 函数映射（可选）
        auto_inject_agents: 如果为 True 且 agents 未提供，自动从 AGENT_REGISTRY 注入

    Returns:
        WorkflowRunner 实例

    注意：在创建 DAGScheduler 前会自动注入专家的默认依赖。
    """
    from app.schemas.expert import get_expert
    from app.services.dag_scheduler import DAGScheduler

    # 注入默认依赖（如果配置中的 custom_dependencies 为空）
    for ec in config.experts:
        if not ec.custom_dependencies:
            expert = get_expert(ec.expert_id)
            if expert:
                ec.custom_dependencies = expert.default_dependencies

    # 创建 DAG 调度器（此时 experts 已含完整依赖）
    scheduler = DAGScheduler(config.experts)

    # Agent 自动注入
    final_agent_map: dict[str, Callable] = agents or {}
    if auto_inject_agents and not agents:
        from app.services.agents import AGENT_REGISTRY
        for ec in config.experts:
            eid = ec.expert_id
            if eid in AGENT_REGISTRY and eid not in final_agent_map:
                agent_cls = AGENT_REGISTRY[eid]
                agent = agent_cls()

                async def run_func(
                    project_id: int,
                    task: str,
                    context: dict | None = None,
                    a=agent,
                ) -> dict:
                    return await a.run(project_id, task, context)

                final_agent_map[eid] = run_func

    return WorkflowRunner(
        config=config,
        dag_scheduler=scheduler,
        agent_map=final_agent_map,
        event_bus=event_bus,
    )
