# 模拟交易组件监控系统 - Python 实现规划

## 1. 项目目录结构

```
/app
├── __init__.py
├── main.py                      # FastAPI 应用入口
├── api/
│   ├── __init__.py
│   ├── heartbeat.py             # 心跳接收路由
│   └── status.py                # 聚合状态查询路由
├── services/
│   ├── __init__.py
│   ├── file_checker.py          # 文件监控定时任务
│   └── level_validator.py       # 等级验证定时任务
├── core/
│   ├── __init__.py
│   ├── config.py                # 配置加载（YAML路径、Redis URL）
│   ├── redis_client.py          # Redis 连接管理
│   └── time_utils.py            # 时间处理工具（跨天逻辑等）
├── models/
│   ├── __init__.py
│   ├── heartbeat.py             # Pydantic 数据模型
│   └── status.py                # 状态响应模型
├── config/
│   ├── file_monitor_plan.yaml   # 文件监控计划配置
│   └── level_schedule.yaml      # 运行等级调度配置
└── sim/
    ├── __init__.py
    └── component_sim.py         # 模拟组件脚本（用于测试）

/requirements.txt                # 依赖列表
/README.md                       # 项目说明
```

---

## 2. 各模块核心函数签名与伪代码

### 2.1 /app/core/config.py

```python
"""配置管理模块 - 加载环境变量和YAML配置"""

from pydantic_settings import BaseSettings
from typing import Dict, List, Any
import yaml
import os

class Settings(BaseSettings):
    """环境变量配置"""
    redis_url: str = "redis://localhost:6379/0"
    file_monitor_plan_path: str = "config/file_monitor_plan.yaml"
    level_schedule_path: str = "config/level_schedule.yaml"
    
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
    # 伪代码：
    # 1. 检查文件是否存在
    # 2. 使用 yaml.safe_load 解析
    # 3. 返回配置字典
    pass

def get_file_monitor_plan() -> Dict[str, Any]:
    """获取文件监控计划配置"""
    return load_yaml_config(settings.file_monitor_plan_path)

def get_level_schedule() -> Dict[str, Any]:
    """获取运行等级调度配置"""
    return load_yaml_config(settings.level_schedule_path)
```

---

### 2.2 /app/core/redis_client.py

```python
"""Redis 连接管理 - 全局单例模式"""

import redis
import json
from typing import Optional, Any, Dict
from .config import settings

class RedisClient:
    """Redis 客户端封装"""
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls) -> 'RedisClient':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> None:
        """
        建立 Redis 连接
        """
        # 伪代码：
        # 1. 从 settings 获取 redis_url
        # 2. redis.from_url(redis_url, decode_responses=True)
        # 3. 验证连接（ping）
        pass
    
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
        # 伪代码：
        # 1. json.dumps(value) 序列化
        # 2. self._client.setex(key, ttl, json_str) 或 set
        pass
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从 Redis 获取 JSON 数据
        
        Args:
            key: Redis key
            
        Returns:
            解析后的字典，如果不存在返回 None
        """
        # 伪代码：
        # 1. self._client.get(key)
        # 2. 如果存在，json.loads 反序列化
        pass
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        按模式获取所有匹配的 key
        
        Args:
            pattern: 匹配模式，如 "heartbeat:*"
            
        Returns:
            key 列表
        """
        # 伪代码：
        # 1. self._client.keys(pattern)
        # 2. 返回列表
        pass

# 全局 Redis 客户端实例
redis_client = RedisClient()
```

---

### 2.3 /app/core/time_utils.py

