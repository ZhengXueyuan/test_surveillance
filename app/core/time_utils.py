"""时间处理工具 - 跨天逻辑、Cron解析"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

import pytz
from croniter import croniter


def parse_time(time_str: str) -> time:
    """
    将 "HH:MM" 字符串解析为 time 对象

    Args:
        time_str: 时间字符串，如 "09:15"

    Returns:
        time 对象
    """
    hour, minute = map(int, time_str.split(":"))
    return time(hour, minute)


def is_time_in_range(
    check_time: time,
    start_time: time,
    end_time: time
) -> bool:
    """
    判断时间是否在给定范围内（支持跨天）

    Args:
        check_time: 要检查的时间
        start_time: 范围开始时间
        end_time: 范围结束时间

    Returns:
        是否在范围内

    示例：
        - 15:30 - 09:00（跨天，表示夜间时段）
        - 09:00 - 15:00（不跨天）
    """
    if start_time <= end_time:
        # 不跨天
        return start_time <= check_time <= end_time
    else:
        # 跨天（例如 22:00 - 06:00）
        return check_time >= start_time or check_time <= end_time


def get_current_time_in_timezone(timezone: str = "Asia/Shanghai") -> datetime:
    """
    获取指定时区的当前时间

    Args:
        timezone: 时区名称

    Returns:
        当前时间的 datetime 对象
    """
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def is_cron_due(
    cron_expr: str,
    last_time: datetime,
    current_time: datetime
) -> bool:
    """
    判断在 last_time 到 current_time 之间是否有 cron 触发点

    Args:
        cron_expr: Cron 表达式
        last_time: 上次更新时间
        current_time: 当前时间

    Returns:
        是否应该有更新
    """
    itr = croniter(cron_expr, last_time)
    next_trigger = itr.get_next(datetime)
    return next_trigger <= current_time


def find_matching_schedule_rule(
    rules: List[Dict],
    current_time: datetime
) -> Optional[Dict]:
    """
    从规则列表中查找当前时间匹配的规则

    Args:
        rules: 规则列表，每个规则包含 start_time, end_time
        current_time: 当前时间

    Returns:
        匹配的规则字典，或 None
    """
    current_time_only = current_time.time()

    for rule in rules:
        start_time = parse_time(rule["start_time"])
        end_time = parse_time(rule["end_time"])

        if is_time_in_range(current_time_only, start_time, end_time):
            return rule

    return None


def get_next_cron_trigger(cron_expr: str, base_time: Optional[datetime] = None) -> datetime:
    """
    获取下次 cron 触发时间

    Args:
        cron_expr: Cron 表达式
        base_time: 基准时间，默认为当前时间

    Returns:
        下次触发时间
    """
    if base_time is None:
        base_time = get_current_time_in_timezone()

    itr = croniter(cron_expr, base_time)
    return itr.get_next(datetime)
