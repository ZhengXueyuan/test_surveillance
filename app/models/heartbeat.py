"""心跳相关 Pydantic 模型"""

from typing import Optional

from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    """心跳请求体模型"""

    process_exists: bool = Field(..., description="进程是否存在")
    timestamp: str = Field(..., description="ISO8601 格式时间戳")
    declared_level: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="声明的运行等级(1-4)"
    )


class HeartbeatData(BaseModel):
    """存储在 Redis 中的心跳数据结构"""

    component_id: str
    process_exists: bool
    timestamp: str          # ISO8601
    declared_level: Optional[int] = None
    received_at: str        # ISO8601，服务器接收时间
