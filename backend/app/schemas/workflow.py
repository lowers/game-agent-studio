"""工作流相关 Schema — 纯工作流数据模型。

从 expert.py 分离，避免循环依赖。
"""

from pydantic import BaseModel, Field


class ExpertOut(BaseModel):
    """专家详情输出（不含系统内部字段）。"""
    expert_id: str
    enabled: bool
    dependencies: list[str]


class WorkflowCreate(BaseModel):
    """创建工作流请求。"""
    project_id: int
    experts: list[str]  # 专家ID列表
    mode: str = Field(default="parallel", description="parallel | sequential | confirm")
    auto_start: bool = False
    custom_deps: dict[str, list[str]] = Field(
        default_factory=dict,
        description="专家ID -> 自定义依赖列表",
    )


class WorkflowDetail(BaseModel):
    """工作流详情。"""
    workflow_id: str
    project_id: int
    status: str
    experts: dict[str, ExpertOut]
    execution_rounds: list[list[str]]
    current_round: int = 0
    complexity: str = "简单"
    auto_started: bool = False  # 🔴 新增：是否自动启动


class WorkflowItem(BaseModel):
    """工作流列表项。"""
    workflow_id: str
    project_id: int | None = None
    status: str
    experts: list[dict] = Field(default_factory=list)
    execution_rounds: list[list[str]] = Field(default_factory=list)
    current_round: int = 0
    complexity: str = "简单"
    created_at: float | None = None


class WorkflowListOut(BaseModel):
    """工作流列表响应。"""
    items: list[WorkflowItem]
    total: int


class QuestionAnswerRequest(BaseModel):
    """提交问题答案请求。"""
    question_id: str = Field(..., description="问题ID（由后端生成）")
    answer: str | int = Field(..., description="答案：选项索引（int）或自定义文本（str）")


class QuestionAnswerResponse(BaseModel):
    """答案提交响应。"""
    success: bool
    question_id: str
    message: str = ""
