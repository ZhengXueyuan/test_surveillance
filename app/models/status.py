"""状态响应模型"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FileStatus(BaseModel):
    """单个文件状态"""

    path: str
    type: str               # "input" 或 "output"
    expected_update_cron: str
    last_modified: Optional[str] = None
    file_size: int = 0
    is_compliant: bool
    next_expected_update: str
    alert_message: Optional[str] = None


class FileMonitorStatus(BaseModel):
    """文件监控状态"""

    component_id: str
    input_files: List[FileStatus]
    output_files: List[FileStatus]
    overall_file_health: bool
    checked_at: str         # ISO8601


class LevelStatus(BaseModel):
    """运行等级状态"""

    component_id: str
    expected_level: int
    observed_level: int
    declared_level: Optional[int] = None
    compliant: bool
    schedule_rule: Optional[str] = None
    last_check: str         # ISO8601


class HeartbeatStatus(BaseModel):
    """心跳状态"""

    component_id: str
    process_exists: bool
    last_heartbeat_at: str
    status: str             # "healthy" | "warning" | "critical" | "offline"
    declared_level: Optional[int] = None


class ComponentStatus(BaseModel):
    """单个组件聚合状态"""

    component_id: str
    heartbeat: Optional[HeartbeatStatus] = None
    file_status: Optional[FileMonitorStatus] = None
    level_status: Optional[LevelStatus] = None
    overall_status: str     # 综合状态


class StatusResponse(BaseModel):
    """统一状态 API 响应"""

    components: List[ComponentStatus]
    total_count: int
    healthy_count: int
    warning_count: int
    critical_count: int
    queried_at: str         # ISO8601
