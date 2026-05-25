"""DAG 调度器 — 基于 Kahn 算法的多专家并行调度。

支持:
- 拓扑排序计算执行顺序
- 每轮并行专家分组
- 依赖状态检查与阻塞

使用 Kahn 拓扑排序算法，将专家按依赖关系分组，
每轮可以同时执行的专家组成一个执行轮次（round）。

示例 DAG:

        planner
       /       \\
    architect   qa
       \\       /
     programmer
       \\      /
        devops

执行顺序:
- Round 0: [planner]           (无依赖)
- Round 1: [architect]         (planner 完成后)
- Round 2: [programmer, qa]    (architect 完成后同时执行)
- Round 3: [devops]            (programmer 完成后)
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.expert import ExpertConfig

# 专家状态常量
STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WAITING_USER = "waiting_user"
STATUS_BLOCKED = "blocked"


@dataclass
class DAGNode:
    """DAG 中的一个节点（专家）。"""
    expert_id: str
    dependencies: list[str]  # 依赖的专家ID列表
    status: str = STATUS_IDLE
    depends_on: list[str] = field(default_factory=list)  # 反向依赖（谁依赖我）
    remaining_deps: list[str] = field(default_factory=list)  # 待完成的依赖


class DAGScheduler:
    """基于 Kahn 算法的 DAG 调度器。

    使用 Kahn 拓扑排序算法，将专家按依赖关系分组，
    每轮可以同时执行的专家组成一个执行轮次（round）。
    """

    def __init__(self, experts: list["ExpertConfig"]):
        """初始化 DAG 调度器。

        Args:
            experts: 工作流中的专家配置列表（已注入默认依赖）
        """
        self.nodes: dict[str, DAGNode] = {}
        self.execution_rounds: list[list[str]] = []
        self._is_scheduled = False

        # 构建节点
        for ec in experts:
            self.nodes[ec.expert_id] = DAGNode(
                expert_id=ec.expert_id,
                dependencies=ec.custom_dependencies or [],
                remaining_deps=list(ec.custom_dependencies or []),
            )

        # 构建反向依赖图
        for node in self.nodes.values():
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    self.nodes[dep_id].depends_on.append(node.expert_id)

    def schedule(self) -> list[list[str]]:
        """执行 Kahn 拓扑排序，返回每轮可并行执行的专家ID列表。

        Returns:
            按执行轮次分组的专家ID列表，每轮内的专家可以并行执行
        """
        # 重置状态
        for node in self.nodes.values():
            node.status = STATUS_IDLE
            node.remaining_deps = list(node.dependencies)

        self.execution_rounds = []
        rounds: list[list[str]] = []

        # 复制剩余依赖用于计算
        remaining: dict[str, list[str]] = {
            eid: list(node.dependencies) for eid, node in self.nodes.items()
        }

        # 计算每个节点的入度（剩余未满足的依赖数）
        in_degree: dict[str, int] = {
            eid: len(deps) for eid, deps in remaining.items()
        }

        # 第一轮：入度为0的节点
        queue = deque([eid for eid, d in in_degree.items() if d == 0])

        while queue:
            # 当前轮次所有可以并行执行的专家
            round_experts: list[str] = []
            level_size = len(queue)

            for _ in range(level_size):
                eid = queue.popleft()
                round_experts.append(eid)

            rounds.append(sorted(round_experts))  # 排序便于调试和UI展示

            # 处理本轮完成的所有专家
            for eid in round_experts:
                # 减少依赖此专家的节点入度
                for dependent_id in self.nodes[eid].depends_on:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)

        # 检查是否有环（节点未全部访问）
        if sum(len(r) for r in rounds) != len(self.nodes):
            raise ValueError("DAG 中存在环，无法完成拓扑排序")

        self.execution_rounds = rounds
        self._is_scheduled = True
        return rounds

    def get_next_round(self) -> list[str] | None:
        """获取下一个可执行的专家轮次（只返回未完成的）。

        Returns:
            下一个可并行执行的专家ID列表，或 None（无剩余节点）
        """
        if not self._is_scheduled:
            self.schedule()

        # 找到第一个全部未完成的轮次
        for round_experts in self.execution_rounds:
            unfinished = [
                eid for eid in round_experts
                if self.nodes[eid].status not in (STATUS_DONE, STATUS_ERROR)
            ]
            if unfinished:
                return unfinished

        return None  # 全部完成

    def get_blocked_experts(self) -> list[str]:
        """获取因依赖未完成而阻塞的专家。"""
        blocked = []
        for eid, node in self.nodes.items():
            if node.status == STATUS_IDLE:
                unfinished_deps = [
                    dep for dep in node.remaining_deps
                    if self.nodes[dep].status not in (STATUS_DONE,)
                ]
                if unfinished_deps:
                    blocked.append(eid)
        return blocked

    def mark_running(self, expert_id: str) -> None:
        """标记专家为运行中。"""
        if expert_id in self.nodes:
            self.nodes[expert_id].status = STATUS_RUNNING

    def mark_done(self, expert_id: str) -> None:
        """标记专家为已完成，并更新其依赖的阻塞状态。"""
        if expert_id not in self.nodes:
            return

        node = self.nodes[expert_id]
        node.status = STATUS_DONE

        # 减少依赖此专家的节点的剩余依赖计数
        for dependent_id in node.depends_on:
            dep_node = self.nodes[dependent_id]
            if expert_id in dep_node.remaining_deps:
                dep_node.remaining_deps.remove(expert_id)

    def mark_error(self, expert_id: str, error_msg: str) -> None:
        """标记专家为错误状态。"""
        if expert_id in self.nodes:
            self.nodes[expert_id].status = STATUS_ERROR

    def update_status(self, expert_id: str, status: str) -> None:
        """更新专家状态。"""
        if expert_id in self.nodes:
            self.nodes[expert_id].status = status

    def get_status(self, expert_id: str) -> str:
        """获取专家状态。"""
        return self.nodes.get(expert_id, DAGNode(expert_id, [])).status

    def get_summary(self) -> dict:
        """获取调度器摘要（用于API响应）。"""
        if not self._is_scheduled:
            self.schedule()

        status_count = defaultdict(int)
        for node in self.nodes.values():
            status_count[node.status] += 1

        return {
            "total_experts": len(self.nodes),
            "execution_rounds": self.execution_rounds,
            "total_rounds": len(self.execution_rounds),
            "status_summary": dict(status_count),
            "blocked_experts": self.get_blocked_experts(),
            "current_round": next(
                (i for i, r in enumerate(self.execution_rounds)
                 if any(self.nodes[e].status == STATUS_RUNNING for e in r)),
                -1,
            ),
        }
