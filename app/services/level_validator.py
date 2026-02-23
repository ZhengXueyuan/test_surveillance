"""运行等级验证定时任务服务"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler

from ..core.config import get_level_schedule
from ..core.redis_client import redis_client
from ..core.time_utils import (
    find_matching_schedule_rule,
    get_current_time_in_timezone,
)

scheduler = BackgroundScheduler()


def get_expected_level(
    component_config: Dict,
    current_time: datetime
) -> Tuple[int, Optional[str]]:
    """
    获取组件在指定时间的期望等级

    Args:
        component_config: 组件配置
        current_time: 当前时间

    Returns:
        (expected_level: int, rule_name: Optional[str])
    """
    rules = component_config.get("rules", [])

    if not rules:
        # 没有规则时返回默认值
        default_level = component_config.get("non_trading_day_level", 1)
        return default_level, None

    # 查找匹配的规则
    matching_rule = find_matching_schedule_rule(rules, current_time)

    if matching_rule:
        return (
            matching_rule["expected_level"],
            matching_rule.get("name")
        )
    else:
        # 没有匹配到规则，使用非交易日默认等级
        default_level = component_config.get("non_trading_day_level", 1)
        return default_level, None


def get_declared_level_from_heartbeat(component_id: str) -> Optional[int]:
    """
    从 Redis 获取组件声明的运行等级

    Args:
        component_id: 组件ID

    Returns:
        declared_level，如果不存在返回 None
    """
    heartbeat_data = redis_client.get_json(f"heartbeat:{component_id}")

    if heartbeat_data is None:
        return None

    declared_level = heartbeat_data.get("declared_level")

    # 如果声明的等级不是 1-4 的有效值，返回 None
    if declared_level is not None and not (1 <= declared_level <= 4):
        return None

    return declared_level


def update_level_status_for_component(
    component_id: str,
    component_config: Dict
) -> None:
    """
    更新单个组件的等级验证状态

    Args:
        component_id: 组件ID
        component_config: 组件配置
    """
    current_time = get_current_time_in_timezone()

    # 获取期望等级
    expected_level, rule_name = get_expected_level(
        component_config,
        current_time
    )

    # 获取声明的等级
    declared_level = get_declared_level_from_heartbeat(component_id)

    # 观察到的等级（模拟阶段简化：等于声明的等级）
    observed_level = declared_level if declared_level is not None else 0

    # 判断合规性
    compliant = observed_level == expected_level

    # 构建存储结构
    status_data = {
        "component_id": component_id,
        "expected_level": expected_level,
        "observed_level": observed_level,
        "declared_level": declared_level,
        "compliant": compliant,
        "schedule_rule": rule_name,
        "last_check": current_time.isoformat()
    }

    # 存入 Redis
    redis_key = f"level_status:{component_id}"
    redis_client.set_json(redis_key, status_data)


@scheduler.scheduled_job('cron', minute='*/1')  # 每分钟执行
def scheduled_level_check() -> None:
    """
    定时任务：每分钟检查所有组件的等级合规性
    """
    try:
        config = get_level_schedule()
        components = config.get("components", [])

        checked_count = 0
        for component in components:
            component_id = component.get("component_id")
            if not component_id:
                continue

            try:
                update_level_status_for_component(component_id, component)
                checked_count += 1
            except Exception as e:
                print(f"❌ 检查组件 {component_id} 等级状态失败: {e}")

        print(f"✅ 等级验证定时任务完成: 检查了 {checked_count} 个组件")

    except Exception as e:
        print(f"❌ 等级验证定时任务失败: {e}")


def start_level_validator() -> None:
    """启动等级验证定时任务"""
    scheduler.start()
    print("✅ 等级验证定时任务已启动 (每分钟执行)")


def stop_level_validator() -> None:
    """停止等级验证定时任务"""
    scheduler.shutdown()
    print("👋 等级验证定时任务已停止")