```python
"""时间处理工具 - 跨天逻辑、Cron解析"""

from datetime import datetime, time
from typing import Optional, Tuple
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
    # 伪代码：
    # 1. 分割 hour, minute
    # 2. 返回 time(hour, minute)
    pass

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
    # 伪代码：
    # 1. 如果 start_time <= end_time：
    #       返回 start_time <= check_time <= end_time
    # 2. 否则（跨天）：
    #       返回 check_time >= start_time 或 check_time <= end_time
    pass

def get_current_time_in_timezone(timezone: str = "Asia/Shanghai") -> datetime:
    """
    获取指定时区的当前时间
    
    Args:
        timezone: 时区名称
        
    Returns:
        当前时间的 datetime 对象
    """
    # 伪代码：
    # 1. pytz.timezone(timezone)
    # 2. datetime.now(tz)
    pass

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
    # 伪代码：
    # 1. croniter(cron_expr, last_time)
    # 2. 获取 next(last_time)
    # 3. 返回 next_trigger <= current_time
    pass

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
    # 伪代码：
    # 1. 遍历 rules
    # 2. 对每个规则，解析 start_time, end_time
    # 3. 使用 is_time_in_range 检查 current_time 是否在范围内
    # 4. 返回第一个匹配的规则
    pass
```

---

### 2.4 /app/models/heartbeat.py

```python
"""心跳相关 Pydantic 模型"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

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
```

---

### 2.5 /app/models/status.py

```python
"""状态响应模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

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
```

---

### 2.6 /app/api/heartbeat.py

```python
"""心跳接收路由"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..models.heartbeat import HeartbeatRequest, HeartbeatData
from ..core.redis_client import redis_client
from ..core.time_utils import get_current_time_in_timezone

router = APIRouter(prefix="/api/v1", tags=["heartbeat"])

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
    # 伪代码逻辑：
    # 1. 验证 component_id 格式（只允许字母、数字、下划线、连字符）
    # 2. 构建 HeartbeatData：
    #    - component_id: component_id
    #    - process_exists: request.process_exists
    #    - timestamp: request.timestamp
    #    - declared_level: request.declared_level
    #    - received_at: 当前 ISO8601 时间
    # 3. Redis key: f"heartbeat:{component_id}"
    # 4. 存储 JSON，TTL=300 秒
    # 5. 返回 {"success": True, "message": "Heartbeat received"}
    pass
```

---

### 2.7 /app/api/status.py

```python
"""统一状态查询路由"""

from fastapi import APIRouter
from typing import List, Dict, Any
from ..models.status import StatusResponse, ComponentStatus
from ..core.redis_client import redis_client
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["status"])

def calculate_heartbeat_status(heartbeat_data: Dict) -> str:
    """
    根据心跳数据计算状态
    
    Args:
        heartbeat_data: Redis 中的心跳数据
        
    Returns:
        状态字符串：healthy / warning / critical / offline
    """
    # 伪代码逻辑：
    # 1. 获取当前时间和 last_heartbeat_at
    # 2. 计算差值（秒）
    # 3. 假设 heartbeat_interval_sec = 30（可从配置读取）
    # 4. 根据设计文档的状态计算逻辑返回对应状态
    pass

@router.get("/status", response_model=StatusResponse)
async def get_all_status() -> StatusResponse:
    """
    获取所有组件的聚合状态
    
    Returns:
        包含所有组件心跳、文件状态、等级状态的聚合响应
    """
    # 伪代码逻辑：
    # 1. 获取所有 heartbeat keys: redis_client.get_keys_by_pattern("heartbeat:*")
    # 2. 对每个 key，提取 component_id
    # 3. 查询该组件的三类状态：
    #    - heartbeat: redis_client.get_json(f"heartbeat:{component_id}")
    #    - file_status: redis_client.get_json(f"file_status:{component_id}")
    #    - level_status: redis_client.get_json(f"level_status:{component_id}")
    # 4. 构建 ComponentStatus 对象
    # 5. 计算 overall_status（取最差的那个状态）
    # 6. 统计各类状态数量
    # 7. 返回 StatusResponse
    pass

@router.get("/status/{component_id}")
async def get_component_status(component_id: str) -> ComponentStatus:
    """
    获取单个组件的详细状态
    
    Args:
        component_id: 组件ID
        
    Returns:
        组件聚合状态
    """
    # 伪代码：
    # 1. 查询该组件的 heartbeat、file_status、level_status
    # 2. 如果不存在任何数据，返回 404
    # 3. 否则构建并返回 ComponentStatus
    pass
```

---

### 2.8 /app/services/file_checker.py

