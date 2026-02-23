"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import heartbeat, status
from .core.redis_client import redis_client
from .services.file_checker import (
    scheduler as file_scheduler,
    start_file_checker,
    stop_file_checker,
)
from .services.level_validator import (
    scheduler as level_scheduler,
    start_level_validator,
    stop_level_validator,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    # 1. 连接 Redis
    try:
        redis_client.connect()
        print("✅ Redis 连接成功")
    except Exception as e:
        print(f"⚠️ Redis 连接失败: {e}")
        # 继续启动，允许在运行时再重试连接

    # 2. 启动定时任务
    try:
        start_file_checker()
    except Exception as e:
        print(f"⚠️ 文件监控定时任务启动失败: {e}")

    try:
        start_level_validator()
    except Exception as e:
        print(f"⚠️ 等级验证定时任务启动失败: {e}")

    yield

    # 关闭时执行
    # 清理资源
    print("👋 应用关闭，清理资源")

    # 停止定时任务
    try:
        stop_file_checker()
    except Exception as e:
        print(f"⚠️ 停止文件监控定时任务失败: {e}")

    try:
        stop_level_validator()
    except Exception as e:
        print(f"⚠️ 停止等级验证定时任务失败: {e}")


app = FastAPI(
    title="模拟交易组件监控系统",
    description="监控模拟交易组件的心跳、文件更新和运行等级",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS - 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(heartbeat.router)
app.include_router(status.router)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    health_info = {
        "status": "ok",
        "version": "1.0.0",
        "services": {}
    }

    # 检查 Redis 连接
    try:
        redis_client.get_client().ping()
        health_info["services"]["redis"] = "connected"
    except Exception as e:
        health_info["services"]["redis"] = f"disconnected: {e}"

    # 检查定时任务状态
    health_info["services"]["file_checker"] = (
        "running" if file_scheduler.running else "stopped"
    )
    health_info["services"]["level_validator"] = (
        "running" if level_scheduler.running else "stopped"
    )

    return health_info


@app.get("/")
async def root():
    """根路径重定向到文档"""
    return {
        "message": "模拟交易组件监控系统 API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
