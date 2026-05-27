"""多专家并行工作流 API 端点。

端点设计:
GET  /api/workflows                    - 列出工作流
POST /api/workflows                    - 创建工作流（配置+专家选择）
GET  /api/workflows/{workflow_id}      - 获取工作流详情
POST /api/workflows/{workflow_id}/start - 启动工作流
POST /api/workflows/{workflow_id}/pause  - 暂停工作流
POST /api/workflows/{workflow_id}/resume - 恢复工作流
DELETE /api/workflows/{workflow_id}     - 删除工作流

GET /api/workflows/status              - 获取所有工作流状态（用于前端轮询/WS订阅）
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_current_user
from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.expert import (
    ExpertConfig,
    ParallelWorkflowConfig,
    ParallelWorkflowStatusOut,
    get_expert,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowDetail,
    WorkflowListOut,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.services.workflow_runner import WorkflowRunner

router = APIRouter(tags=["多专家工作流"])

# 运行时缓存（项目ID -> WorkflowRunner）
# 生产环境应使用 StateStore/Redis 持久化
_workflow_runners: dict[str, "WorkflowRunner"] = {}


@router.get("/", response_model=WorkflowListOut)
async def list_workflows(
    project_id: int | None = None,
    current_user: dict = Depends(get_current_user),
):
    """列出工作流（支持按项目过滤）— 返回运行时缓存中的实时状态。"""
    items = []
    for wf_id, data in _workflow_runners.items():
        config = data.get("config")
        if project_id is not None and (config is None or config.project_id != project_id):
            continue
        rounds = data.get("rounds", [])
        items.append({
            "workflow_id": wf_id,
            "project_id": config.project_id if config else None,
            "status": data.get("status", "idle"),
            "experts": [
                {"expert_id": ec.expert_id, "enabled": ec.enabled}
                for ec in (config.experts if config else [])
            ],
            "execution_rounds": rounds,
            "current_round": data.get("current_round", 0),
            "complexity": _estimate_complexity(rounds),
        })
    return {"items": items, "total": len(items)}


@router.post("/", response_model=WorkflowDetail)
async def create_workflow(
    config: WorkflowCreate,
    user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建工作流（配置多专家并行）。

    前端传递:
    - project_id
    - experts: 专家ID列表 + 自定义依赖
    - mode: "parallel" | "sequential" | "confirm"
    - auto_start: 是否自动启动

    后端返回:
    - workflow_id
    - DAG 调度结果（执行轮次）
    - 初始状态
    """
    # 验证项目存在
    project = await db.get(Project, config.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {config.project_id}",
        )

    # 验证专家ID
    for expert_id in config.experts:
        if not get_expert(expert_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未知的专家ID: {expert_id}",
            )

    # 构建 ParallelWorkflowConfig
    expert_configs = [
        ExpertConfig(
            expert_id=eid,
            enabled=True,
            custom_dependencies=config.custom_deps.get(eid, []),
        )
        for eid in config.experts
    ]

    workflow_config = ParallelWorkflowConfig(
        project_id=config.project_id,
        experts=expert_configs,
        mode=config.mode or "parallel",
        auto_start=config.auto_start or False,
    )

    # 构建 DAG 并验证
    from app.services.dag_scheduler import DAGScheduler

    scheduler = DAGScheduler(expert_configs)
    try:
        rounds = scheduler.schedule()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DAG 依赖环检测失败: {str(e)}",
        )

    workflow_id = f"wf-{uuid.uuid4().hex[:12]}"

    # 缓存调度器（实际运行时需持久化）
    _workflow_runners[workflow_id] = {
        "scheduler": scheduler,
        "config": workflow_config,
        "status": "idle",
        "rounds": rounds,
        "current_round": 0,
    }

    # 如果 auto_start=True，直接启动工作流
    auto_started = False
    if config.auto_start:
        try:
            from app.services.agents import AGENT_REGISTRY, get_agent_run_func
            agent_map = {}
            for expert_config in expert_configs:
                eid = expert_config.expert_id
                if eid in AGENT_REGISTRY:
                    agent_map[eid] = await get_agent_run_func(eid)

            from app.services.event_bus import event_bus
            from app.services.workflow_runner import create_workflow_runner

            runner = create_workflow_runner(
                config=workflow_config,
                agents=agent_map,
                event_bus=event_bus,
            )
            runner_task = asyncio.create_task(runner.run())

            _workflow_runners[workflow_id] = {
                "scheduler": scheduler,
                "config": workflow_config,
                "status": "running",
                "rounds": rounds,
                "current_round": 0,
                "runner": runner,
                "task": runner_task,
            }
            auto_started = True
        except Exception as e:
            logger.warning(f"自动启动失败: {e}, 降级为手动启动")

    return WorkflowDetail(
        workflow_id=workflow_id,
        project_id=config.project_id,
        status="running" if auto_started else "idle",
        experts={
            eid: {
                "expert_id": eid,
                "enabled": True,
                "dependencies": config.custom_deps.get(eid, []),
            }
            for eid in config.experts
        },
        execution_rounds=rounds,
        current_round=0,
        complexity=_estimate_complexity(rounds),
        auto_started=auto_started,
    )