```python
"""文件监控定时任务服务"""

import os
from datetime import datetime
from typing import Dict, Any, List
from croniter import croniter
from apscheduler.schedulers.background import BackgroundScheduler

from ..core.config import get_file_monitor_plan, settings
from ..core.redis_client import redis_client
from ..core.time_utils import get_current_time_in_timezone, is_cron_due

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
    # 伪代码逻辑：
    # 1. 检查文件是否存在：os.path.exists(file_path)
    # 2. 如果不存在：
    #    - 返回 is_compliant=False, alert_message="文件不存在"
    # 3. 获取文件修改时间：os.path.getmtime(file_path)
    # 4. 转换为 datetime 对象
    # 5. 使用 croniter 计算上次应该更新的时间：
    #    - itr = croniter(expected_cron, current_time)
    #    - last_expected = itr.get_prev(datetime)
    # 6. 判断：last_modified >= last_expected - grace_period_sec
    # 7. 计算 next_expected_update（下次应更新时间）
    # 8. 返回文件状态字典
    pass

def update_file_status_for_component(component_id: str, component_config: Dict) -> None:
    """
    更新单个组件的文件监控状态
    
    Args:
        component_id: 组件ID
        component_config: 组件配置（包含 input_files, output_files）
    """
    # 伪代码逻辑：
    # 1. 初始化 input_files_status = [], output_files_status = []
    # 2. 遍历 input_files：
    #    - 调用 check_file_compliance
    #    - type = "input"
    #    - 添加到列表
    # 3. 遍历 output_files：
    #    - 同样处理，type = "output"
    # 4. overall_file_health = 所有文件的 is_compliant 都是 True
    # 5. 构建存储结构：
    #    {
    #      "component_id": component_id,
    #      "input_files": [...],
    #      "output_files": [...],
    #      "overall_file_health": overall_file_health,
    #      "checked_at": ISO8601
    #    }
    # 6. 存入 Redis：key = f"file_status:{component_id}"
    pass

@scheduler.scheduled_job('cron', minute='*/1')  # 每分钟执行
def scheduled_file_check() -> None:
    """
    定时任务：每分钟检查所有组件的文件状态
    """
    # 伪代码逻辑：
    # 1. 读取配置：config = get_file_monitor_plan()
    # 2. 遍历 config["components"]：
    #    - component_id = comp["component_id"]
    #    - 调用 update_file_status_for_component(component_id, comp)
    # 3. 记录日志：打印检查了多少个组件
    pass

def start_file_checker() -> None:
    """启动文件监控定时任务"""
    scheduler.start()
```

---

### 2.9 /app/services/level_validator.py

```python
"""运行等级验证定时任务服务"""

from datetime import datetime
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler

from ..core.config import get_level_schedule, settings
from ..core.redis_client import redis_client
from ..core.time_utils import (
    get_current_time_in_timezone, 
    find_matching_schedule_rule
)

scheduler = BackgroundScheduler()

def get_expected_level(component_config: Dict, current_time: datetime) -> tuple:
    """
    获取组件在指定时间的期望等级
    
    Args:
        component_config: 组件配置
        current_time: 当前时间
        
    Returns:
        (expected_level: int, rule_name: Optional[str])
    """
    # 伪代码逻辑：
    # 1. 获取 rules = component_config.get("rules", [])
    # 2. 调用 find_matching_schedule_rule(rules, current_time)
    # 3. 如果匹配到规则：
    #    - 返回 (rule["expected_level"], rule.get("name"))
    # 4. 如果没有匹配：
    #    - 返回 (component_config.get("non_trading_day_level", 1), None)
    pass

def get_declared_level_from_heartbeat(component_id: str) -> Optional[int]:
    """
    从 Redis 获取组件声明的运行等级
    
    Args:
        component_id: 组件ID
        
    Returns:
        declared_level，如果不存在返回 None
    """
    # 伪代码逻辑：
    # 1. heartbeat_data = redis_client.get_json(f"heartbeat:{component_id}")
    # 2. 如果存在，返回 heartbeat_data.get("declared_level")
    # 3. 否则返回 None
    pass

def update_level_status_for_component(component_id: str, component_config: Dict) -> None:
    """
    更新单个组件的等级验证状态
    
    Args:
        component_id: 组件ID
        component_config: 组件配置
    """
    # 伪代码逻辑：
    # 1. current_time = get_current_time_in_timezone()
    # 2. expected_level, rule_name = get_expected_level(component_config, current_time)
    # 3. declared_level = get_declared_level_from_heartbeat(component_id)
    # 4. observed_level = declared_level（模拟阶段简化）
    # 5. 如果 observed_level 为 None：
    #    - observed_level = 0（表示未知/未报告）
    # 6. compliant = (observed_level == expected_level)
    # 7. 构建存储结构：
    #    {
    #      "component_id": component_id,
    #      "expected_level": expected_level,
    #      "observed_level": observed_level,
    #      "declared_level": declared_level,
    #      "compliant": compliant,
    #      "schedule_rule": rule_name,
    #      "last_check": current_time.isoformat()
    #    }
    # 8. 存入 Redis：key = f"level_status:{component_id}"
    pass

@scheduler.scheduled_job('cron', minute='*/1')  # 每分钟执行
def scheduled_level_check() -> None:
    """
    定时任务：每分钟检查所有组件的等级合规性
    """
    # 伪代码逻辑：
    # 1. 读取配置：config = get_level_schedule()
    # 2. 遍历 config["components"]：
    #    - component_id = comp["component_id"]
    #    - 调用 update_level_status_for_component(component_id, comp)
    # 3. 记录日志
    pass

def start_level_validator() -> None:
    """启动等级验证定时任务"""
    scheduler.start()
```

