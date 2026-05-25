"""Agent 协调服务 — 支持 Agent 主动向用户提问的工作流控制。

核心能力：
- Agent 可在执行过程中暂停并向用户提问
- 等待用户响应后继续执行
- 支持暂停/恢复/中断工作流
- 通过 EventBus 解耦对 WebSocket 的直接依赖
- 🔴 P2 修复：PendingQuestions 迁移到 StateStore，支持进程重启后恢复
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum

from app.schemas.enums import AgentStatus
from app.schemas.game_design_doc import GameDesignDoc
from app.services.agents import get_agent
from app.services.event_bus import Event, event_bus
from app.services.state_store import get_state_store

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """工作流状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


@dataclass
class AgentQuestion:
    """Agent 提问数据结构"""
    question_id: str
    agent: str
    question: str
    options: list[str] = field(default_factory=list)
    task_context: dict = field(default_factory=dict)  # 执行上下文，用于恢复


@dataclass
class AgentState:
    """单个 Agent 的执行状态"""
    role: str
    name: str
    status: AgentStatus = AgentStatus.IDLE
    task: str = ""
    progress: int = 0  # 0-100
    output_preview: str = ""
    dependencies: list[str] = field(default_factory=list)
    blocked_by: str | None = None
    error_message: str | None = None
    started_at: float | None = None


class PendingQuestions:
    """待回答问题队列 — 使用 StateStore 存储，支持进程重启后恢复。

    🔴 P2 修复：之前使用类变量 (_questions/_responses/_events) 存储在内存中，
    进程重启后丢失。现在迁移到 StateStore，数据持久化。

    设计说明：
    - asyncio.Event 仍然用于跨协程等待/通知（只能进程内存）
    - StateStore 用于持久化存储问题元数据和响应
    - 进程重启时，StateStore 中的数据自动恢复
    - 但 asyncio.Event 无法跨进程恢复，因此需要初始化空 Event
    - 超时自动清理，防止脏数据堆积
    """
    _state_store = None  # 延迟初始化，避免循环导入

    _pending_events: dict[str, asyncio.Event] = {}  # 进程内存 Event，跨协程通知用

    @classmethod
    def _ensure_store(cls):
        """确保 StateStore 已初始化。"""
        if cls._state_store is None:
            cls._state_store = get_state_store()

    @classmethod
    async def create_question(
        cls,
        workflow_id: str,
        agent: str,
        question: str,
        options: list[str],
        task_context: dict,
    ) -> AgentQuestion:
        """创建问题并返回。"""
        cls._ensure_store()
        qid = f"{workflow_id}_{uuid.uuid4().hex[:8]}"
        q = AgentQuestion(
            question_id=qid,
            agent=agent,
            question=question,
            options=options,
            task_context=task_context,
        )
        await cls._state_store.set(f"question:{qid}", q)
        # 初始化异步等待事件（仅在内存中）
        cls._pending_events[qid] = asyncio.Event()
        return q

    @classmethod
    async def wait_for_response(cls, question_id: str, timeout: float = 300) -> str | None:
        """等待用户响应，超时返回 None。"""
        cls._ensure_store()
        event = cls._pending_events.get(question_id)
        if event is None:
            # 🔴 P2 修复：尝试从 StateStore 恢复事件
            stored = await cls._state_store.get(f"question:{question_id}")
            if stored is None:
                return None
            event = asyncio.Event()
            cls._pending_events[question_id] = event

        try:
            async with asyncio.timeout(timeout):
                await event.wait()
                responses = await cls._responses()
                return responses.get(question_id)
        except asyncio.TimeoutError:
            await cls.cleanup(question_id)
            return None

    @classmethod
    async def _responses(cls) -> dict[str, str]:
        """获取响应字典（从 StateStore 读取）。"""
        cls._ensure_store()
        keys = await cls._state_store.keys("response:*")
        result = {}
        for k in keys:
            v = await cls._state_store.get(k)
            if v is not None:
                result[k[len("response:"):]] = v
        return result

    @classmethod
    async def resolve_question(cls, question_id: str, answer: str) -> bool:
        """提交用户响应。"""
        cls._ensure_store()
        stored_q = await cls._state_store.get(f"question:{question_id}")
        if stored_q is None:
            return False
        await cls._state_store.set(f"response:{question_id}", answer)
        # 🔴 P2: 触发进程内存事件
        event = cls._pending_events.get(question_id)
        if event is not None:
            event.set()
        return True

    @classmethod
    async def get_question(cls, question_id: str) -> AgentQuestion | None:
        """获取问题。"""
        cls._ensure_store()
        stored = await cls._state_store.get(f"question:{question_id}")
        if stored is None:
            return None
        if isinstance(stored, AgentQuestion):
            return stored
        # 如果存储的是 dict（从 StateStore 读取时），需要反序列化
        if isinstance(stored, dict):
            return AgentQuestion(**stored)
        return None

    @classmethod
    async def cleanup(cls, question_id: str) -> None:
        """清理问题（删除持久化数据和内存事件）。"""
        cls._ensure_store()
        await cls._state_store.delete(f"question:{question_id}")
        await cls._state_store.delete(f"response:{question_id}")
        cls._pending_events.pop(question_id, None)


