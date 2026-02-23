"""文件监控定时任务服务"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from croniter import croniter

from ..core.config import get_file_monitor_plan
from ..core.redis_client import redis_client
from ..core.time_utils import get_current_time_in_timezone

scheduler = BackgroundScheduler()


def check_file_compliance(
    file_path: str,
    expected_cron: str,
    grace_period_sec: int
) -> Dict[str, Any]:
    """
    检查单个文件的更新合规性

    Args:
        file_path: 文件绝对路径
        expected_cron: 预期更新 cron 表达式
        grace_period_sec: 宽限期（秒）

    Returns:
        文件状态字典
    """
    current_time = get_current_time_in_timezone()

    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 计算下次应更新时间
        itr = croniter(expected_cron, current_time)
        next_expected = itr.get_next(datetime)

        return {
            "path": file_path,
            "last_modified": None,
            "file_size": 0,
            "is_compliant": False,
            "next_expected_update": next_expected.isoformat(),
            "alert_message": "文件不存在"
        }

    # 获取文件修改时间
    try:
        mtime_timestamp = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime_timestamp)
        # 添加时区信息
        last_modified = last_modified.astimezone(current_time.tzinfo)

        file_size = os.path.getsize(file_path)
    except (OSError, IOError) as e:
        itr = croniter(expected_cron, current_time)
        next_expected = itr.get_next(datetime)

        return {
            "path": file_path,
            "last_modified": None,
            "file_size": 0,
            "is_compliant": False,
            "next_expected_update": next_expected.isoformat(),
            "alert_message": f"无法访问文件: {str(e)}"
        }

    # 使用 croniter 计算上次应该更新的时间
    itr = croniter(expected_cron, current_time)
    last_expected = itr.get_prev(datetime)

    # 考虑宽限期：文件修改时间应该 >= 上次预期更新时间 - 宽限期
    grace_delta = timedelta(seconds=grace_period_sec)
    effective_deadline = last_expected - grace_delta

    is_compliant = last_modified >= effective_deadline

    # 计算下次应更新时间
    next_expected = itr.get_next(datetime)

    # 生成告警信息
    alert_message = None
    if not is_compliant:
        overdue_seconds = (current_time - last_expected).total_seconds()
        alert_message = (
            f"文件已过期 {overdue_seconds:.0f} 秒，"
            f"上次更新: {last_modified.isoformat()},"
            f"应在: {last_expected.isoformat()} 前更新"
        )

    return {
        "path": file_path,
        "last_modified": last_modified.isoformat(),
        "file_size": file_size,
        "is_compliant": is_compliant,
        "next_expected_update": next_expected.isoformat(),
        "alert_message": alert_message
    }


def update_file_status_for_component(
    component_id: str,
    component_config: Dict
) -> None:
    """
    更新单个组件的文件监控状态

    Args:
        component_id: 组件ID
        component_config: 组件配置（包含 input_files, output_files）
    """
    current_time = get_current_time_in_timezone()

    input_files_status: List[Dict[str, Any]] = []
    output_files_status: List[Dict[str, Any]] = []

    # 处理输入文件
    for file_config in component_config.get("input_files", []):
        file_path = file_config["path"]
        expected_cron = file_config["expected_update_cron"]
        grace_period = file_config.get("grace_period_sec", 60)

        file_status = check_file_compliance(
            file_path,
            expected_cron,
            grace_period
        )
        file_status["type"] = "input"
        file_status["expected_update_cron"] = expected_cron

        input_files_status.append(file_status)

    # 处理输出文件
    for file_config in component_config.get("output_files", []):
        file_path = file_config["path"]
        expected_cron = file_config["expected_update_cron"]
        grace_period = file_config.get("grace_period_sec", 60)

        file_status = check_file_compliance(
            file_path,
            expected_cron,
            grace_period
        )
        file_status["type"] = "output"
        file_status["expected_update_cron"] = expected_cron

        output_files_status.append(file_status)

    # 计算整体健康状态
    all_files = input_files_status + output_files_status
    overall_file_health = all(f["is_compliant"] for f in all_files) if all_files else True

    # 构建存储结构
    status_data = {
        "component_id": component_id,
        "input_files": input_files_status,
        "output_files": output_files_status,
        "overall_file_health": overall_file_health,
        "checked_at": current_time.isoformat()
    }

    # 存入 Redis
    redis_key = f"file_status:{component_id}"
    redis_client.set_json(redis_key, status_data)


@scheduler.scheduled_job('cron', minute='*/1')  # 每分钟执行
def scheduled_file_check() -> None:
    """
    定时任务：每分钟检查所有组件的文件状态
    """
    try:
        config = get_file_monitor_plan()
        components = config.get("components", [])

        checked_count = 0
        for component in components:
            component_id = component.get("component_id")
            if not component_id:
                continue

            try:
                update_file_status_for_component(component_id, component)
                checked_count += 1
            except Exception as e:
                print(f"❌ 检查组件 {component_id} 文件状态失败: {e}")

        print(f"✅ 文件监控定时任务完成: 检查了 {checked_count} 个组件")

    except Exception as e:
        print(f"❌ 文件监控定时任务失败: {e}")


def start_file_checker() -> None:
    """启动文件监控定时任务"""
    scheduler.start()
    print("✅ 文件监控定时任务已启动 (每分钟执行)")


def stop_file_checker() -> None:
    """停止文件监控定时任务"""
    scheduler.shutdown()
    print("👋 文件监控定时任务已停止")
