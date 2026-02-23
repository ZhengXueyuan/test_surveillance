你是一位 Python 全栈工程师，正在实现一套基于 Redis 的模拟交易组件监控系统。请按以下要求规划并生成代码骨架：

## 技术栈
- 后端：Python 3.10+，FastAPI
- 存储：Redis（使用 redis-py）
- 定时任务：APScheduler
- 配置：YAML 文件

## 核心需求
1. **心跳接收器**：
   - 路由：POST /api/v1/heartbeat/{component_id}
   - 请求体（JSON）：
     {
       "process_exists": bool,
       "timestamp": str (ISO8601),
       "declared_level": int?  // 可选，1-4
     }
   - 行为：将数据以 JSON 形式存入 Redis key `heartbeat:{component_id}`，设置 TTL 300 秒。

2. **文件监控计划**（file_monitor_plan.yaml）：
   - 定义每个组件的 input_files 和 output_files，含路径和 expected_update_cron。
   - 定时任务（每分钟）：
     - 读取 YAML；
     - 对每个文件，检查 os.path.getmtime；
     - 判断是否在 cron 允许的更新窗口内（使用 croniter）；
     - 写入 Redis key `file_status:{component_id}`，结构包含每个文件的 ok/last_mtime/expected_cron。

3. **运行等级计划**（level_schedule.yaml）：
   - 定义每个组件在不同时间段的 expected_level。
   - 定时任务（每分钟）：
     - 读取 YAML；
     - 获取当前时间；
     - 查找匹配的时间段，得到 expected_level；
     - 从 Redis 读取该组件最近的 heartbeat 数据，获取 declared_level（如有）；
     - 设定 observed_level = declared_level（模拟阶段简化）；
     - 判断 compliant = (observed_level == expected_level)；
     - 写入 Redis key `level_status:{component_id}`，包含：
       {
         "expected_level": int,
         "observed_level": int,
         "declared_level": int?,
         "compliant": bool,
         "schedule_rule": str,
         "last_check": ISO8601
       }

4. **统一状态 API**：
   - 路由：GET /api/v1/status
   - 返回：聚合所有 component_id 的 heartbeat + file_status + level_status，按组件分组。

5. **项目结构要求**：
   - /app
     - main.py                # FastAPI app
     - api/
       - heartbeat.py         # 心跳路由
       - status.py            # 聚合状态路由
     - services/
       - file_checker.py      # 文件检查定时任务
       - level_validator.py   # 等级验证定时任务
     - core/
       - config.py            # 加载 YAML 路径、Redis URL
       - redis_client.py      # 全局 Redis 连接
       - time_utils.py        # 时间解析、跨天逻辑
     - sim/
       - component_sim.py     # 模拟组件脚本（可选）

## 输出要求
- 不要生成完整代码，只需提供：
  a) 项目目录结构；
  b) 每个模块的核心函数签名和伪代码逻辑；
  c) Redis key 命名规范和 JSON 结构示例；
  d) FastAPI 路由定义（用 @app.post 等示意）。
- 使用清晰的 Markdown 格式。