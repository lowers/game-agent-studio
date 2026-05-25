"""LLM Wiki 服务层 — 错误模式记录、检索、推荐。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.wiki import ErrorType, LlmWikiEntry

logger = logging.getLogger(__name__)

class LlmWikiService:
    """LLM Wiki 知识库服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(self, entry: LlmWikiEntry) -> LlmWikiEntry:
        """创建新的 Wiki 条目。"""
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_entry(self, entry_id: int) -> Optional[LlmWikiEntry]:
        """根据 ID 获取条目。"""
        result = await self.db.execute(
            select(LlmWikiEntry).where(LlmWikiEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        error_type: Optional[ErrorType] = None,
        related_agent: Optional[str] = None,
        project_id: Optional[int] = None,
        tags: Optional[list[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "occurrence_count",
        sort_desc: bool = True,
    ) -> list[LlmWikiEntry]:
        """列出 Wiki 条目，支持多条件筛选。"""
        stmt = select(LlmWikiEntry)

        # 构建筛选条件
        conditions = []
        if error_type is not None:
            conditions.append(LlmWikiEntry.error_type == error_type)
        if related_agent is not None:
            conditions.append(LlmWikiEntry.related_agent == related_agent)
        if project_id is not None:
            conditions.append(LlmWikiEntry.project_id == project_id)
        if tags:
            # 标签匹配：逗号分隔的字符串中包含任一标签
            for tag in tags:
                conditions.append(LlmWikiEntry.tags.ilike(f"%{tag}%"))
        if search_query:
            # 全文搜索：在标题和描述中搜索
            conditions.append(
                or_(
                    LlmWikiEntry.error_title.ilike(f"%{search_query}%"),
                    LlmWikiEntry.error_description.ilike(f"%{search_query}%"),
                    LlmWikiEntry.fix_description.ilike(f"%{search_query}%"),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 排序
        sort_col = getattr(LlmWikiEntry, sort_by, LlmWikiEntry.occurrence_count)
        if sort_desc:
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        # 分页
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_entries(
        self,
        error_type: Optional[ErrorType] = None,
        related_agent: Optional[str] = None,
        project_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """统计符合条件的条目数。"""
        stmt = select(func.count(LlmWikiEntry.id))
        conditions = []
        if error_type is not None:
            conditions.append(LlmWikiEntry.error_type == error_type)
        if related_agent is not None:
            conditions.append(LlmWikiEntry.related_agent == related_agent)
        if project_id is not None:
            conditions.append(LlmWikiEntry.project_id == project_id)
        if search_query:
            conditions.append(
                or_(
                    LlmWikiEntry.error_title.ilike(f"%{search_query}%"),
                    LlmWikiEntry.error_description.ilike(f"%{search_query}%"),
                )
            )
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_entry(self, entry_id: int, updates: dict) -> Optional[LlmWikiEntry]:
        """更新 Wiki 条目。"""
        entry = await self.get_entry(entry_id)
        if not entry:
            return None

        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete_entry(self, entry_id: int) -> bool:
        """删除 Wiki 条目。"""
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        await self.db.delete(entry)
        await self.db.commit()
        return True

    async def record_error(
        self,
        error_title: str,
        error_description: str,
        fix_description: str,
        error_type: ErrorType = ErrorType.OTHER,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        fix_code_snippet: Optional[str] = None,
        related_agent: Optional[str] = None,
        related_workflow_id: Optional[str] = None,
        project_id: Optional[int] = None,
        tags: Optional[list[str]] = None,
        severity_score: float = 0.5,
    ) -> LlmWikiEntry:
        """记录一个错误（自动去重：相似错误合并）。"""
        # 查找是否已存在相似错误
        existing = await self.list_entries(
            error_type=error_type,
            related_agent=related_agent,
            search_query=error_title[:50],  # 用标题前缀搜索
            limit=5,
        )

        if existing:
            # 找到相似错误，增加计数
            best_match = max(existing, key=lambda e: (
                len(set(e.tags.split(",") if e.tags else []).intersection(set(tags or []))),
                e.occurrence_count,
            ))
            best_match.occurrence_count += 1
            best_match.last_occurred_at = datetime.utcnow()
            if file_path and not best_match.file_path:
                best_match.file_path = file_path
            if line_number and not best_match.line_number:
                best_match.line_number = line_number
            await self.db.commit()
            await self.db.refresh(best_match)
            return best_match

        # 创建新条目
        entry = LlmWikiEntry(
            error_title=error_title,
            error_description=error_description,
            fix_description=fix_description,
            error_type=error_type,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            fix_code_snippet=fix_code_snippet,
            related_agent=related_agent,
            related_workflow_id=related_workflow_id,
            project_id=project_id,
            tags=",".join(tags) if tags else None,
            severity_score=severity_score,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_recommendations(
        self,
        error_description: str,
        limit: int = 3,
    ) -> list[LlmWikiEntry]:
        """根据错误描述推荐相似修复方案（基于关键词匹配）。"""
        keywords = self._extract_keywords(error_description)

        if not keywords:
            return []

        # 构建搜索条件
        conditions = []
        for kw in keywords:
            conditions.append(or_(
                LlmWikiEntry.error_title.ilike(f"%{kw}%"),
                LlmWikiEntry.error_description.ilike(f"%{kw}%"),
                LlmWikiEntry.fix_description.ilike(f"%{kw}%"),
            ))

        if not conditions:
            return []

        stmt = select(LlmWikiEntry).where(or_(*conditions))
        # 按出现次数和严重程度排序
        stmt = stmt.order_by(
            LlmWikiEntry.occurrence_count.desc(),
            LlmWikiEntry.severity_score.desc(),
        ).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _extract_keywords(self, text: str) -> list[str]:
        """从错误描述中提取关键词。"""
        # 简单的关键词提取：去掉常见停用词，提取有意义的词
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "under", "again", "further", "then", "once", "and",
            "but", "or", "nor", "so", "yet", "both", "either", "neither", "not",
            "only", "own", "same", "than", "too", "very", "just", "also",
            "python", "async", "await", "def", "class", "import", "from",
            "return", "if", "else", "elif", "for", "while", "try", "except",
        }

        import re
        # 提取中文字和英文单词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 1]

    async def get_statistics(self, project_id: Optional[int] = None) -> dict:
        """获取 Wiki 统计信息。"""
        conditions = []
        if project_id is not None:
            conditions.append(LlmWikiEntry.project_id == project_id)

        base_stmt = select(LlmWikiEntry)
        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))

        total = await self.db.execute(
            select(func.count(LlmWikiEntry.id)).where(and_(*conditions) if conditions else True)
        )
        total_count = total.scalar_one()

        # 按类型统计
        type_stats = await self.db.execute(
            select(LlmWikiEntry.error_type, func.count(LlmWikiEntry.id))
            .where(and_(*conditions) if conditions else True)
            .group_by(LlmWikiEntry.error_type)
        )
        type_counts = {e[0].value: e[1] for e in type_stats.all()}

        # 按 Agent 统计
        agent_stats = await self.db.execute(
            select(LlmWikiEntry.related_agent, func.count(LlmWikiEntry.id))
            .where(and_(LlmWikiEntry.related_agent.isnot(None), *(conditions if conditions else [])))
            .group_by(LlmWikiEntry.related_agent)
        )
        agent_counts = {e[0]: e[1] for e in agent_stats.all()}

        # 高频错误 Top 5
        top_errors = await self.list_entries(
            limit=5, sort_by="occurrence_count", sort_desc=True,
        )

        return {
            "total_entries": total_count,
            "by_error_type": type_counts,
            "by_related_agent": agent_counts,
            "top_errors": [e.to_dict() for e in top_errors],
            "avg_occurrence": round(sum(e.occurrence_count for e in top_errors) / max(len(top_errors), 1), 2),
        }

    async def update_helpfulness(self, entry_id: int, helpful: bool) -> Optional[LlmWikiEntry]:
        """更新条目的 helpfulness_score（用户反馈）。"""
        entry = await self.get_entry(entry_id)
        if not entry:
            return None

        # 简单评分更新：helpful 增加 0.1，否则减少 0.05
        if helpful:
            entry.helpfulness_score = min(1.0, entry.helpfulness_score + 0.1)
        else:
            entry.helpfulness_score = max(0.0, entry.helpfulness_score - 0.05)

        await self.db.commit()
        await self.db.refresh(entry)
        return entry