---

### 2.10 /app/main.py

```python
"""FastAPI 应用入口"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api import heartbeat, status
from .services.file_checker import start_file_checker, scheduler as file_scheduler
from .services.level_validator import start_level_validator, scheduler as level_scheduler
from .core.redis_client import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    # 1. 连接 Redis：redis_client.connect()
    # 2. 启动文件检查定时任务：start_file_checker()
    # 3. 启动等级验证定时任务：start_level_validator()
    
    yield
    
    # 关闭时执行
    # 1. 关闭定时任务：file_scheduler.shutdown(), level_scheduler.shutdown()
    # 2. 关闭 Redis 连接

app = FastAPI(
    title="模拟交易组件监控系统",
    description="监控模拟交易组件的心跳、文件更新和运行等级",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(heartbeat.router)
app.include_router(status.router)

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### 2.11 /app/sim/component_sim.py

```python
"""模拟组件脚本 - 用于测试"""

import requests
import time
import random
from datetime import datetime
from typing import Optional

class SimulatedComponent:
    """模拟交易组件"""
    
    def __init__(
        self, 
        component_id: str, 
        api_base: str = "http://localhost:8000/api/v1",
        heartbeat_interval: int = 30
    ):
        self.component_id = component_id
        self.api_base = api_base
        self.heartbeat_interval = heartbeat_interval
        self.process_exists = True
        self.declared_level = 1
    
    def send_heartbeat(self) -> bool:
        """
        发送心跳到监控服务器
        
        Returns:
            是否发送成功
        """
        # 伪代码逻辑：
        # 1. 构建请求体：
        #    {
        #      "process_exists": self.process_exists,
        #      "timestamp": datetime.now().isoformat(),
        #      "declared_level": self.declared_level
        #    }
        # 2. POST 请求：f"{self.api_base}/heartbeat/{self.component_id}"
        # 3. 返回响应状态
        pass
    
    def simulate_level_change(self, new_level: int) -> None:
        """模拟等级变更"""
        self.declared_level = new_level
    
    def simulate_crash(self) -> None:
        """模拟进程崩溃"""
        self.process_exists = False
    
    def run(self) -> None:
        """
        运行模拟组件
        """
        # 伪代码逻辑：
        # 1. 循环执行：
        #    - send_heartbeat()
        #    - time.sleep(self.heartbeat_interval)
        #    - 随机模拟一些状态变化（可选）
        pass

def main():
    """
    命令行入口，可启动多个模拟组件
    
    用法：
        python -m app.sim.component_sim trade_engine --level 4 --interval 30
    """
    # 伪代码：
    # 1. 解析命令行参数
    # 2. 创建 SimulatedComponent
    # 3. 调用 run()
    pass

