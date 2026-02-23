"""Redis 连接管理 - 全局单例模式"""

import json
from typing import Any, Dict, List, Optional

import redis

from .config import settings


class RedisClient:
    """Redis 客户端封装"""

    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> None:
        """
        建立 Redis 连接
        """
        self._client = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
        # 验证连接
        self._client.ping()

    def get_client(self) -> redis.Redis:
        """获取 Redis 客户端实例"""
        if self._client is None:
            self.connect()
        return self._client

    def set_json(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        将字典以 JSON 形式存入 Redis

        Args:
            key: Redis key
            value: 要存储的字典
            ttl: 过期时间（秒），None表示永不过期

        Returns:
            是否成功
        """
        client = self.get_client()
        json_str = json.dumps(value, ensure_ascii=False)

        if ttl is not None:
            return client.setex(key, ttl, json_str)
        else:
            return client.set(key, json_str)

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从 Redis 获取 JSON 数据

        Args:
            key: Redis key

        Returns:
            解析后的字典，如果不存在返回 None
        """
        client = self.get_client()
        data = client.get(key)

        if data is None:
            return None

        return json.loads(data)

    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        按模式获取所有匹配的 key

        Args:
            pattern: 匹配模式，如 "heartbeat:*"

        Returns:
            key 列表
        """
        client = self.get_client()
        return list(client.scan_iter(match=pattern))


# 全局 Redis 客户端实例
redis_client = RedisClient()
