"""JWT 认证 — 用户注册、登录、Token 验证。"""
import logging
import re
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from pydantic import BaseModel, Field, field_validator

from app.config import settings

logger = logging.getLogger(__name__)

# JWT 配置 — 从 settings 独立读取，不再依赖 LLM_API_KEY
JWT_SECRET = settings.JWT_SECRET
if not JWT_SECRET or JWT_SECRET == "change-me-in-production":
    import logging
    _logger = logging.getLogger(__name__)
    _logger.warning("JWT_SECRET is not set or using default value! This is INSECURE in production.")
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES


class TokenData(BaseModel):
    """JWT payload 结构。"""
    user_id: int
    email: str | None = None
    exp: datetime | None = None


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str


class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8, description="密码至少8个字符")
    name: str = ""

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """密码强度验证：至少包含字母和数字。"""
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("密码必须包含至少一个字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# === 密码工具 ===

def hash_password(password: str) -> str:
    """哈希密码（使用 bcrypt 直接调用，避免 passlib 兼容问题）。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# === JWT 工具 ===

def create_access_token(user_id: int, email: str | None = None) -> str:
    """生成 JWT access token。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenData | None:
    """解码并验证 JWT token，失败返回 None。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(
            user_id=payload["user_id"],
            email=payload.get("email"),
            exp=payload.get("exp"),
        )
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("JWT token invalid")
        return None
