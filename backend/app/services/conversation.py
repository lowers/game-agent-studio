"""对话需求采集服务 - 增强版。

支持：
1. 状态机驱动的多轮对话
2. 主动问询引导
3. 可行性评估和风险提示
4. 项目经验指导

基于原有的 GameDesignDoc 生成逻辑，扩展为主动问询模式。

注意：langchain_openai / langchain_core 的导入延迟到实际使用 LLM 时，
确保即使未安装 openai 包，fallback 模式也能正常使用。
"""

from app.config import settings
from app.schemas.game_design_doc import GameDesignDoc
from app.services.design_context import (
    ConversationSession,
    ConversationState,
    GameDesignContext,
)
from app.services.feasibility_evaluator import EvaluationResult, feasibility_evaluator
from app.services.inquiry_strategy import InquiryQuestion, inquiry_strategy

MAX_HISTORY_LENGTH = 20


class ProactiveConversationService:
    """主动问询对话服务"""

    def __init__(self):
        # 存储会话状态（从简单的消息列表改为完整的会话对象）
        self.sessions: dict[str, ConversationSession] = {}
        # 存储生成的设计文档
        self.docs: dict[str, GameDesignDoc] = {}
        # 🔴 修复：LLM 真正懒加载，仅在 _generate_natural_reply 时初始化
        # 支持 fallback 模式（无 LLM API Key 或未安装 openai 包）
        self._llm = None
        self._llm_initialized = False

    @property
    def llm(self):
        """懒加载 LLM，仅在需要时初始化"""
        if not self._llm_initialized:
            self._llm_initialized = True
            # 检查 LLM API Key 是否配置
            if not settings.active_api_key:
                # Fallback 模式：使用规则引擎生成回复
                self._llm = None
                return None
            # 尝试导入 LLM（可能未安装 openai 包）
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    api_key=settings.active_api_key,
                    base_url=settings.active_base_url,
                    model=settings.active_model,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                )
            except ImportError:
                # openai 包未安装，使用 fallback
                self._llm = None
        return self._llm

    def _get_or_create_session(self, session_id: str) -> ConversationSession:
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                state=ConversationState.INITIAL,
                context=GameDesignContext(session_id=session_id),
            )
        return self.sessions[session_id]

    async def chat(self, session_id: str, user_message: str) -> dict:
        """处理一轮对话，返回回复和状态信息。"""
        # 确保会话存在
        session = self._get_or_create_session(session_id)

        # 添加用户消息到历史
        session.add_message("user", user_message)

        # 根据当前状态处理输入
        response_data = await self._process_by_state(session, user_message)

        # 添加 AI 回复到历史
        if response_data.get("reply"):
            session.add_message("assistant", response_data["reply"])

        # 检查是否生成设计文档
        doc = None
        # 🔴 修复：在 fallback 模式下，当收集到最低可行信息时就生成 design_doc
        # 因为 fallback 模式可能不会走完完整的状态机
        should_generate_doc = (
            session.context.is_complete() or
            session.context.is_minimum_viable() or  # 新增：最低可行即可生成
            response_data.get("design_doc")
        )

        if should_generate_doc:
            doc = self._generate_design_doc(session.context)
            self.docs[session_id] = doc
            response_data["design_doc"] = doc.model_dump()
            # 如果已生成设计文档，标记为完成
            if doc.protagonist and doc.core_gameplay and doc.win_condition:
                session.state = ConversationState.COMPLETE

        return {
            "reply": response_data.get("reply", ""),
            "session_id": session_id,
            "state": session.state.value,
            "inquiry_topic": session.last_inquiry_topic,
            "design_doc": response_data.get("design_doc"),
            "evaluation": response_data.get("evaluation"),
            "is_complete": session.context.is_complete(),
        }

    async def _process_by_state(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """根据当前状态处理用户输入"""
        state = session.state

        # === 状态处理分支 ===
        if state == ConversationState.INITIAL:
            return await self._handle_initial(session, user_message)

        elif state == ConversationState.GATHERING_IDEA:
            return await self._handle_gathering_idea(session, user_message)

        elif state in [
            ConversationState.CLARIFY_GAME_TYPE,
            ConversationState.CLARIFY_CORE_MECHANICS,
            ConversationState.CLARIFY_CHARACTERS,
            ConversationState.CLARIFY_VISUAL,
            ConversationState.CLARIFY_TECHNICAL,
        ]:
            return await self._handle_clarification(session, user_message)

        elif state == ConversationState.EVALUATING:
            return await self._handle_evaluating(session, user_message)

        elif state == ConversationState.REFINE_WITH_ISSUES:
            return await self._handle_refinement(session, user_message)

        elif state == ConversationState.FINALIZING:
            return await self._handle_finalizing(session, user_message)

        elif state == ConversationState.COMPLETE:
            return {
                "reply": "设计文档已生成完成！您可以告诉我需要修改的部分，或者直接开始创建项目。",
            }

        # 默认：继续对话
        return await self._generate_followup(session)

    async def _handle_initial(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理初始状态 - 记录用户想法"""
        session.context.user_idea = user_message
        session.advance_state()

        # 生成第一个问询问题
        return await self._generate_followup(session)

    async def _handle_gathering_idea(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理想法收集状态"""
        # 追加用户想法
        session.context.user_idea += "\n" + user_message

        # 🔴 修复：在 fallback 模式下（无 LLM），主动从用户消息中提取信息
        # 这样可以让测试中的连续消息也能正确填充 context
        if self.llm is None:
            self._try_extract_from_message(session, user_message)

        session.inquiry_count += 1

        # 检查是否足够
        if len(user_message) > 50 or session.inquiry_count >= 2:
            session.advance_state()

        return await self._generate_followup(session)

    def _try_extract_from_message(self, session: ConversationSession, user_message: str):
        """从用户消息中尝试提取所有可能字段的信息（fallback 模式专用）"""
        context = session.context

        # 按优先级尝试提取
        # 1. 游戏类型
        if not context.game_type:
            extraction = inquiry_strategy.extract_from_response(
                "game_type", user_message, context
            )
            if extraction.extracted:
                for key, value in extraction.extracted.items():
                    setattr(context, key, value)

        # 2. 核心玩法
        if not context.core_mechanics:
            extraction = inquiry_strategy.extract_from_response(
                "core_mechanics", user_message, context
            )
            if extraction.extracted:
                for key, value in extraction.extracted.items():
                    setattr(context, key, value)

        # 3. 胜利条件（关键词匹配）
        if not context.win_condition:
            win_keywords = ["胜利", "赢", "通关", "结束", "终点", "完成", "获胜", "过关"]
            if any(kw in user_message for kw in win_keywords):
                context.win_condition = user_message.strip()

        # 4. 主角（如果包含"角色"、"主角"、"玩家"等词）
        if not context.protagonist:
            protagonist_keywords = ["角色", "主角", "玩家", "控制", "操作"]
            if any(kw in user_message for kw in protagonist_keywords):
                context.protagonist = user_message.strip()


    async def _handle_clarification(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理澄清状态 - 从用户回复中提取信息"""
        topic = session.last_inquiry_topic

        if topic:
            # 使用问询策略提取信息
            extraction = inquiry_strategy.extract_from_response(
                topic, user_message, session.context
            )

            # 更新上下文
            for key, value in extraction.extracted.items():
                setattr(session.context, key, value)

            # 如果已经提取到信息，不再需要澄清
            if not extraction.needs_clarification and extraction.extracted:
                # 继续尝试提取其他字段
                self._try_extract_from_message(session, user_message)

        session.inquiry_count += 1
        session.advance_state()

        return await self._generate_followup(session)

    async def _handle_evaluating(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理评估状态 - 进行可行性评估"""
        # 进行可行性评估
        evaluation = feasibility_evaluator.evaluate(session.context)

        # 更新复杂度评分
        session.context.complexity_score = evaluation.complexity_score

        if evaluation.has_critical_issues():
            # 有严重问题，需要用户确认
            session.state = ConversationState.REFINE_WITH_ISSUES
            # stay in REFINE_WITH_ISSUES so _handle_refinement can process it  # 设为 REFINE_WITH_ISSUES
            return {
                "reply": self._format_evaluation_warning(evaluation),
                "evaluation": self._format_evaluation(evaluation),
            }

        session.advance_state()
        return await self._generate_followup(session)

    async def _handle_refinement(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理优化状态 - 用户确认或调整方案"""
        # 检查用户是否接受建议
        if any(word in user_message.lower() for word in ["好的", "可以", "同意", "没问题", "ok", "yes"]):
            # 用户接受，执行建议
            # TODO: 应用具体的修改
            session.advance_state()
        else:
            # 用户拒绝或有其他想法
            session.inquiry_count += 1
            # 继续询问

        return await self._generate_followup(session)

    async def _handle_finalizing(
        self,
        session: ConversationSession,
        user_message: str
    ) -> dict:
        """处理最终确认状态"""
        # 检查用户是否有最后的修改
        if any(word in user_message.lower() for word in ["修改", "改变", "调整", "不同"]):
            session.inquiry_count += 1
            return await self._generate_followup(session)

        session.state = ConversationState.COMPLETE
        return {
            "reply": "太好了！设计文档已生成。您可以查看下方文档，确认无误后点击'创建项目'开始开发。",
        }

    async def _generate_followup(self, session: ConversationSession) -> dict:
        """生成跟进回复（追问或确认）"""
        # 检查是否应该继续追问
        if not session.should_continue_inquiry():
            # 达到最大追问次数，直接进入评估
            session.state = ConversationState.EVALUATING
            return await self._generate_followup(session)

        # 进行可行性评估（用于生成针对性的问题）
        evaluation = feasibility_evaluator.evaluate(session.context)

        # 获取下一个问题
        question = inquiry_strategy.get_next_question(session, evaluation)

        if not question:
            # 没有更多问题，进入评估
            session.state = ConversationState.EVALUATING
            return await self._generate_followup(session)

        # 更新最后问询主题
        session.last_inquiry_topic = question.topic

        # 使用 LLM 生成自然的回复
        reply = await self._generate_natural_reply(session, question)

        return {
            "reply": reply,
            "evaluation": self._format_evaluation(evaluation) if evaluation.has_warnings() else None,
        }

    async def _generate_natural_reply(
        self,
        session: ConversationSession,
        question: InquiryQuestion
    ) -> str:
        """使用 LLM 或 fallback 规则生成自然的追问回复"""
        # 🔴 修复：处理 LLM 不可用的 fallback 模式
        if self.llm is None:
            # Fallback：使用模板生成回复
            return self._generate_fallback_reply(session, question)

        # 使用 LLM 生成回复
        # 构建提示
        context_summary = self._summarize_context(session.context)

        prompt = f"""你是一个经验丰富的游戏策划，正在和用户对话收集游戏设计需求。

当前收集到的信息：
{context_summary}

你需要问用户一个问题来继续收集信息：
{question.question}

要求：
1. 语言自然、友好，像朋友聊天
2. 不要一次问太多问题，最多1-2个
3. 如果有选项，可以给出选项让用户选择
4. 可以适当解释为什么问这个问题
5. 用中文回答"""

        # 检查是否有选项
        if question.options:
            options_text = "\n".join([f"  - {opt}" for opt in question.options])
            prompt += f"\n\n可选方案：\n{options_text}"

        # 懒加载 LLM 消息类型
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        return response.content.strip()

    def _generate_fallback_reply(self, session: ConversationSession, question: InquiryQuestion) -> str:
        """无 LLM 时的 fallback 回复生成（规则引擎）"""
        import random

        # 根据状态生成不同风格的回复
        if session.state == ConversationState.INITIAL:
            return f"好的，听起来很有趣！{question.question}"

        elif session.state == ConversationState.GATHERING_IDEA:
            templates = [
                f"明白了！{question.question}",
                f"不错的想法！{question.question}",
                f"我在记下来... {question.question}",
            ]
            return random.choice(templates)

        elif session.state in [
            ConversationState.CLARIFY_GAME_TYPE,
            ConversationState.CLARIFY_CORE_MECHANICS,
            ConversationState.CLARIFY_CHARACTERS,
            ConversationState.CLARIFY_VISUAL,
            ConversationState.CLARIFY_TECHNICAL,
        ]:
            templates = [
                f"收到！这很关键。{question.question}",
                f"让我确认一下... {question.question}",
                f"好的，{question.question}",
            ]
            return random.choice(templates)

        elif session.state == ConversationState.EVALUATING:
            return f"让我思考一下这个设计的可行性... {question.question}"

        else:
            return f"继续完善中... {question.question}"

    def _summarize_context(self, context: GameDesignContext) -> str:
        """总结当前上下文"""
        lines = []

        if context.game_type:
            lines.append(f"- 游戏类型：{context.game_type.value if hasattr(context.game_type, 'value') else context.game_type}")

        if context.core_mechanics:
            lines.append(f"- 核心玩法：{context.core_mechanics[:50]}...")

        if context.protagonist:
            lines.append(f"- 主角：{context.protagonist[:30]}...")

        if context.win_condition:
            lines.append(f"- 胜利条件：{context.win_condition[:30]}...")

        if context.visual_style:
            lines.append(f"- 视觉风格：{context.visual_style.value if hasattr(context.visual_style, 'value') else context.visual_style}")

        if context.target_platforms:
            platforms = [p.value if hasattr(p, 'value') else p for p in context.target_platforms]
            lines.append(f"- 目标平台：{', '.join(platforms)}")

        missing = context.get_missing_fields()
        if missing:
            lines.append(f"- 还需要补充：{', '.join(missing)}")

        return "\n".join(lines) if lines else "（刚开始收集信息）"

    def _format_evaluation(self, evaluation: EvaluationResult) -> dict:
        """格式化评估结果"""
        return {
            "complexity_score": evaluation.complexity_score,
            "complexity_label": feasibility_evaluator.get_complexity_label(evaluation.complexity_score),
            "risk_level": evaluation.risk_level,
            "is_feasible": evaluation.is_feasible,
            "issues": [
                {"severity": i.severity, "message": i.message, "suggestion": i.suggestion}
                for i in evaluation.issues
            ],
            "warnings": evaluation.warnings,
            "suggestions": evaluation.suggestions,
        }

    def _format_evaluation_warning(self, evaluation: EvaluationResult) -> str:
        """格式化评估警告"""
        warnings = []

        for issue in evaluation.issues:
            if issue.severity == "critical":
                warnings.append(f"⚠️ {issue.message}")
                warnings.append(f"   建议：{issue.suggestion}")
            elif issue.severity == "warning":
                warnings.append(f"💡 {issue.message}")

        return "\n".join(warnings)

    def _generate_design_doc(self, context: GameDesignContext) -> GameDesignDoc:
        """从上下文生成设计文档"""
        return GameDesignDoc(
            game_type=(
                context.game_type.value if isinstance(context.game_type, object) and hasattr(context.game_type, 'value')
                else str(context.game_type) if context.game_type else ""
            ),
            protagonist=context.protagonist,
            core_gameplay=context.core_mechanics,
            enemies_collectibles=context.enemies_collectibles,
            win_condition=context.win_condition,
        )

    def get_doc(self, session_id: str) -> GameDesignDoc | None:
        """获取设计文档"""
        return self.docs.get(session_id)

    def clear_session(self, session_id: str):
        """清除会话"""
        self.sessions.pop(session_id, None)
        self.docs.pop(session_id, None)

    # === 兼容旧接口 ===
    async def chat_legacy(self, session_id: str, user_message: str) -> dict:
        """兼容旧接口 - 保持原有的简单对话模式"""
        self._get_or_create_session(session_id)
        return await self.chat(session_id, user_message)


# === 保持旧接口兼容 ===
def get_conversation_service() -> ProactiveConversationService:
    """懒加载获取 conversation_service，避免导入时即初始化 LLM。"""
    # 使用函数级全局变量实现单例懒加载
    if not hasattr(get_conversation_service, "_instance"):
        get_conversation_service._instance = ProactiveConversationService()
    return get_conversation_service._instance


# 为了兼容直接导入 conversation_service 的旧代码，提供一个代理对象
class _LazyConversationService:
    """代理对象，将方法调用转发到懒加载的真实实例。"""
    def __getattr__(self, name):
        return getattr(get_conversation_service(), name)
    async def chat(self, session_id: str, user_message: str) -> dict:
        return await get_conversation_service().chat(session_id, user_message)
    async def chat_legacy(self, session_id: str, user_message: str) -> dict:
        return await get_conversation_service().chat_legacy(session_id, user_message)
    def get_doc(self, session_id: str) -> GameDesignDoc | None:
        return get_conversation_service().get_doc(session_id)
    def clear_session(self, session_id: str):
        get_conversation_service().clear_session(session_id)

conversation_service = _LazyConversationService()
