"""心跳接收路由"""

import re
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..core.redis_client import redis_client
from ..core.time_utils import get_current_time_in_timezone
from ..models.heartbeat import HeartbeatRequest

router = APIRouter(prefix="/api/v1", tags=["heartbeat"])

# 组件ID格式验证：只允许字母、数字、下划线、连字符
COMPONENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@router.post("/heartbeat/{component_id}")
async def receive_heartbeat(
    component_id: str,
    request: HeartbeatRequest
) -> Dict[str, Any]:
    """
    接收组件心跳，存入 Redis

    Args:
        component_id: 组件ID（路径参数）
        request: 心跳请求体

    Returns:
        处理结果
    """
    # 验证 component_id 格式
    if not COMPONENT_ID_PATTERN.match(component_id):
        raise HTTPException(
            status_code=400,
            detail="组件ID格式无效，只允许字母、数字、下划线、连字符"
        )

    # 构建心跳数据
    current_time = get_current_time_in_timezone()
    heartbeat_data = {
        "component_id": component_id,
        "process_exists": request.process_exists,
        "timestamp": request.timestamp,
        "declared_level": request.declared_level,
        "received_at": current_time.isoformat()
    }

    # 存储到 Redis，TTL=300秒
    redis_key = f"heartbeat:{component_id}"
    redis_client.set_json(redis_key, heartbeat_data, ttl=300)

    return {
        "success": True,
        "message": "Heartbeat received",
        "component_id": component_id,
        "received_at": current_time.isoformat()
    }
