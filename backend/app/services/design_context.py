"""设计上下文 - 结构化采集用户的游戏设计需求。

这个模块定义了在主动问询过程中需要收集的完整设计上下文。
它作为 ConversationService 和 FeasibilityEvaluator 之间的桥梁。
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GameType(str, Enum):
    """游戏类型枚举"""
    PLATFORMER = "platformer"           # 平台跳跃
    RPG = "rpg"                         # 角色扮演
    PUZZLE = "puzzle"                   # 解谜
    SHOOTER = "shooter"                 # 射击
    STRATEGY = "strategy"               # 策略
    SIMULATION = "simulation"            # 模拟经营
    ADVENTURE = "adventure"             # 冒险
    FIGHTING = "fighting"               # 格斗
    RACING = "racing"                   # 竞速
    CASUAL = "casual"                   # 休闲/益智
    OTHER = "other"                     # 其他


class Platform(str, Enum):
    """目标平台"""
    WEB_BROWSER = "web_browser"         # 网页浏览器
    WINDOWS = "windows"                 # Windows
    MACOS = "macos"                    # macOS
    LINUX = "linux"                    # Linux
    IOS = "ios"                        # iOS
    ANDROID = "android"                # Android
    STEAM = "steam"                    # Steam
    SWITCH = "switch"                  # Nintendo Switch


class VisualStyle(str, Enum):
    """视觉风格"""
    PIXEL_ART = "pixel_art"            # 像素风格
    CARTOON = "cartoon"                # 卡通
    REALISTIC = "realistic"            # 写实
    MINIMALIST = "minimalist"          # 极简
    RETRO = "retro"                    # 复古
    CYBERPUNK = "cyberpunk"             # 赛博朋克
    FANTASY = "fantasy"                # 奇幻
    ABSTRACT = "abstract"               # 抽象


class GameDesignContext(BaseModel):
    """游戏设计上下文 - 完整的结构化需求采集"""

    # === 基础信息 ===
    session_id: str = Field(default="", description="会话ID")
    user_idea: str = Field(default="", description="用户的原始想法（保留原始输入）")

    # === 游戏类型 ===
    game_type: Optional[GameType] = Field(default=None, description="游戏类型")
    game_type_other: Optional[str] = Field(default=None, description="其他游戏类型描述")

    # === 核心玩法 ===
    core_mechanics: str = Field(default="", description="核心玩法机制描述")
    gameplay_keywords: list[str] = Field(default_factory=list, description="玩法关键词")

    # === 角色/单位设计 ===
    protagonist: str = Field(default="", description="主角描述")
    antagonist: Optional[str] = Field(default=None, description="反派/敌人描述")
    npcs: list[str] = Field(default_factory=list, description="NPC描述列表")
    enemies_collectibles: str = Field(default="", description="敌人和收集物")

    # === 目标和条件 ===
    win_condition: str = Field(default="", description="胜利条件")
    lose_condition: Optional[str] = Field(default=None, description="失败条件")
    level_design: Optional[str] = Field(default=None, description="关卡设计概述")

    # === 视觉风格 ===
    visual_style: Optional[VisualStyle] = Field(default=None, description="视觉风格")
    visual_style_other: Optional[str] = Field(default=None, description="其他视觉风格")
    color_palette_hint: Optional[str] = Field(default=None, description="配色倾向")

    # === 技术栈 ===
    target_platforms: list[Platform] = Field(default_factory=list, description="目标平台")
    tech_preference: Optional[str] = Field(default=None, description="技术偏好（Canvas/Unity/Unreal等）")

    # === 团队/项目信息 ===
    team_size: Optional[int] = Field(default=None, description="团队规模")
    dev_time_constraint: Optional[str] = Field(default=None, description="开发时间限制")
    budget_level: Optional[str] = Field(default=None, description="预算等级：low/medium/high")

    # === 元数据 ===
    complexity_score: int = Field(default=0, ge=0, le=100, description="复杂度评分（0-100）")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")
    developer_experience: Optional[str] = Field(default=None, description="开发者经验水平")

    def get_missing_fields(self) -> list[str]:
        """返回缺失的必需字段列表（按优先级）"""
        missing = []

        # P0 - 核心必需
        if not self.game_type:
            missing.append("game_type")
        if not self.core_mechanics:
            missing.append("core_mechanics")
        if not self.protagonist:
            missing.append("protagonist")
        if not self.win_condition:
            missing.append("win_condition")

        # P1 - 重要但可选
        if not self.visual_style:
            missing.append("visual_style")
        if not self.target_platforms:
            missing.append("target_platforms")

        return missing

    def is_minimum_viable(self) -> bool:
        """检查是否满足最低可行需求"""
        return (
            self.game_type is not None
            and self.core_mechanics
            and self.protagonist
        )

    def is_complete(self) -> bool:
        """检查是否所有字段都已填充"""
        return len(self.get_missing_fields()) == 0

    def to_game_design_doc(self) -> dict:
        """转换为旧的 GameDesignDoc 格式（兼容现有系统）"""
        return {
            "game_type": self.game_type.value if self.game_type else "",
            "protagonist": self.protagonist,
            "core_gameplay": self.core_mechanics,
            "enemies_collectibles": self.enemies_collectibles,
            "win_condition": self.win_condition,
        }


class ConversationState(str, Enum):
    """对话状态枚举"""
    INITIAL = "initial"                          # 初始，等待需求描述
    GATHERING_IDEA = "gathering_idea"            # 收集用户原始想法
    CLARIFY_GAME_TYPE = "clarify_game_type"     # 追问游戏类型
    CLARIFY_CORE_MECHANICS = "clarify_core"    # 追问核心玩法
    CLARIFY_CHARACTERS = "clarify_chars"       # 追问角色设计
    CLARIFY_VISUAL = "clarify_visual"          # 追问视觉风格
    CLARIFY_TECHNICAL = "clarify_technical"     # 追问技术偏好
    EVALUATING = "evaluating"                   # 评估可行性
    REFINE_WITH_ISSUES = "refine_with_issues"   # 基于问题优化
    FINALIZING = "finalizing"                   # 确认方案
    COMPLETE = "complete"                       # 完成设计文档


class ConversationSession(BaseModel):
    """对话会话状态"""
    session_id: str
    state: ConversationState = ConversationState.INITIAL
    context: GameDesignContext = Field(default_factory=GameDesignContext)
    message_history: list[dict] = Field(default_factory=list)
    last_inquiry_topic: Optional[str] = None
    inquiry_count: int = Field(default=0, description="追问次数")
    max_inquiry_count: int = Field(default=10, description="最大追问次数（防止无限循环）")

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.message_history.append({
            "role": role,
            "content": content,
            "state": self.state.value
        })

    def should_continue_inquiry(self) -> bool:
        """判断是否应该继续追问"""
        return (
            not self.context.is_complete()
            and self.inquiry_count < self.max_inquiry_count
        )

    def advance_state(self):
        """推进状态机到下一个状态"""
        state_transitions = {
            ConversationState.INITIAL: ConversationState.GATHERING_IDEA,
            ConversationState.GATHERING_IDEA: ConversationState.CLARIFY_GAME_TYPE,
            ConversationState.CLARIFY_GAME_TYPE: ConversationState.CLARIFY_CORE_MECHANICS,
            ConversationState.CLARIFY_CORE_MECHANICS: ConversationState.CLARIFY_CHARACTERS,
            ConversationState.CLARIFY_CHARACTERS: ConversationState.CLARIFY_VISUAL,
            ConversationState.CLARIFY_VISUAL: ConversationState.CLARIFY_TECHNICAL,
            ConversationState.CLARIFY_TECHNICAL: ConversationState.EVALUATING,
            ConversationState.EVALUATING: ConversationState.FINALIZING,
            ConversationState.REFINE_WITH_ISSUES: ConversationState.FINALIZING,
            ConversationState.FINALIZING: ConversationState.COMPLETE,
        }
        self.state = state_transitions.get(self.state, self.state)