@dataclass
class WorkflowContext:
    """工作流执行上下文"""
    workflow_id: str
    project_id: int
    status: WorkflowStatus = WorkflowStatus.IDLE
    agents: dict[str, AgentState] = field(default_factory=dict)
    doc: GameDesignDoc | None = None
    previous_results: str = ""
    current_question_id: str | None = None


class AgentCoordinator:
    """Agent 协调器 — 管理多 Agent 工作流，支持主动提问"""

    def __init__(self):
        # 活跃工作流: {workflow_id: WorkflowContext}
        self._workflows: dict[str, WorkflowContext] = {}
        # 全局协调器实例
        AgentCoordinator._instance = self

    @property
    def workflows(self) -> dict[str, WorkflowContext]:
        return self._workflows

    async def start_workflow(
        self,
        project_id: int,
        doc: GameDesignDoc,
        agent_roles: list[str],
    ) -> WorkflowContext:
        """启动新的工作流"""
        workflow_id = uuid.uuid4().hex[:8]
        ctx = WorkflowContext(
            workflow_id=workflow_id,
            project_id=project_id,
            doc=doc,
        )

        # 初始化 Agent 状态
        for role in agent_roles:
            agent = get_agent(role)
            ctx.agents[role] = AgentState(
                role=role,
                name=agent.name if agent else role,
            )

        # 设置依赖关系
        self._setup_dependencies(ctx, agent_roles)

        self._workflows[workflow_id] = ctx
        ctx.status = WorkflowStatus.RUNNING

        await event_bus.emit(Event(
            type="workflow_started",
            project_id=project_id,
            data={"workflow_id": workflow_id},
            source="agent_coordinator",
        ))
        await self._broadcast_all_agents(project_id, ctx)

        return ctx

    def _setup_dependencies(self, ctx: WorkflowContext, roles: list[str]) -> None:
        """设置 Agent 依赖关系"""
        dependency_map = {
            "planner": [],
            "architect": ["planner"],
            "programmer": ["architect", "planner"],
            "qa": ["programmer", "architect"],
        }

        for role in roles:
            deps = dependency_map.get(role, [])
            if role in ctx.agents and deps:
                ctx.agents[role].dependencies = [d for d in deps if d in roles]

    async def execute_workflow(self, ctx: WorkflowContext) -> dict:
        """执行完整工作流"""
        import time
        results = []

        for role, state in ctx.agents.items():
            # P1: 跳过已完成（DONE）的 Agent，resume 时已执行过的不会重复
            if state.status == AgentStatus.DONE:
                logger.info(f"Agent {role} already DONE, skipping")
                results.append({"agent": role, "status": "skipped"})
                continue

            # 检查是否被中断
            if ctx.status == WorkflowStatus.INTERRUPTED:
                break

            # 检查是否被阻塞
            if self._is_blocked(ctx, role):
                state.status = AgentStatus.BLOCKED
                state.blocked_by = self._get_blocker(ctx, role)
                await event_bus.emit(Event(
                    type="agent_blocked",
                    project_id=ctx.project_id,
                    data={
                        "agent": role,
                        "blocked_by": state.blocked_by,
                        "reason": f"等待 {state.blocked_by} 完成",
                    },
                    source="agent_coordinator",
                ))
                await self._broadcast_agent_state(ctx.project_id, state)
                continue

            # 执行 Agent
            state.status = AgentStatus.RUNNING
            state.started_at = time.time()
            await self._broadcast_agent_state(ctx.project_id, state)

            try:
                result = await self._run_agent(ctx, role)
                results.append(result)

                state.status = AgentStatus.DONE
                state.progress = 100
                state.output_preview = result["result"][:200] + "..." if len(result["result"]) > 200 else result["result"]

                ctx.previous_results += f"\n\n[{state.name} 结果]\n{result['result']}"

            except UserQuestionError as e:
                # Agent 需要向用户提问
                state.status = AgentStatus.WAITING_USER
                ctx.current_question_id = e.question_id
                await self._broadcast_agent_state(ctx.project_id, state)
                return {"status": "waiting_user", "question_id": e.question_id}

            except Exception as e:
                state.status = AgentStatus.ERROR
                state.error_message = str(e)
                logger.exception(f"Agent {role} execution error")
                await event_bus.emit(Event(
                    type="workflow_error",
                    project_id=ctx.project_id,
                    data={"workflow_id": ctx.workflow_id, "error": str(e)},
                    source="agent_coordinator",
                ))

            await self._broadcast_agent_state(ctx.project_id, state)

        # 工作流完成
        ctx.status = WorkflowStatus.COMPLETED
        await event_bus.emit(Event(
            type="workflow_completed",
            project_id=ctx.project_id,
            data={"workflow_id": ctx.workflow_id},
            source="agent_coordinator",
        ))

        return {
            "workflow_id": ctx.workflow_id,
            "results": results,
            "status": ctx.status.value,
        }

    async def _run_agent(self, ctx: WorkflowContext, role: str) -> dict:
        """运行单个 Agent，支持主动提问"""
        agent = get_agent(role)
        state = ctx.agents[role]

        task = self._build_task_prompt(role, ctx)
        context = {
            "design_doc": ctx.doc.model_dump() if ctx.doc else {},
            "previous_results": ctx.previous_results,
        }

        # 分段执行，实时推送输出
        result_chunks = []

        async def progress_callback(progress: int, message: str):
            state.progress = progress
            await event_bus.emit(Event(
                type="agent_progress",
                project_id=ctx.project_id,
                data={"agent": role, "progress": progress, "text": message},
                source="agent_coordinator",
            ))

        async def output_callback(chunk: str, is_final: bool):
            result_chunks.append(chunk)
            state.output_preview = "".join(result_chunks)[-200:]
            await event_bus.emit(Event(
                type="agent_output",
                project_id=ctx.project_id,
                data={"agent": role, "chunk": chunk, "is_final": is_final},
                source="agent_coordinator",
            ))

        # 检查是否需要用户确认（智能检查点）
        checkpoints = self._get_checkpoints(role, ctx)
        for checkpoint in checkpoints:
            if self._needs_confirmation(role, checkpoint, ctx):
                question = self._generate_question(role, checkpoint, ctx)
                options = self._generate_options(role, checkpoint, ctx)

                q = await PendingQuestions.create_question(
                    ctx.workflow_id, role, question, options, context
                )

                # 广播问题给用户
                await event_bus.emit(Event(
                    type="agent_question",
                    project_id=ctx.project_id,
                    data={"agent": role, "question": question, "options": options, "allow_custom": True},
                    source="agent_coordinator",
                ))

                # 等待用户响应
                answer = await PendingQuestions.wait_for_response(q.question_id)

                if answer is None:
                    # 超时，使用默认
                    answer = "默认"
                    logger.warning(f"Question {q.question_id} timeout, using default")

                await PendingQuestions.cleanup(q.question_id)

                # 应用用户反馈
                context[f"user_feedback_{checkpoint}"] = answer

        # 实际执行 Agent
        result = await agent.run(
            ctx.project_id,
            task,
            context,
            progress_callback=progress_callback,
            output_callback=output_callback,
        )

        return result

    def _get_checkpoints(self, role: str, ctx: WorkflowContext) -> list[str]:
        """获取 Agent 的检查点列表"""
        checkpoints_map = {
            "planner": ["modules", "tasks"],
            "architect": ["tech_stack", "data_model"],
            "programmer": ["code_style", "features"],
            "qa": ["test_scope", "criteria"],
        }
        return checkpoints_map.get(role, [])

    def _needs_confirmation(self, role: str, checkpoint: str, ctx: WorkflowContext) -> bool:
        """判断是否需要用户确认"""
        # 简化的启发式判断
        # 实际可以从 Agent 返回的特殊标记判断
        return False

    def _generate_question(self, role: str, checkpoint: str, ctx: WorkflowContext) -> str:
        """生成引导性问题"""
        questions = {
            "modules": "请确认模块划分方式：按功能分层还是按游戏对象划分？",
            "tasks": "任务粒度偏好：细粒度（每功能一个任务）还是粗粒度（每系统一个任务）？",
            "tech_stack": "技术栈偏好：纯 HTML5 Canvas 还是需要配合框架？",
            "data_model": "数据存储方式：使用 LocalStorage 还是纯内存？",
            "code_style": "代码风格：更注重可读性还是紧凑度？",
            "features": "功能优先级：先生成核心玩法还是完整功能？",
            "test_scope": "测试范围：仅测试核心逻辑还是全面覆盖？",
            "criteria": "验收标准：功能正确优先还是性能优先？",
        }
        return questions.get(checkpoint, f"请确认 {checkpoint} 的方案")

    def _generate_options(self, role: str, checkpoint: str, ctx: WorkflowContext) -> list[str]:
        """生成选项"""
        options_map = {
            "modules": ["按功能分层", "按游戏对象", "混合方式"],
            "tasks": ["细粒度", "中等粒度", "粗粒度"],
            "tech_stack": ["纯 Canvas", "Phaser.js", "PixiJS"],
            "data_model": ["LocalStorage", "纯内存", "IndexedDB"],
            "code_style": ["可读性优先", "紧凑优先", "平衡"],
            "features": ["核心玩法优先", "完整功能", "按优先级"],
            "test_scope": ["仅核心逻辑", "中等覆盖", "全面覆盖"],
            "criteria": ["功能正确", "性能优先", "平衡"],
        }
        return options_map.get(checkpoint, ["选项A", "选项B", "自定义"])

    def _build_task_prompt(self, role: str, ctx: WorkflowContext) -> str:
        """构建 Agent 任务提示"""
        base = ""
        if ctx.doc:
            base = (
                f"游戏类型：{ctx.doc.game_type}\n"
                f"主角：{ctx.doc.protagonist}\n"
                f"核心玩法：{ctx.doc.core_gameplay}\n"
                f"敌人/收集物：{ctx.doc.enemies_collectibles}\n"
                f"胜利条件：{ctx.doc.win_condition}"
            )

        prompts = {
            "planner": f"请根据以下设计文档拆分模块和任务：\n{base}",
            "architect": f"请根据以下设计文档设计技术架构：\n{base}",
            "programmer": f"请根据以下设计文档生成完整的游戏代码（HTML5 Canvas）：\n{base}",
            "qa": f"请为以下游戏生成测试用例并检查代码质量：\n{base}",
        }
        return prompts.get(role, base)

    def _is_blocked(self, ctx: WorkflowContext, role: str) -> bool:
        """检查 Agent 是否被阻塞"""
        state = ctx.agents.get(role)
        if not state:
            return False

        for dep in state.dependencies:
            dep_state = ctx.agents.get(dep)
            if dep_state and dep_state.status != AgentStatus.DONE:
                return True
        return False

    def _get_blocker(self, ctx: WorkflowContext, role: str) -> str | None:
        """获取阻塞来源"""
        state = ctx.agents.get(role)
        if not state:
            return None

        for dep in state.dependencies:
            dep_state = ctx.agents.get(dep)
            if dep_state and dep_state.status != AgentStatus.DONE:
                return dep
        return None

    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        ctx = self._workflows.get(workflow_id)
        if not ctx or ctx.status != WorkflowStatus.RUNNING:
            return False

        ctx.status = WorkflowStatus.PAUSED
        await event_bus.emit(Event(
            type="workflow_paused",
            project_id=ctx.project_id,
            data={"workflow_id": workflow_id},
            source="agent_coordinator",
        ))
        return True

    async def resume_workflow(self, workflow_id: str) -> dict:
        """恢复工作流"""
        ctx = self._workflows.get(workflow_id)
        if not ctx or ctx.status not in [WorkflowStatus.PAUSED, WorkflowStatus.WAITING_USER]:
            return {"status": "error", "message": "Cannot resume workflow"}

        ctx.status = WorkflowStatus.RUNNING

        await event_bus.emit(Event(
            type="workflow_resumed",
            project_id=ctx.project_id,
            data={"workflow_id": workflow_id},
            source="agent_coordinator",
        ))

        return await self.execute_workflow(ctx)

    async def interrupt_workflow(self, workflow_id: str) -> bool:
        """中断工作流"""
        ctx = self._workflows.get(workflow_id)
        if not ctx:
            return False

        ctx.status = WorkflowStatus.INTERRUPTED

        await event_bus.emit(Event(
            type="workflow_interrupted",
            project_id=ctx.project_id,
            data={"workflow_id": workflow_id},
            source="agent_coordinator",
        ))
        return True

    async def submit_answer(self, question_id: str, answer: str) -> bool:
        """提交用户对问题的回答"""
        return await PendingQuestions.resolve_question(question_id, answer)

    def get_workflow(self, workflow_id: str) -> WorkflowContext | None:
        """获取工作流上下文"""
        return self._workflows.get(workflow_id)

    async def _broadcast_agent_state(self, project_id: int, state: AgentState) -> None:
        """广播单个 Agent 状态"""
        await event_bus.emit(Event(
            type="agent_status",
            project_id=project_id,
            data={
                "role": state.role,
                "name": state.name,
                "status": state.status.value,
                "task": state.task,
                "progress": state.progress,
                "output_preview": state.output_preview,
                "dependencies": state.dependencies,
                "blocked_by": state.blocked_by,
                "error_message": state.error_message,
            },
            source="agent_coordinator",
        ))

    async def _broadcast_all_agents(self, project_id: int, ctx: WorkflowContext) -> None:
        """广播所有 Agent 状态"""
        for state in ctx.agents.values():
            await self._broadcast_agent_state(project_id, state)


class UserQuestionError(Exception):
    """用户提问异常 — 用于 Agent 执行中暂停并等待用户"""
    def __init__(self, question_id: str, message: str = "需要用户确认"):
        self.question_id = question_id
        super().__init__(message)


# 全局协调器实例
coordinator = AgentCoordinator()
