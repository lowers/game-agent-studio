"""LLM Wiki 数据模型 — 记录 AI 代码生成/执行中的错误模式与修复方案。"""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ErrorType(str, enum.Enum):
    """错误类型枚举。"""
    SYNTAX = "syntax"           # 语法错误
    LOGIC = "logic"             # 逻辑错误
    SECURITY = "security"       # 安全漏洞
    PERFORMANCE = "performance" # 性能问题
    ARCHITECTURE = "architecture" # 架构问题
    API_INTEGRATION = "api_integration"  # API 集成错误
    DATABASE = "database"       # 数据库相关错误
    DEPENDENCY = "dependency"   # 依赖/导入错误
    OTHER = "other"             # 其他类型


class LlmWikiEntry(Base):
    """LLM Wiki 错误记录。"""
    __tablename__ = "llm_wiki"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    error_type = Column(Enum(ErrorType), nullable=False, index=True)
    error_title = Column(String(200), nullable=False, index=True)
    error_description = Column(Text, nullable=False)

    # 位置信息
    file_path = Column(String(500), nullable=True, index=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)  # 出错代码片段

    # 修复信息
    fix_description = Column(Text, nullable=False)
    fix_code_snippet = Column(Text, nullable=True)  # 修复后代码片段

    # 关联信息
    related_agent = Column(String(100), nullable=True, index=True)  # 哪个 Agent 触发的
    related_workflow_id = Column(String(100), nullable=True, index=True)  # 工作流 ID
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    # 统计信息
    occurrence_count = Column(Integer, default=1, nullable=False)  # 出现次数
    last_occurred_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 最后出现时间
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 标签系统
    tags = Column(String(500), nullable=True)  # 逗号分隔的标签

    # 评分（0-1，用于推荐排序）
    severity_score = Column(Float, default=0.5, nullable=False)  # 严重程度
    helpfulness_score = Column(Float, default=0.5, nullable=False)  # 修复方案有效性评分

    # 关联项目
    project = relationship("Project", back_populates="llm_wiki_entries")

    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "id": self.id,
            "error_type": self.error_type.value,
            "error_title": self.error_title,
            "error_description": self.error_description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "fix_description": self.fix_description,
            "fix_code_snippet": self.fix_code_snippet,
            "related_agent": self.related_agent,
            "related_workflow_id": self.related_workflow_id,
            "project_id": self.project_id,
            "occurrence_count": self.occurrence_count,
            "last_occurred_at": self.last_occurred_at.isoformat() if self.last_occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags.split(",") if self.tags else [],
            "severity_score": self.severity_score,
            "helpfulness_score": self.helpfulness_score,
        }
