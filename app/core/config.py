"""配置管理模块 - 加载环境变量和YAML配置"""

import os
from typing import Any, Dict

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """环境变量配置"""

    redis_url: str = "redis://localhost:6379/0"
    file_monitor_plan_path: str = "app/config/file_monitor_plan.yaml"
    level_schedule_path: str = "app/config/level_schedule.yaml"

    class Config:
        env_file = ".env"


settings = Settings()


def load_yaml_config(path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件

    Args:
        path: YAML文件路径

    Returns:
        解析后的字典数据
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_file_monitor_plan() -> Dict[str, Any]:
    """获取文件监控计划配置"""
    return load_yaml_config(settings.file_monitor_plan_path)


def get_level_schedule() -> Dict[str, Any]:
    """获取运行等级调度配置"""
    return load_yaml_config(settings.level_schedule_path)
