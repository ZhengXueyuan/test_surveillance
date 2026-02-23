"""统一状态查询路由"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from ..core.redis_client import redis_client
from ..core.time_utils import get_current_time_in_timezone
from ..models.status import (
    ComponentStatus,
    FileMonitorStatus,
    HeartbeatStatus,
    LevelStatus,
    StatusResponse,
)

router = APIRouter(prefix="/api/v1", tags=["status"])

# 状态优先级（用于计算综合状态）
STATUS_PRIORITY = {
    "offline": 0,
    "critical": 1,
    "warning": 2,
    "healthy": 3,
    "unknown": -1
}

# 心跳间隔（秒）- 用于计算心跳状态
DEFAULT_HEARTBEAT_INTERVAL = 30


def calculate_heartbeat_status(heartbeat_data: Dict[str, Any]) -> str:
    """
    根据心跳数据计算状态

    Args:
        heartbeat_data: Redis 中的心跳数据

    Returns:
        状态字符串：healthy / warning / critical / offline
    """
    if not heartbeat_data:
        return "offline"

    process_exists = heartbeat_data.get("process_exists", False)
    if not process_exists:
        return "critical"

    last_heartbeat_str = heartbeat_data.get("timestamp")
    if not last_heartbeat_str:
        return "offline"

    try:
        last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
        current_time = get_current_time_in_timezone()

        # 计算时间差（秒）
        time_diff = (current_time - last_heartbeat).total_seconds()

        # 根据时间差判断状态
        interval = DEFAULT_HEARTBEAT_INTERVAL

        if time_diff < interval * 1.5:
            return "healthy"
        elif time_diff < interval * 3:
            return "warning"
        else:
            return "critical"

    except (ValueError, TypeError):
        return "offline"


def get_worst_status(statuses: List[str]) -> str:
    """
    获取最差的状态

    Args:
        statuses: 状态列表

    Returns:
        最差的状态
    """
    if not statuses:
        return "unknown"

    # 按优先级排序，返回最差的（优先级最低的）
    return min(statuses, key=lambda s: STATUS_PRIORITY.get(s, -1))


def build_component_status(component_id: str) -> ComponentStatus:
    """
    构建单个组件的聚合状态

    Args:
        component_id: 组件ID

    Returns:
        组件聚合状态
    """
    # 查询各类状态
    heartbeat_data = redis_client.get_json(f"heartbeat:{component_id}")
    file_status_data = redis_client.get_json(f"file_status:{component_id}")
    level_status_data = redis_client.get_json(f"level_status:{component_id}")

    # 构建心跳状态
    heartbeat_status: Optional[HeartbeatStatus] = None
    if heartbeat_data:
        hb_status = calculate_heartbeat_status(heartbeat_data)
        heartbeat_status = HeartbeatStatus(
            component_id=component_id,
            process_exists=heartbeat_data.get("process_exists", False),
            last_heartbeat_at=heartbeat_data.get("timestamp", ""),
            status=hb_status,
            declared_level=heartbeat_data.get("declared_level")
        )

    # 构建文件状态
    file_status: Optional[FileMonitorStatus] = None
    if file_status_data:
        file_status = FileMonitorStatus(**file_status_data)

    # 构建等级状态
    level_status: Optional[LevelStatus] = None
    if level_status_data:
        level_status = LevelStatus(**level_status_data)

    # 计算综合状态
    all_statuses: List[str] = []
    if heartbeat_status:
        all_statuses.append(heartbeat_status.status)
    if file_status:
        all_statuses.append(
            "healthy" if file_status.overall_file_health else "warning"
        )
    if level_status:
        all_statuses.append(
            "healthy" if level_status.compliant else "warning"
        )

    overall_status = get_worst_status(all_statuses) if all_statuses else "unknown"

    return ComponentStatus(
        component_id=component_id,
        heartbeat=heartbeat_status,
        file_status=file_status,
        level_status=level_status,
        overall_status=overall_status
    )


@router.get("/status", response_model=StatusResponse)
async def get_all_status() -> StatusResponse:
    """
    获取所有组件的聚合状态

    Returns:
        包含所有组件心跳、文件状态、等级状态的聚合响应
    """
    # 获取所有心跳 key
    heartbeat_keys = redis_client.get_keys_by_pattern("heartbeat:*")

    # 提取组件ID列表
    component_ids: List[str] = []
    for key in heartbeat_keys:
        # key 格式: heartbeat:{component_id}
        component_id = key.replace("heartbeat:", "")
        component_ids.append(component_id)

    # 也去 file_status 和 level_status 中查找组件
    file_keys = redis_client.get_keys_by_pattern("file_status:*")
    for key in file_keys:
        component_id = key.replace("file_status:", "")
        if component_id not in component_ids:
            component_ids.append(component_id)

    level_keys = redis_client.get_keys_by_pattern("level_status:*")
    for key in level_keys:
        component_id = key.replace("level_status:", "")
        if component_id not in component_ids:
            component_ids.append(component_id)

    # 构建每个组件的状态
    components: List[ComponentStatus] = []
    for component_id in sorted(component_ids):
        component_status = build_component_status(component_id)
        components.append(component_status)

    # 统计各类状态数量
    healthy_count = sum(1 for c in components if c.overall_status == "healthy")
    warning_count = sum(1 for c in components if c.overall_status == "warning")
    critical_count = sum(
        1 for c in components
        if c.overall_status in ["critical", "offline"]
    )

    current_time = get_current_time_in_timezone()

    return StatusResponse(
        components=components,
        total_count=len(components),
        healthy_count=healthy_count,
        warning_count=warning_count,
        critical_count=critical_count,
        queried_at=current_time.isoformat()
    )


@router.get("/status/{component_id}")
async def get_component_status(component_id: str) -> ComponentStatus:
    """
    获取单个组件的详细状态

    Args:
        component_id: 组件ID

    Returns:
        组件聚合状态
    """
    # 检查是否存在该组件的任何数据
    heartbeat_data = redis_client.get_json(f"heartbeat:{component_id}")
    file_status_data = redis_client.get_json(f"file_status:{component_id}")
    level_status_data = redis_client.get_json(f"level_status:{component_id}")

    if not any([heartbeat_data, file_status_data, level_status_data]):
        raise HTTPException(
            status_code=404,
            detail=f"组件不存在: {component_id}"
        )

    return build_component_status(component_id)
