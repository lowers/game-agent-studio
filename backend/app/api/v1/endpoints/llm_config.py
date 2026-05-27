"""
LLM 配置端点 — 允许用户动态配置 LLM 提供商和 API Key，并验证密钥有效性
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from app.api.v1.deps import require_current_user
from app.models.user import User

router = APIRouter()

ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class LlmConfigRequest(BaseModel):
    provider: str
    api_key: str | None = None
    base_url: str | None = None


class LlmVerifyRequest(BaseModel):
    """密钥验证请求"""
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class LlmVerifyResponse(BaseModel):
    """密钥验证响应"""
    valid: bool
    provider: str
    model: str
    error: str | None = None
    model_info: dict | None = None


# 合法提供商列表
VALID_PROVIDERS = {"deepseek", "sensenova", "openai", "ollama"}

# 各提供商常用模型映射
PROVIDER_MODELS = {
    "sensenova": ["sensenova-6.7-flash-lite", "sensenova-6.7-flash", "sensenova-1.5-pro"],
    "deepseek": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "ollama": ["llama3", "mistral", "gemma2"],
}


@router.post("/llm/configure")
async def configure_llm(
    payload: LlmConfigRequest,
    user: User = Depends(require_current_user),
):
    """动态配置 LLM 提供商和 API Key。"""
    provider = payload.provider.strip().lower()
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {payload.provider}")

    if provider != "ollama" and (not payload.api_key or len(payload.api_key.strip()) < 10):
        raise HTTPException(status_code=400, detail="Invalid API key")

    # 更新 .env 文件
    if ENV_FILE.exists():
        env_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    else:
        env_lines = []

    env_map: dict[str, str] = {}
    for line in env_lines:
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            env_map[key.strip()] = value.strip()

    # 根据提供商设置对应配置
    if provider == "sensenova":
        env_map["LLM_PROVIDER"] = "sensenova"
        env_map["LLM_API_KEY"] = payload.api_key or ""
        env_map["LLM_BASE_URL"] = ""  # 不覆盖 SenseNova 默认 URL
        env_map["SENSENOVA_API_KEY"] = payload.api_key or ""
        env_map["SENSENOVA_BASE_URL"] = "https://token.sensenova.cn/v1"
        env_map["SENSENOVA_MODEL"] = "sensenova-6.7-flash-lite"
    elif payload.provider == "ollama":
        env_map["LLM_PROVIDER"] = "ollama"
        env_map["LLM_BASE_URL"] = payload.base_url or "http://localhost:11434"
        env_map["LLM_API_KEY"] = ""
    else:
        # deepseek / openai
        env_map["LLM_PROVIDER"] = payload.provider
        env_map["LLM_API_KEY"] = payload.api_key or ""
        if payload.base_url:
            env_map["LLM_BASE_URL"] = payload.base_url

    # 写回 .env
    new_lines = []
    for line in env_lines:
        if "=" in line and not line.strip().startswith("#"):
            key, _, _ = line.partition("=")
            key = key.strip()
            if key in env_map:
                new_lines.append(f"{key}={env_map[key]}")
                continue
        new_lines.append(line)

    # 添加遗漏的键
    for key in list(env_map.keys()):
        if not any(l.startswith(f"{key}=") for l in new_lines):
            new_lines.append(f"{key}={env_map[key]}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "provider": payload.provider,
        "configured": True,
    }


@router.post("/llm/verify", response_model=LlmVerifyResponse)
async def verify_llm_key(
    payload: LlmVerifyRequest,
    user: User = Depends(require_current_user),
):
    """
    验证 LLM API Key 有效性。
    创建一个临时 ChatOpenAI 实例，发送一条简单的测试请求。
    返回具体错误原因（密钥无效、提供商不支持、模型不存在等）。
    """
    provider = payload.provider.strip().lower()

    # 1. 验证提供商
    if provider not in VALID_PROVIDERS:
        return LlmVerifyResponse(
            valid=False,
            provider=provider,
            model=payload.model or "",
            error=f"不支持的提供商: {provider}。支持的提供商: {', '.join(sorted(VALID_PROVIDERS))}",
        )

    # 2. 验证 API Key
    if provider != "ollama":
        if not payload.api_key or len(payload.api_key.strip()) < 10:
            return LlmVerifyResponse(
                valid=False,
                provider=provider,
                model=payload.model or "",
                error="API Key 无效或过短（至少需要 10 个字符）",
            )

    # 3. 验证模型（对于非 ollama）
    model = payload.model or PROVIDER_MODELS.get(provider, [""])[0]
    if provider != "ollama" and model:
        available_models = PROVIDER_MODELS.get(provider, [])
        # 如果模型不在推荐列表中，不直接报错，因为用户可能使用了其他合法模型
        # 但仍会返回可用模型列表作为参考
        pass

    # 4. 确定 base_url
    base_url = payload.base_url
    if provider == "sensenova":
        base_url = base_url or "https://token.sensenova.cn/v1"
    elif provider == "ollama":
        base_url = base_url or "http://localhost:11434"
    elif provider == "deepseek":
        base_url = base_url or "https://api.deepseek.com/v1"

    # 5. 创建临时 LLM 实例并测试
    api_key = payload.api_key or ""

    try:
        # 创建临时 LLM 实例（不影响全局配置）
        llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0,
            max_tokens=50,  # 仅测试，不需要大量 token
            request_timeout=30,  # 超时设为 30 秒
        )

        # 发送测试消息
        test_message = "Hello, this is a test message. Please respond with 'OK'."
        response = await llm.ainvoke(test_message)

        # 如果成功返回响应，说明密钥有效
        return LlmVerifyResponse(
            valid=True,
            provider=provider,
            model=model,
            error=None,
            model_info={
                "model": model,
                "input_tokens": response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0) if hasattr(response, 'response_metadata') else 0,
                "available_models": PROVIDER_MODELS.get(provider, []),
            },
        )

    except Exception as e:
        # 根据异常类型返回具体的错误信息
        error_msg = str(e).lower()

        if "unauthorized" in error_msg or "invalid_api_key" in error_msg or "401" in error_msg:
            error_detail = "API Key 无效或被拒绝。请检查密钥是否正确。"
        elif "not_found" in error_msg or "404" in error_msg:
            error_detail = f"模型 '{model}' 不存在或该提供商不支持此模型。"
        elif "connection" in error_msg or "timeout" in error_msg or "could not connect" in error_msg:
            if provider == "ollama":
                error_detail = "无法连接到 Ollama 服务。请检查 Ollama 是否已启动（默认端口 11434）。"
            else:
                error_detail = f"无法连接到 {provider} 的 API 服务。请检查网络连接或 base_url 配置。"
        elif "rate_limit" in error_msg or "too many requests" in error_msg or "429" in error_msg:
            error_detail = "API 调用频率超限。请稍后再试。"
        else:
            # 通用错误，返回简化的错误描述
            error_detail = f"验证失败: {e}"

        return LlmVerifyResponse(
            valid=False,
            provider=provider,
            model=model,
            error=error_detail,
            model_info={
                "available_models": PROVIDER_MODELS.get(provider, []),
            },
        )
