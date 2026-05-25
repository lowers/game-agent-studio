"""问询策略引擎 - 生成引导性问题，实现主动问询。

这个模块负责：
1. 根据当前上下文缺失的字段决定下一个问题
2. 生成引导性问题（不是简单的Yes/No）
3. 提取用户回复中的有用信息
4. 基于历史对话调整问询策略
"""
from dataclasses import dataclass
from typing import Callable, Optional

from app.services.design_context import (
    ConversationSession,
    GameDesignContext,
    GameType,
    Platform,
    VisualStyle,
)


@dataclass
class InquiryQuestion:
    """问询问题"""
    topic: str  # 问题主题
    question: str  # 完整的问题文本
    options: Optional[list[str]] = None  # 可选的多选题选项
    hint: Optional[str] = None  # 给用户的提示
    follow_up: Optional[str] = None  # 追问模板


@dataclass
class ExtractionResult:
    """从用户回复中提取的信息"""
    extracted: dict  # 提取到的字段
    confidence: float  # 提取置信度 (0-1)
    needs_clarification: bool  # 是否需要进一步澄清


class InquiryStrategy:
    """主动问询策略引擎"""

    # === 问询优先级（数字越小优先级越高）===
    FIELD_PRIORITY = {
        "game_type": 1,
        "core_mechanics": 2,
        "protagonist": 3,
        "win_condition": 4,
        "visual_style": 5,
        "target_platforms": 6,
        "enemies_collectibles": 7,
        "antagonist": 8,
        "level_design": 9,
    }

    # === 游戏类型选项 ===
    GAME_TYPE_OPTIONS = [
        ("平台跳跃", "如马里奥、Celeste、蔚蓝等"),
        ("RPG/角色扮演", "如塞尔达、最终幻想等"),
        ("解谜游戏", "如传送门、纪念碑谷等"),
        ("射击游戏", "如毁灭战士、灵魂之火等"),
        ("格斗游戏", "如街霸、拳皇等"),
        ("策略游戏", "如文明、三国志等"),
        ("模拟经营", "如星露谷、模拟城市等"),
        ("休闲/益智", "如2048、消消乐等"),
        ("其他/不确定", "让我描述一下玩法特点"),
    ]

    # === 视觉风格选项 ===
    VISUAL_STYLE_OPTIONS = [
        ("像素风格", "Retro像素游戏"),
        ("卡通/动漫风格", "颜色鲜艳，角色可爱"),
        ("写实风格", "追求真实感"),
        ("极简风格", "简单几何形状，少即是多"),
        ("复古风格", "致敬经典游戏的视觉"),
        ("赛博朋克", "霓虹灯、高科技感"),
        ("奇幻风格", "魔法、龙、剑与骑士"),
        ("抽象风格", "艺术化、实验性"),
    ]

    # === 平台选项 ===
    PLATFORM_OPTIONS = [
        ("网页浏览器", "H5游戏，可分享链接"),
        ("Windows", "PC端应用"),
        ("Android", "安卓手机/平板"),
        ("iOS", "苹果手机/平板"),
    ]

    def __init__(self):
        self._extractors: dict[str, Callable] = {
            "game_type": self._extract_game_type,
            "visual_style": self._extract_visual_style,
            "target_platforms": self._extract_platforms,
            "core_mechanics": self._extract_core_mechanics,
            "protagonist": self._extract_protagonist,
            "win_condition": self._extract_win_condition,
        }

    def get_next_question(
        self,
        session: ConversationSession,
        evaluation_result=None
    ) -> Optional[InquiryQuestion]:
        """根据当前会话状态生成下一个问题"""
        context = session.context

        # 如果有可行性评估问题，先处理问题
        if evaluation_result and not evaluation_result.is_feasible:
            return self._generate_feasibility_question(evaluation_result)

        # 获取缺失字段
        missing = context.get_missing_fields()
        if not missing:
            return None  # 上下文完整

        # 按优先级选择下一个问询主题
        priority_field = min(missing, key=lambda f: self.FIELD_PRIORITY.get(f, 99))

        return self._generate_question_for_field(priority_field, context)

    def _generate_question_for_field(
        self,
        field: str,
        context: GameDesignContext
    ) -> InquiryQuestion:
        """为指定字段生成引导性问题"""
        generators = {
            "game_type": self._question_game_type,
            "core_mechanics": self._question_core_mechanics,
            "protagonist": self._question_protagonist,
            "win_condition": self._question_win_condition,
            "visual_style": self._question_visual_style,
            "target_platforms": self._question_platforms,
            "enemies_collectibles": self._question_enemies,
        }

        generator = generators.get(field)
        if generator:
            return generator(context)

        # 默认问题
        return InquiryQuestion(
            topic=field,
            question=f"请补充一下 {field} 相关的信息",
            hint="越详细越好"
        )

    def _question_game_type(self, context: GameDesignContext) -> InquiryQuestion:
        """游戏类型问题"""
        # 检查用户是否已有模糊描述
        if context.user_idea:
            return InquiryQuestion(
                topic="game_type",
                question="听起来很有趣！你想做的游戏更接近哪种类型？",
                options=[opt[0] for opt in self.GAME_TYPE_OPTIONS],
                hint="不同类型有不同的开发难度和重点",
                follow_up="好的，{answer}游戏。我再确认一下，核心玩法是怎样的？"
            )

        return InquiryQuestion(
            topic="game_type",
            question="你想做什么类型的游戏呢？",
            options=[opt[0] for opt in self.GAME_TYPE_OPTIONS],
            hint="类型决定了游戏的基本框架"
        )

    def _question_core_mechanics(self, context: GameDesignContext) -> InquiryQuestion:
        """核心玩法问题"""
        game_type_hint = f"一款{context.game_type.value}游戏" if context.game_type else "这款游戏"

        return InquiryQuestion(
            topic="core_mechanics",
            question=f"{game_type_hint}，玩家主要做什么？是怎么操作的？",
            hint="比如'控制角色左右移动，跳跃躲避障碍'或'拖动方块消除同类'",
            follow_up="明白了，{answer}。这个玩法听起来{'有趣' if context.game_type in [GameType.CASUAL, GameType.PUZZLE] else '有挑战性'}！"
        )

    def _question_protagonist(self, context: GameDesignContext) -> InquiryQuestion:
        """主角问题"""
        mechanics_hint = f"关于{context.core_mechanics[:20]}..." if context.core_mechanics else ""

        return InquiryQuestion(
            topic="protagonist",
            question=f"{mechanics_hint}玩家控制的主角是什么样的？",
            hint="比如'一个会飞的机器人'或'一只可爱的小狐狸'",
            follow_up="好的，主角是{answer}。有什么特别的能力吗？"
        )

    def _question_win_condition(self, context: GameDesignContext) -> InquiryQuestion:
        """胜利条件问题"""
        return InquiryQuestion(
            topic="win_condition",
            question="玩家怎么就算赢了呢？目标是什么？",
            hint="'收集所有金币过关'、'打败Boss'、'到达终点'等"
        )

    def _question_visual_style(self, context: GameDesignContext) -> InquiryQuestion:
        """视觉风格问题"""
        return InquiryQuestion(
            topic="visual_style",
            question="游戏的视觉风格是什么样的？",
            options=[opt[0] for opt in self.VISUAL_STYLE_OPTIONS],
            hint="视觉风格会影响开发工作量和美术资源"
        )

    def _question_platforms(self, context: GameDesignContext) -> InquiryQuestion:
        """目标平台问题"""
        return InquiryQuestion(
            topic="target_platforms",
            question="你希望游戏在哪些平台运行？",
            options=[opt[0] for opt in self.PLATFORM_OPTIONS],
            hint="优先选择一个平台，后续可以扩展"
        )

    def _question_enemies(self, context: GameDesignContext) -> InquiryQuestion:
        """敌人/收集物问题"""
        return InquiryQuestion(
            topic="enemies_collectibles",
            question="游戏中有什么敌人或可以收集的东西吗？",
            hint="'金币、宝石'、'怪物、陷阱'，或者'可以没有敌人，纯解谜'"
        )

    def _generate_feasibility_question(self, evaluation_result) -> InquiryQuestion:
        """生成关于可行性问题的追问"""
        # 找到最严重的问题
        critical_issues = [i for i in evaluation_result.issues if i.severity == "critical"]
        warning_issues = [i for i in evaluation_result.issues if i.severity == "warning"]

        if critical_issues:
            issue = critical_issues[0]
            return InquiryQuestion(
                topic="feasibility",
                question=f"我想确认一下：{issue.message}",
                hint=issue.suggestion
            )

        if warning_issues:
            issue = warning_issues[0]
            return InquiryQuestion(
                topic="feasibility",
                question=f"有个建议想听听你的想法：{issue.suggestion}",
                hint="这样调整可以让项目更容易实现"
            )

        return None

    def extract_from_response(
        self,
        field: str,
        response: str,
        context: GameDesignContext
    ) -> ExtractionResult:
        """从用户回复中提取指定字段的信息"""
        extractor = self._extractors.get(field)
        if extractor:
            return extractor(response, context)

        # 默认提取：整段作为文本
        return ExtractionResult(
            extracted={field: response.strip()},
            confidence=0.5,
            needs_clarification=False
        )

    def _extract_game_type(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取游戏类型"""
        response_lower = response.lower()
        extracted_type = None

        # 关键词映射
        keyword_map = {
            "platform": GameType.PLATFORMER,
            "跳跃": GameType.PLATFORMER,
            "马里奥": GameType.PLATFORMER,
            "rpg": GameType.RPG,
            "角色扮演": GameType.RPG,
            "塞尔达": GameType.RPG,
            "puzzle": GameType.PUZZLE,
            "解谜": GameType.PUZZLE,
            "传送门": GameType.PUZZLE,
            "shooter": GameType.SHOOTER,
            "射击": GameType.SHOOTER,
            "fps": GameType.SHOOTER,
            "strategy": GameType.STRATEGY,
            "策略": GameType.STRATEGY,
            "simulation": GameType.SIMULATION,
            "模拟": GameType.SIMULATION,
            "casual": GameType.CASUAL,
            "休闲": GameType.CASUAL,
            "益智": GameType.CASUAL,
            "adventure": GameType.ADVENTURE,
            "冒险": GameType.ADVENTURE,
        }

        for keyword, game_type in keyword_map.items():
            if keyword in response_lower:
                extracted_type = game_type
                break

        if extracted_type:
            return ExtractionResult(
                extracted={"game_type": extracted_type},
                confidence=0.9,
                needs_clarification=False
            )

        # 尝试匹配选项
        for opt_name, opt_desc in self.GAME_TYPE_OPTIONS:
            if opt_name in response or opt_desc in response:
                # 重新映射
                for keyword, game_type in keyword_map.items():
                    if keyword in opt_name.lower():
                        return ExtractionResult(
                            extracted={"game_type": game_type},
                            confidence=0.8,
                            needs_clarification=False
                        )

        return ExtractionResult(
            extracted={"game_type_other": response.strip()},
            confidence=0.5,
            needs_clarification=True
        )

    def _extract_visual_style(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取视觉风格"""
        response_lower = response.lower()
        style_map = {
            "pixel": VisualStyle.PIXEL_ART,
            "像素": VisualStyle.PIXEL_ART,
            "cartoon": VisualStyle.CARTOON,
            "卡通": VisualStyle.CARTOON,
            "动漫": VisualStyle.CARTOON,
            "写实": VisualStyle.REALISTIC,
            "realistic": VisualStyle.REALISTIC,
            "极简": VisualStyle.MINIMALIST,
            "minimalist": VisualStyle.MINIMALIST,
            "复古": VisualStyle.RETRO,
            "retro": VisualStyle.RETRO,
            "cyberpunk": VisualStyle.CYBERPUNK,
            "赛博": VisualStyle.CYBERPUNK,
            "fantasy": VisualStyle.FANTASY,
            "奇幻": VisualStyle.FANTASY,
            "abstract": VisualStyle.ABSTRACT,
            "抽象": VisualStyle.ABSTRACT,
        }

        for keyword, style in style_map.items():
            if keyword in response_lower:
                return ExtractionResult(
                    extracted={"visual_style": style},
                    confidence=0.9,
                    needs_clarification=False
                )

        return ExtractionResult(
            extracted={"visual_style_other": response.strip()},
            confidence=0.5,
            needs_clarification=True
        )

    def _extract_platforms(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取目标平台"""
        response_lower = response.lower()
        platforms = []

        platform_map = {
            "web": Platform.WEB_BROWSER,
            "浏览器": Platform.WEB_BROWSER,
            "h5": Platform.WEB_BROWSER,
            "windows": Platform.WINDOWS,
            "pc": Platform.WINDOWS,
            "android": Platform.ANDROID,
            "安卓": Platform.ANDROID,
            "ios": Platform.IOS,
            "苹果": Platform.IOS,
            "手机": [Platform.ANDROID, Platform.IOS],
        }

        for keyword, platform in platform_map.items():
            if keyword in response_lower:
                if isinstance(platform, list):
                    platforms.extend(platform)
                else:
                    platforms.append(platform)

        if platforms:
            # 去重
            unique_platforms = list(set(platforms))
            return ExtractionResult(
                extracted={"target_platforms": unique_platforms},
                confidence=0.9,
                needs_clarification=False
            )

        return ExtractionResult(
            extracted={},
            confidence=0,
            needs_clarification=True
        )

    def _extract_core_mechanics(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取核心玩法"""
        return ExtractionResult(
            extracted={
                "core_mechanics": response.strip(),
                "gameplay_keywords": self._extract_keywords(response)
            },
            confidence=0.8,
            needs_clarification=False
        )

    def _extract_protagonist(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取主角信息"""
        return ExtractionResult(
            extracted={"protagonist": response.strip()},
            confidence=0.8,
            needs_clarification=False
        )

    def _extract_win_condition(self, response: str, context: GameDesignContext) -> ExtractionResult:
        """从回复中提取胜利条件"""
        return ExtractionResult(
            extracted={"win_condition": response.strip()},
            confidence=0.8,
            needs_clarification=False
        )

    def _extract_keywords(self, text: str) -> list[str]:
        """提取玩法关键词"""
        keywords = []
        keyword_list = [
            "移动", "跳跃", "射击", "躲避", "收集", "消除",
            "合成", "升级", "解谜", "探索", "战斗", "建造",
            "养成", "经营", "节奏", "反应", "策略", "模拟"
        ]

        for kw in keyword_list:
            if kw in text:
                keywords.append(kw)

        return keywords


# 全局实例
inquiry_strategy = InquiryStrategy()
