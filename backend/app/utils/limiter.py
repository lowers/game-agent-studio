"""P1: 登录限流配置 — 共享模块，避免 circular import。"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# 每个 IP 的限流规则
login_limiter = Limiter(key_func=get_remote_address)