@router.post("/{workflow_id}/start", response_model=ParallelWorkflowStatusOut)
async def start_workflow(
    workflow_id: str,
    user: User = Depends(require_current_user),
):
    """启动工作流（异步执行）。

    实际实现:
    1. 从 StateStore 加载工作流状态
    2. 创建 WorkflowRunner
    3. 后台异步启动 asyncio.create_task(run)
    4. 立即返回状态
    """
    runner_data = _workflow_runners.get(workflow_id)
    if not runner_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    # 检查状态
    if runner_data["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流已在运行中",
        )

    # 获取 Agent 映射（使用 AGENT_REGISTRY）
    from app.services.agents import AGENT_REGISTRY, get_agent_run_func

    agent_map = {}
    for expert_config in runner_data["config"].experts:
        eid = expert_config.expert_id
        if eid in AGENT_REGISTRY:
            try:
                agent_map[eid] = await get_agent_run_func(eid)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法初始化 Agent '{eid}': {str(e)}",
                )

    if not agent_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可用的 Agent（请检查 LLM 配置）",
        )

    # 获取 EventBus
    from app.services.event_bus import event_bus

    # 创建并启动运行时
    from app.services.workflow_runner import create_workflow_runner

    runner = create_workflow_runner(
        config=runner_data["config"],
        agents=agent_map,
        event_bus=event_bus,
    )

    # 后台异步启动
    runner_task = asyncio.create_task(runner.run())

    # 缓存 runner（实际用 StateStore）
    _workflow_runners[workflow_id]["runner"] = runner
    _workflow_runners[workflow_id]["task"] = runner_task
    _workflow_runners[workflow_id]["status"] = "running"

    return _runner_to_status_out(runner)


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    user: User = Depends(require_current_user),
):
    """暂停工作流。"""
    runner_data = _workflow_runners.get(workflow_id)
    if not runner_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    runner = runner_data.get("runner")
    if not runner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流未启动",
        )

    result = runner.pause()
    runner_data["status"] = "paused"
    return result


@router.post("/{workflow_id}/resume", response_model=ParallelWorkflowStatusOut)
async def resume_workflow(
    workflow_id: str,
    user: User = Depends(require_current_user),
):
    """恢复工作流（用户确认后继续执行）。"""
    runner_data = _workflow_runners.get(workflow_id)
    if not runner_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    runner = runner_data.get("runner")
    if not runner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流未启动",
        )

    result = await runner.resume()
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    runner_data["status"] = runner.session.status
    return _runner_to_status_out(runner)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user: User = Depends(require_current_user),
):
    """删除工作流。"""
    if workflow_id not in _workflow_runners:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    runner_data = _workflow_runners.pop(workflow_id)

    # 取消后台任务
    task = runner_data.get("task")
    if task and not task.done():
        task.cancel()

    return {"message": f"工作流 {workflow_id} 已删除"}


@router.get("/status", response_model=dict)
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取工作流状态详情（用于前端轮询/WS监听）。"""
    runner_data = _workflow_runners.get(workflow_id)
    if not runner_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    runner = runner_data.get("runner")
    if runner:
        return runner.get_status()

    config = runner_data.get("config")
    return {
        "workflow_id": workflow_id,
        "project_id": config.project_id if config else None,
        "status": runner_data["status"],
        "experts": [
            {"expert_id": ec.expert_id, "enabled": ec.enabled}
            for ec in (config.experts if config else [])
        ],
        "execution_rounds": runner_data.get("rounds", []),
        "current_round": runner_data.get("current_round", 0),
        "complexity": _estimate_complexity(runner_data.get("rounds", [])),
    }


# === 工具函数 ===

def _runner_to_status_out(runner: "WorkflowRunner") -> ParallelWorkflowStatusOut:
    """将 WorkflowRunner 状态转换为 API 响应。"""
    session = runner.session
    dag = runner.dag_scheduler

    # 专家状态详情
    expert_details = {}
    for expert_config in (session.config or {}).get("experts", []):
        eid = expert_config["expert_id"]
        result = session.expert_results.get(eid, {})
        expert_details[eid] = {
            "role": eid,
            "name": get_expert(eid).name if get_expert(eid) else eid,
            "status": dag.get_status(eid),
            "task": result.get("task", ""),
            "progress": 100 if result.get("status") == "done" else 0,
            "output_preview": result.get("output", "")[:100] if result.get("output") else "",
            "dependencies": expert_config.get("custom_dependencies", []),
            "blocked_by": None,
            "error_message": result.get("error"),
        }

    return ParallelWorkflowStatusOut(
        workflow_id=session.workflow_id,
        project_id=session.project_id,
        status=session.status,
        experts=expert_details,
        execution_rounds=dag.execution_rounds,
        current_round=session.current_round,
        complexity=_estimate_complexity(dag.execution_rounds),
    )


def _estimate_complexity(rounds: list[list[str]]) -> str:
    """估算工作流复杂度。"""
    total_experts = sum(len(r) for r in rounds)
    if total_experts <= 2:
        return "简单"
    elif total_experts <= 5:
        return "中等"
    else:
        return "复杂"


@router.post("/{workflow_id}/question-answer", response_model=QuestionAnswerResponse)
async def submit_question_answer(
    workflow_id: str,
    payload: QuestionAnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    """提交用户对 Agent 提问的回答。

    前端传递:
    - question_id: 问题ID（由 agent_question WebSocket 消息中的 data.question_id 提供）
    - answer: 选项索引（int）或自定义文本（str）

    后端处理:
    1. 通过 AgentCoordinator.submit_answer 提交答案
    2. PendingQuestions.resolve_question 将答案写入 StateStore
    3. 触发 PendingQuestions._pending_events 通知等待中的 Agent 协程
    4. Agent 恢复执行，应用用户反馈
    """
    from app.services.agent_coordinator import coordinator
    success = await coordinator.submit_answer(payload.question_id, str(payload.answer))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"问题不存在或已过期: {payload.question_id}",
        )

    return QuestionAnswerResponse(
        success=True,
        question_id=payload.question_id,
        message="答案已提交，工作流将恢复执行",
    )
