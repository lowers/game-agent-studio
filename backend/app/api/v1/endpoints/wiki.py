"""LLM Wiki CRUD 端点 — 错误模式知识库管理。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_current_user
from app.database import get_db
from app.models.wiki import ErrorType
from app.services.wiki_service import LlmWikiService

router = APIRouter()


class WikiEntryCreate(BaseModel):
    """创建 Wiki 条目的请求。"""
    error_title: str = Field(..., max_length=500)
    error_description: str = Field(..., max_length=10000)
    fix_description: str = Field(..., max_length=10000)
    error_type: str = "other"
    file_path: Optional[str] = Field(None, max_length=500)
    line_number: Optional[int] = None
    code_snippet: Optional[str] = Field(None, max_length=20000)
    fix_code_snippet: Optional[str] = Field(None, max_length=20000)
    related_agent: Optional[str] = Field(None, max_length=100)
    related_workflow_id: Optional[str] = Field(None, max_length=200)
    project_id: Optional[int] = None
    tags: Optional[list[str]] = None
    severity_score: Optional[float] = 0.5


class WikiEntryUpdate(BaseModel):
    """更新 Wiki 条目的请求。"""
    error_title: Optional[str] = Field(None, max_length=500)
    error_description: Optional[str] = Field(None, max_length=10000)
    fix_description: Optional[str] = Field(None, max_length=10000)
    error_type: Optional[str] = None
    file_path: Optional[str] = Field(None, max_length=500)
    line_number: Optional[int] = None
    code_snippet: Optional[str] = Field(None, max_length=20000)
    fix_code_snippet: Optional[str] = Field(None, max_length=20000)
    related_agent: Optional[str] = Field(None, max_length=100)
    severity_score: Optional[float] = None
    helpfulness_score: Optional[float] = None
    tags: Optional[list[str]] = None


@router.get("/", response_model=dict)
async def list_wiki_entries(
    error_type: Optional[str] = Query(None, description="错误类型过滤"),
    related_agent: Optional[str] = Query(None, description="关联 Agent 过滤"),
    project_id: Optional[int] = Query(None, description="项目 ID 过滤"),
    tags: Optional[str] = Query(None, description="标签过滤，逗号分隔"),
    search: Optional[str] = Query(None, description="全文搜索关键词"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    sort_by: str = Query("occurrence_count", description="排序字段"),
    sort_desc: bool = Query(True, description="是否降序"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出 Wiki 条目，支持多条件筛选。"""
    service = LlmWikiService(db)

    # 解析错误类型
    error_type_enum = None
    if error_type:
        try:
            error_type_enum = ErrorType(error_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的错误类型: {error_type}")

    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    entries = await service.list_entries(
        error_type=error_type_enum,
        related_agent=related_agent,
        project_id=project_id,
        tags=tag_list,
        search_query=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await service.count_entries(
        error_type=error_type_enum,
        related_agent=related_agent,
        project_id=project_id,
        search_query=search,
    )

    return {
        "items": [e.to_dict() for e in entries],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_wiki_stats(
    project_id: Optional[int] = Query(None, description="项目 ID 过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取 Wiki 统计信息。"""
    service = LlmWikiService(db)
    return await service.get_statistics(project_id=project_id)


@router.get("/recommend", response_model=dict)
async def get_wiki_recommendations(
    description: str = Query(..., description="错误描述文本"),
    limit: int = Query(3, ge=1, le=10, description="推荐数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """根据错误描述推荐相似修复方案。"""
    service = LlmWikiService(db)
    recommendations = await service.get_recommendations(description, limit=limit)
    return {
        "recommendations": [e.to_dict() for e in recommendations],
        "count": len(recommendations),
    }


@router.post("/", response_model=dict)
async def create_wiki_entry(
    data: WikiEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_current_user),
):
    """创建新的 Wiki 条目（自动去重合并）。"""
    service = LlmWikiService(db)

    # 解析错误类型
    try:
        error_type = ErrorType(data.error_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的错误类型: {data.error_type}")

    entry = await service.record_error(
        error_title=data.error_title,
        error_description=data.error_description,
        fix_description=data.fix_description,
        error_type=error_type,
        file_path=data.file_path,
        line_number=data.line_number,
        code_snippet=data.code_snippet,
        fix_code_snippet=data.fix_code_snippet,
        related_agent=data.related_agent,
        related_workflow_id=data.related_workflow_id,
        project_id=data.project_id,
        tags=data.tags,
        severity_score=data.severity_score or 0.5,
    )
    return {"id": entry.id, "message": "条目已创建（或已合并到现有条目）"}


@router.get("/{entry_id}", response_model=dict)
async def get_wiki_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取单个 Wiki 条目。"""
    service = LlmWikiService(db)
    entry = await service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    return entry.to_dict()


@router.put("/{entry_id}", response_model=dict)
async def update_wiki_entry(
    entry_id: int,
    data: WikiEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_current_user),
):
    """更新 Wiki 条目。"""
    service = LlmWikiService(db)

    # 构建更新字典，排除 None 值
    updates = {k: v for k, v in data.model_dump().items() if v is not None}

    # 解析错误类型
    if "error_type" in updates:
        try:
            updates["error_type"] = ErrorType(updates["error_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的错误类型: {data.error_type}")

    entry = await service.update_entry(entry_id, updates)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    return entry.to_dict()


@router.delete("/{entry_id}", response_model=dict)
async def delete_wiki_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_current_user),
):
    """删除 Wiki 条目。"""
    service = LlmWikiService(db)
    success = await service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"message": "条目已删除"}


@router.post("/{entry_id}/feedback")
async def submit_feedback(
    entry_id: int,
    helpful: bool = Query(..., description="是否有帮助"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_current_user),
):
    """提交修复方案反馈。"""
    service = LlmWikiService(db)
    entry = await service.update_helpfulness(entry_id, helpful)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"message": "反馈已记录", "new_score": entry.helpfulness_score}
