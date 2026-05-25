"""专家（Expert）相关 Schema — 支持多专家并行开发架构。

专家角色定义 + 工作流基础配置类。
完整工作流请求/响应类在 workflow.py 中定义。
"""

from pydantic import BaseModel, Field


class ExpertConfig(BaseModel):
    """工作流中的专家配置。"""
    expert_id: str
    enabled: bool = True
    priority: int = 0  # 同优先级可以并行执行
    custom_dependencies: list[str] = Field(default_factory=list)  # 覆盖默认依赖


class ParallelWorkflowConfig(BaseModel):
    """并行工作流配置。"""
    project_id: int
    experts: list[ExpertConfig]
    mode: str = Field(default="parallel", description="parallel | sequential")
    auto_start: bool = False


class ExpertProfile(BaseModel):
    """专家定义 — 代表一个可用的 Agent 专家角色。"""
    id: str = Field(..., description="专家ID，如 'planner', 'architect', 'programmer'")
    name: str = Field(..., description="专家名称，如 '策划师', '架构师'")
    description: str = Field(..., description="专家描述")
    role: str = Field(..., description="对应的 Agent role")
    capabilities: list[str] = Field(default_factory=list, description="该专家的能力列表")
    default_dependencies: list[str] = Field(default_factory=list, description="默认依赖的其他专家ID")


class ExpertStatusDetail(BaseModel):
    """单个专家的详细状态。"""
    role: str
    name: str
    status: str  # idle, running, done, waiting_user, error, blocked
    task: str = ""
    progress: int = 0
    output_preview: str = ""
    dependencies: list[str] = []
    blocked_by: str | None = None
    error_message: str | None = None
    started_at: float | None = None


class ParallelWorkflowStatusOut(BaseModel):
    """并行工作流状态响应。"""
    workflow_id: str
    project_id: int
    status: str  # idle, running, paused, waiting_user, completed, interrupted, error
    experts: dict[str, ExpertStatusDetail]
    execution_rounds: list[list[str]] = []  # 每轮并行的专家ID列表
    current_round: int = 0
    current_question_id: str | None = None
    complexity: str = ""


# 预定义的专家库
EXPERT_REGISTRY: dict[str, ExpertProfile] = {
    "planner": ExpertProfile(
        id="planner",
        name="策划师",
        description="负责需求分析、任务拆分、生成游戏设计文档",
        role="planner",
        capabilities=["需求分析", "任务规划", "文档生成"],
        default_dependencies=[],  # 第一个执行
    ),
    "architect": ExpertProfile(
        id="architect",
        name="架构师",
        description="负责技术选型、API 设计、系统架构",
        role="architect",
        capabilities=["技术选型", "架构设计", "API 设计"],
        default_dependencies=["planner"],  # 依赖策划师
    ),
    "programmer": ExpertProfile(
        id="programmer",
        name="程序员",
        description="负责代码生成、功能实现",
        role="programmer",
        capabilities=["代码生成", "功能实现", "Bug 修复"],
        default_dependencies=["planner", "architect"],  # 依赖策划和架构
    ),
    "qa": ExpertProfile(
        id="qa",
        name="测试工程师",
        description="负责测试用例生成、质量检查",
        role="qa",
        capabilities=["测试设计", "质量评估", "Bug 报告"],
        default_dependencies=["planner", "architect"],  # 与程序员并行，都依赖策划和架构
    ),
    "security": ExpertProfile(
        id="security",
        name="安全专家",
        description="负责安全审计、漏洞扫描",
        role="security",
        capabilities=["安全审计", "漏洞扫描", "合规检查"],
        default_dependencies=["architect"],
    ),
    "devops": ExpertProfile(
        id="devops",
        name="运维专家",
        description="负责部署配置、CI/CD 流水线",
        role="devops",
        capabilities=["部署配置", "CI/CD", "监控告警"],
        default_dependencies=["programmer", "security"],
    ),
}


def get_expert(expert_id: str) -> ExpertProfile | None:
    """根据 ID 获取专家定义。"""
    return EXPERT_REGISTRY.get(expert_id)


def list_experts() -> list[ExpertProfile]:
    """列出所有可用专家。"""
    return list(EXPERT_REGISTRY.values())
