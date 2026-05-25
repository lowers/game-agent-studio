"""可行性评估模块 - 评估游戏设计需求的可行性和风险。

这个模块负责：
1. 评估技术可行性
2. 计算复杂度评分
3. 识别潜在风险
4. 提供专业改进建议
"""
from dataclasses import dataclass, field
from typing import Optional

from app.services.design_context import GameDesignContext, GameType, Platform


@dataclass
class EvaluationIssue:
    """评估问题"""
    severity: str  # "critical", "warning", "info"
    category: str  # "complexity", "technical", "scope", "experience"
    message: str
    suggestion: str
    reference: Optional[str] = None  # 参考文档链接


@dataclass
class EvaluationResult:
    """评估结果"""
    is_feasible: bool  # 整体是否可行
    complexity_score: int  # 0-100
    issues: list[EvaluationIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    risk_level: str = "low"  # "low", "medium", "high", "critical"

    def has_critical_issues(self) -> bool:
        return any(i.severity == "critical" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues) or len(self.warnings) > 0


class FeasibilityEvaluator:
    """游戏设计可行性评估器"""

    # === 复杂度阈值 ===
    COMPLEXITY_THRESHOLD_SIMPLE = 30
    COMPLEXITY_THRESHOLD_MEDIUM = 60
    COMPLEXITY_THRESHOLD_HIGH = 80

    # === 复杂度因子权重 ===
    COMPLEXITY_WEIGHTS = {
        "game_type": 10,
        "core_mechanics": 20,
        "characters": 15,
        "levels": 15,
        "visual_style": 5,
        "multiplayer": 25,
        "ai_enemies": 15,
        "physics": 10,
        "narrative": 10,
    }

    # === 经验对应的复杂度上限 ===
    EXPERIENCE_COMPLEXITY_LIMIT = {
        "beginner": 30,      # 初学者最多做简单项目
        "intermediate": 60,  # 中级开发者
        "advanced": 85,      # 高级开发者
        "expert": 100,       # 专家无限制
    }

    # === 不支持的功能（当前架构） ===
    UNSUPPORTED_FEATURES = [
        ("realtime_multiplayer", "实时多人在线游戏需要后端服务，当前版本不支持"),
        ("3d_rendering", "3D渲染需要专业引擎（如Unity/Unreal），当前版本基于2D Canvas"),
        ("voice_recognition", "语音识别需要额外服务集成"),
        ("cross_platform_native", "原生跨平台需要Unity/Unreal等引擎"),
    ]

    def evaluate(self, context: GameDesignContext) -> EvaluationResult:
        """评估设计上下文的可行性"""
        issues = []
        warnings = []
        suggestions = []
        complexity_breakdown = {}

        # 1. 基础复杂度评估
        complexity_breakdown = self._calculate_complexity(context)

        # 2. 技术可行性检查
        tech_issues = self._check_technical_feasibility(context)
        issues.extend(tech_issues)

        # 3. 范围评估（功能是否过多）
        scope_issues = self._check_scope(context)
        issues.extend(scope_issues)

        # 4. 经验匹配度
        total_complexity = sum(complexity_breakdown.values())
        exp_issues = self._check_experience_match(context, total_complexity)
        issues.extend(exp_issues)

        # 5. 生成建议
        suggestions = self._generate_suggestions(context, complexity_breakdown, issues)

        # 6. 确定风险等级
        risk_level = self._determine_risk_level(issues, total_complexity)

        # 7. 判断整体可行性
        is_feasible = (
            not any(i.severity == "critical" for i in issues)
            and total_complexity <= 100
        )

        # 如果不可行，生成具体改进建议
        if not is_feasible:
            critical_issues = [i for i in issues if i.severity == "critical"]
            for issue in critical_issues:
                suggestions.append(f"【必须】{issue.suggestion}")

        return EvaluationResult(
            is_feasible=is_feasible,
            complexity_score=min(total_complexity, 100),
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            risk_level=risk_level,
        )

    def _calculate_complexity(self, context: GameDesignContext) -> dict[str, int]:
        """计算各维度复杂度"""
        breakdown = {}

        # 游戏类型复杂度
        type_complexity = {
            GameType.CASUAL: 10,
            GameType.PUZZLE: 15,
            GameType.PLATFORMER: 20,
            GameType.SHOOTER: 25,
            GameType.ADVENTURE: 30,
            GameType.FIGHTING: 30,
            GameType.RACING: 35,
            GameType.RPG: 45,
            GameType.STRATEGY: 40,
            GameType.SIMULATION: 50,
        }
        breakdown["game_type"] = type_complexity.get(context.game_type, 20)

        # 核心玩法复杂度
        mechanics_complexity = 10
        if context.gameplay_keywords:
            # 关键词越多越复杂
            mechanics_complexity += len(context.gameplay_keywords) * 3
        # 检查高复杂度玩法
        complex_keywords = ["物理", "重力", "碰撞", "AI", "寻路", "路径", "判定"]
        for kw in complex_keywords:
            if kw in context.core_mechanics:
                mechanics_complexity += 5
        breakdown["core_mechanics"] = min(mechanics_complexity, 40)

        # 角色复杂度
        char_complexity = 5  # 基础
        if context.antagonist:
            char_complexity += 5
        if context.npcs:
            char_complexity += len(context.npcs) * 3
        breakdown["characters"] = min(char_complexity, 25)

        # 关卡复杂度
        level_complexity = 5  # 基础
        if context.level_design:
            level_complexity += 10
            if len(context.level_design) > 200:
                level_complexity += 5
        breakdown["levels"] = min(level_complexity, 30)

        # 视觉风格复杂度
        visual_complexity = 3  # 基础
        if context.visual_style_other:
            visual_complexity += 5
        breakdown["visual_style"] = min(visual_complexity, 15)

        # 多平台复杂度
        (len(context.target_platforms) - 1) * 5 if context.target_platforms else 0
        breakdown["multiplayer"] = 0  # 单独计算

        return breakdown

    def _check_technical_feasibility(self, context: GameDesignContext) -> list[EvaluationIssue]:
        """检查技术可行性"""
        issues = []

        # 检查不支持的功能
        idea_lower = context.user_idea.lower() + context.core_mechanics.lower()

        for feature, reason in self.UNSUPPORTED_FEATURES:
            if feature.replace("_", "") in idea_lower.replace("_", ""):
                issues.append(EvaluationIssue(
                    severity="critical",
                    category="technical",
                    message=f"功能 '{feature}' 当前不支持",
                    suggestion=reason,
                    reference="docs/limitations.md"
                ))

        # 检查 3D 需求
        d_keywords = ["3d", "三维", "立体", "unity", "unreal", "blender"]
        if any(kw in idea_lower for kw in d_keywords):
            issues.append(EvaluationIssue(
                severity="critical",
                category="technical",
                message="检测到3D渲染需求",
                suggestion="当前版本基于HTML5 Canvas 2D渲染，建议改为2D像素风或使用WebGL（如Phaser框架）",
                reference="docs/2d-vs-3d.md"
            ))

        # 检查 Web 平台兼容性
        if Platform.WEB_BROWSER in context.target_platforms:
            # Web 平台的限制
            if "文件读写" in context.core_mechanics or "存档" in context.core_mechanics:
                issues.append(EvaluationIssue(
                    severity="warning",
                    category="technical",
                    message="存档功能在Web平台需要特殊处理",
                    suggestion="Web平台可使用LocalStorage或IndexedDB存储游戏进度",
                    reference="docs/web-storage.md"
                ))

        return issues

    def _check_scope(self, context: GameDesignContext) -> list[EvaluationIssue]:
        """检查项目范围"""
        issues = []

        # 描述长度检查（过长的描述可能意味着需求过多）
        total_length = (
            len(context.user_idea)
            + len(context.core_mechanics)
            + len(context.protagonist)
        )

        if total_length > 2000:
            issues.append(EvaluationIssue(
                severity="warning",
                category="scope",
                message="需求描述较长，可能包含过多功能",
                suggestion="建议将项目拆分为多个阶段，MVP阶段聚焦核心玩法",
                reference="docs/scoping.md"
            ))

        # 检查关键词复杂度
        all_text = f"{context.user_idea} {context.core_mechanics}"
        high_effort_keywords = [
            "物理引擎", "重力模拟", "AI行为树", "寻路算法",
            "多人联机", "网络同步", "动画系统", "粒子效果"
        ]

        high_effort_count = sum(1 for kw in high_effort_keywords if kw in all_text)
        if high_effort_count >= 3:
            issues.append(EvaluationIssue(
                severity="warning",
                category="scope",
                message=f"检测到{high_effort_count}个高难度功能",
                suggestion="建议分阶段实现，或降低部分功能的复杂度",
                reference="docs/phase-planning.md"
            ))

        return issues

    def _check_experience_match(self, context: GameDesignContext, total_complexity: int) -> list[EvaluationIssue]:
        """检查经验匹配度"""
        issues = []

        if not context.developer_experience:
            return issues

        exp = context.developer_experience.lower()
        complexity = total_complexity

        # 确定经验等级
        if "初学" in exp or "新手" in exp or "beginner" in exp:
            level = "beginner"
        elif "中级" in exp or "intermediate" in exp:
            level = "intermediate"
        elif "高级" in exp or "senior" in exp:
            level = "advanced"
        else:
            return issues

        max_complexity = self.EXPERIENCE_COMPLEXITY_LIMIT.get(level, 60)

        if complexity > max_complexity:
            issues.append(EvaluationIssue(
                severity="warning",
                category="experience",
                message=f"项目复杂度({complexity})可能超出{level}开发者的能力范围",
                suggestion=f"建议将复杂度控制在{max_complexity}以下，或寻求更有经验的开发者帮助",
                reference="docs/experience-matrix.md"
            ))

        return issues

    def _generate_suggestions(
        self,
        context: GameDesignContext,
        complexity_breakdown: dict[str, int],
        issues: list[EvaluationIssue]
    ) -> list[str]:
        """生成改进建议"""
        suggestions = []

        # 基于复杂度过高给出建议
        total = sum(complexity_breakdown.values())
        if total > 60:
            # 找出最高复杂度的部分
            sorted_parts = sorted(complexity_breakdown.items(), key=lambda x: x[1], reverse=True)
            if sorted_parts[0][0] == "core_mechanics":
                suggestions.append("考虑简化核心玩法，先实现最基础的机制")
            elif sorted_parts[0][0] == "characters":
                suggestions.append("减少角色数量，第一版只做主角和1-2个敌人")

        # 基于缺失信息给出建议
        if not context.visual_style:
            suggestions.append("建议选择明确的视觉风格，如'像素风'或'卡通风'，便于后续美术执行")

        if not context.target_platforms:
            suggestions.append("明确目标平台有助于选择合适的技术方案")

        # 基于问题给出建议
        for issue in issues:
            if issue.suggestion and issue.suggestion not in suggestions:
                suggestions.append(issue.suggestion)

        return suggestions

    def _determine_risk_level(
        self,
        issues: list[EvaluationIssue],
        complexity: int
    ) -> str:
        """确定风险等级"""
        critical_count = sum(1 for i in issues if i.severity == "critical")
        warning_count = sum(1 for i in issues if i.severity == "warning")

        if critical_count >= 2 or complexity > 90:
            return "critical"
        elif critical_count >= 1 or warning_count >= 3 or complexity > 70:
            return "high"
        elif warning_count >= 1 or complexity > 50:
            return "medium"
        return "low"

    def get_complexity_label(self, score: int) -> str:
        """获取复杂度标签"""
        if score <= self.COMPLEXITY_THRESHOLD_SIMPLE:
            return "简单"
        elif score <= self.COMPLEXITY_THRESHOLD_MEDIUM:
            return "中等"
        elif score <= self.COMPLEXITY_THRESHOLD_HIGH:
            return "复杂"
        return "非常复杂"


# 全局实例
feasibility_evaluator = FeasibilityEvaluator()
