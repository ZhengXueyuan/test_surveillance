# 模拟交易组件监控系统

一个基于 FastAPI + Vue 3 + Redis 的交易组件监控平台，支持心跳监控、文件更新检测和运行等级验证。

## 系统架构

```
┌─────────────┐      HTTP       ┌─────────────┐      ┌─────────────┐
│   Vue 3     │ ◄──────────────► │   FastAPI   │ ◄───► │    Redis    │
│  Frontend   │                  │   Backend   │       │    Store    │
└─────────────┘                  └─────────────┘       └─────────────┘
                                        ▲
                                        │ HTTP
                                 ┌──────┴──────┐
                                 │  Simulated  │
                                 │ Components  │
                                 └─────────────┘
```

## 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **Redis**: 6.0+
- **OS**: Linux / macOS / WSL2

## 快速开始

### 1. 克隆项目并进入目录

```bash
cd /path/to/test_surveillance
```

### 2. 启动 Redis

```bash
# 方式一：本地 Redis
redis-server

# 方式二：Docker
sudo docker run -d -p 6379:6379 redis:7-alpine
```

### 3. 启动后端服务

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 在项目根目录启动（重要！）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行，API 文档访问 http://localhost:8000/docs

### 4. 启动前端服务

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

### 5. （可选）启动模拟组件

```bash
source venv/bin/activate

# 启动 market_data_feeder（带文件更新模拟）
python sim/market_data_sim.py &

# 启动其他模拟组件
python -m app.sim.component_sim trade_engine --level 4 --interval 30 &
python -m app.sim.component_sim risk_checker --level 4 --interval 30 &
```

## 访问系统

- **监控面板**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 功能特性

- ✅ **心跳监控** - 实时检测组件存活状态
- ✅ **文件更新检测** - 监控输入/输出文件的新鲜度
- ✅ **运行等级验证** - 根据时间段验证组件等级合规性
- ✅ **趋势图表** - 健康分数历史趋势可视化
- ✅ **CSV 导出** - 一键导出监控数据
- ✅ **深色主题** - 现代化科技风格界面

## 项目结构

```
.
├── app/                          # 后端代码
│   ├── api/                      # API 路由
│   │   ├── heartbeat.py          # 心跳接收
│   │   └── status.py             # 状态查询
│   ├── config/                   # 配置文件
│   │   ├── file_monitor_plan.yaml    # 文件监控计划
│   │   └── level_schedule.yaml       # 等级调度计划
│   ├── core/                     # 核心模块
│   │   ├── config.py             # 配置加载
│   │   ├── redis_client.py       # Redis 连接
│   │   └── time_utils.py         # 时间工具
│   ├── models/                   # 数据模型
│   ├── services/                 # 定时任务
│   │   ├── file_checker.py       # 文件检查
│   │   └── level_validator.py    # 等级验证
│   ├── sim/                      # 模拟组件
│   └── main.py                   # 应用入口
├── src/                          # 前端代码
│   ├── components/
│   │   └── StatusBoard.vue       # 监控面板
│   ├── App.vue
│   └── main.js
├── sim/                          # 独立模拟脚本
│   └── market_data_sim.py        # 带文件更新的模拟器
├── data/                         # 模拟数据文件
├── config/                       # 配置文件
├── requirements.txt              # Python 依赖
├── package.json                  # Node.js 依赖
└── README.md                     # 本文件
```

## 退出与清理

### 停止前端

在运行 `npm run dev` 的终端中按 `Ctrl + C`

### 停止后端

在运行 `uvicorn` 的终端中按 `Ctrl + C`

### 停止模拟组件

```bash
# 停止所有模拟组件
pkill -f "component_sim"
pkill -f "market_data_sim"

# 或查找并停止特定进程
ps aux | grep component_sim
kill <PID>
```

### 停止 Redis

```bash
# 如果是本地启动
redis-cli shutdown

# 如果是 Docker
docker stop <redis_container_id>
```

### 一键清理脚本

```bash
#!/bin/bash
# cleanup.sh

echo "停止模拟组件..."
pkill -f "component_sim" 2>/dev/null
pkill -f "market_data_sim" 2>/dev/null

echo "停止前端 (如使用 nohup)..."
pkill -f "vite" 2>/dev/null

echo "清理完成！"
```

## 配置说明

### 环境变量

创建 `.env` 文件：

```env
REDIS_URL=redis://localhost:6379/0
FILE_MONITOR_PLAN_PATH=app/config/file_monitor_plan.yaml
LEVEL_SCHEDULE_PATH=app/config/level_schedule.yaml
```

### 文件监控计划

编辑 `app/config/file_monitor_plan.yaml`：

```yaml
components:
  - component_id: "trade_engine"
    input_files:
      - path: "./data/market_data.csv"
        expected_update_cron: "*/5 * * * *"
    output_files:
      - path: "./logs/trade_engine.log"
        expected_update_cron: "*/1 * * * *"
```

### 等级调度计划

编辑 `app/config/level_schedule.yaml`：

```yaml
components:
  - component_id: "trade_engine"
    rules:
      - start_time: "09:15"
        end_time: "11:30"
        expected_level: 4
```

## 常见问题

### Q: 后端启动报错 "Error loading ASGI app"
**A**: 确保在项目根目录运行 `uvicorn app.main:app`，而非 `app` 目录内

### Q: 前端提示 CORS 错误
**A**: 后端已配置 CORS，确保访问的是 http://localhost:5173 而非 127.0.0.1:5173

### Q: 图表不显示或报错
**A**: 检查浏览器控制台，确保 Chart.js CDN 可访问。必要时刷新页面

### Q: Redis 连接失败
**A**: 检查 Redis 是否运行：`redis-cli ping`，应返回 `PONG`

## 技术栈

- **后端**: FastAPI, Redis, APScheduler, Pydantic
- **前端**: Vue 3, Chart.js, Vite
- **协议**: HTTP REST, CORS
- **部署**: Uvicorn, Nginx (生产)

## License

MIT License