if __name__ == "__main__":
    main()
```

---

## 3. Redis Key 命名规范与 JSON 结构

### 3.1 Key 命名规范

| 数据类型 | Key 格式 | 示例 |
|----------|----------|------|
| 心跳数据 | `heartbeat:{component_id}` | `heartbeat:trade_engine` |
| 文件状态 | `file_status:{component_id}` | `file_status:trade_engine` |
| 等级状态 | `level_status:{component_id}` | `level_status:trade_engine` |

### 3.2 JSON 结构示例

#### heartbeat:{component_id}
```json
{
  "component_id": "trade_engine",
  "process_exists": true,
  "timestamp": "2026-02-23T10:30:00+08:00",
  "declared_level": 4,
  "received_at": "2026-02-23T10:30:01+08:00"
}
```

#### file_status:{component_id}
```json
{
  "component_id": "trade_engine",
  "input_files": [
    {
      "path": "/data/market_data.csv",
      "type": "input",
      "expected_update_cron": "0 */5 * * *",
      "last_modified": "2026-02-23T10:25:00+08:00",
      "file_size": 1024000,
      "is_compliant": true,
      "next_expected_update": "2026-02-23T10:30:00+08:00",
      "alert_message": null
    }
  ],
  "output_files": [
    {
      "path": "/logs/trade_engine.log",
      "type": "output",
      "expected_update_cron": "*/1 * * * *",
      "last_modified": "2026-02-23T10:29:55+08:00",
      "file_size": 51200,
      "is_compliant": true,
      "next_expected_update": "2026-02-23T10:31:00+08:00",
      "alert_message": null
    }
  ],
  "overall_file_health": true,
  "checked_at": "2026-02-23T10:30:00+08:00"
}
```

#### level_status:{component_id}
```json
{
  "component_id": "trade_engine",
  "expected_level": 4,
  "observed_level": 4,
  "declared_level": 4,
  "compliant": true,
  "schedule_rule": "continuous_trading",
  "last_check": "2026-02-23T10:30:00+08:00"
}
```

---

## 4. FastAPI 路由定义

```python
# /app/main.py 中的路由汇总

from fastapi import FastAPI

app = FastAPI()

# ========== 心跳路由 ==========
# POST /api/v1/heartbeat/{component_id}
# 接收组件心跳，存入 Redis，TTL=300秒
@app.post("/api/v1/heartbeat/{component_id}")
async def receive_heartbeat(component_id: str, request: HeartbeatRequest):
    pass

# ========== 状态查询路由 ==========
# GET /api/v1/status
# 获取所有组件的聚合状态
@app.get("/api/v1/status")
async def get_all_status() -> StatusResponse:
    pass

# GET /api/v1/status/{component_id}
# 获取单个组件的详细状态
@app.get("/api/v1/status/{component_id}")
async def get_component_status(component_id: str) -> ComponentStatus:
    pass

# ========== 健康检查 ==========
# GET /health
# 系统健康检查
@app.get("/health")
async def health_check():
    pass
```

---

## 5. 依赖列表 (requirements.txt)

```txt
# Web 框架
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# 数据验证
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Redis
redis>=5.0.0

# 定时任务
apscheduler>=3.10.0

# Cron 解析
croniter>=2.0.0

# 时区处理
pytz>=2023.3

# YAML 解析
pyyaml>=6.0.1

# HTTP 客户端（模拟组件使用）
httpx>=0.25.0
```

---

## 6. 启动与测试流程

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 Redis 运行
redis-server

# 3. 启动监控服务
python -m app.main

# 4. 在另一个终端启动模拟组件
python -m app.sim.component_sim trade_engine --level 4
python -m app.sim.component_sim risk_checker --level 4

# 5. 测试 API
curl http://localhost:8000/api/v1/status
curl -X POST http://localhost:8000/api/v1/heartbeat/test_component \
  -H "Content-Type: application/json" \
  -d '{"process_exists": true, "timestamp": "2026-02-23T10:00:00+08:00", "declared_level": 4}'
```

---

*文档生成时间: 2026-02-23*
