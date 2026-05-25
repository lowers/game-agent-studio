"""状态存储抽象 — 为内存状态提供统一接口，支持未来切换到 Redis 等持久化后端。

解决的问题：
- AgentCoordinator._workflows 进程重启丢失
- PendingQuestions._questions/_responses/_events 进程重启丢失
- MasterChatAgent._sessions 进程重启丢失

使用方式：
    from app.services.state_store import get_state_store, StateStore

    store = get_state_store()
    await store.set("workflow:abc123", ctx_dict, ttl=3600)
    ctx_dict = await store.get("workflow:abc123")
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class StateStore(ABC):
    """状态存储抽象接口。"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取值，不存在返回 None。"""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置值，ttl 为秒数，None 表示永不过期。"""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除键，返回是否存在。"""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在。"""

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """列出匹配的键。支持简单前缀匹配：'workflow:*'。"""

    @abstractmethod
    async def clear(self) -> None:
        """清空所有数据（测试用）。"""


class InMemoryStateStore(StateStore):
    """内存实现 — 基于字典，带 TTL 支持。

    适用于单进程开发和测试。生产环境应切换到 RedisStateStore。
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}  # key -> timestamp
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        """检查键是否过期。"""
        import time
        exp = self._expiry.get(key)
        if exp is not None and time.monotonic() > exp:
            del self._data[key]
            del self._expiry[key]
            return True
        return False

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if self._is_expired(key):
                return None
            return self._data.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        import time
        async with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expiry[key] = time.monotonic() + ttl
            else:
                self._expiry.pop(key, None)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            existed = key in self._data
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return existed

    async def exists(self, key: str) -> bool:
        async with self._lock:
            if self._is_expired(key):
                return False
            return key in self._data

    async def keys(self, pattern: str = "*") -> list[str]:
        async with self._lock:
            # 清理过期键
            import time
            now = time.monotonic()
            expired = [k for k, exp in self._expiry.items() if now > exp]
            for k in expired:
                self._data.pop(k, None)
                del self._expiry[k]

            if pattern == "*":
                return list(self._data.keys())

            # 简单前缀匹配：'workflow:*' → 匹配 'workflow:' 开头的键
            if pattern.endswith(":*"):
                prefix = pattern[:-1]  # 'workflow:'
                return [k for k in self._data if k.startswith(prefix)]

            return [k for k in self._data if k == pattern]

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()
            self._expiry.clear()


class RedisStateStore(StateStore):
    """Redis 实现 — 基于 redis-py 异步客户端，支持持久化和多进程共享。

    适用于多进程/多容器生产环境。
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: Any = None  # redis.asyncio.Redis

    async def _ensure_connected(self):
        if self._redis is not None:
            return
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=False)
            await self._redis.ping()
            logger.info("RedisStateStore connected: %s", self._redis_url)
        except ImportError:
            raise RuntimeError(
                "redis-py is not installed. Install it with: pip install redis"
            )
        except Exception as e:
            logger.error("RedisStateStore connection failed: %s", e)
            raise

    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_connected()
        import json
        data = await self._redis.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data.decode("utf-8") if isinstance(data, bytes) else data

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self._ensure_connected()
        import json
        serialized = json.dumps(value, default=str)
        if ttl is not None:
            await self._redis.setex(key, ttl, serialized)
        else:
            await self._redis.set(key, serialized)

    async def delete(self, key: str) -> bool:
        await self._ensure_connected()
        result = await self._redis.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        await self._ensure_connected()
        return await self._redis.exists(key) > 0

    async def keys(self, pattern: str = "*") -> list[str]:
        await self._ensure_connected()
        redis_pattern = pattern.replace(":*", ":*")  # Redis 通配符兼容
        result = []
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor, match=redis_pattern, count=100)
            result.extend(k.decode("utf-8") if isinstance(k, bytes) else k for k in keys)
            if cursor == 0:
                break
        return result

    async def clear(self) -> None:
        await self._ensure_connected()
        await self._redis.flushdb()


# === 全局单例 ===

_store: Optional[StateStore] = None


def get_state_store() -> StateStore:
    """获取全局 StateStore 实例。

    优先使用 Redis（若配置了 REDIS_URL），否则回退到 InMemoryStateStore。
    """
    global _store
    if _store is not None:
        return _store

    from app.config import settings
    if settings.REDIS_URL:
        _store = RedisStateStore(settings.REDIS_URL)
        logger.info("StateStore initialized: RedisStateStore")
    else:
        _store = InMemoryStateStore()
        logger.info("StateStore initialized: InMemoryStateStore")
    return _store


def set_state_store(store: StateStore) -> None:
    """替换全局 StateStore（测试或切换到 Redis 时使用）。"""
    global _store
    _store = store
    logger.info("StateStore replaced: %s", type(store).__name__)
