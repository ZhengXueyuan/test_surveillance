"""模拟组件脚本 - 用于测试"""

import argparse
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import httpx


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
        self.declared_level: Optional[int] = 1
        self._running = False

    def send_heartbeat(self) -> bool:
        """
        发送心跳到监控服务器

        Returns:
            是否发送成功
        """
        url = f"{self.api_base}/heartbeat/{self.component_id}"

        # 使用带时区的时间戳（UTC）
        payload = {
            "process_exists": self.process_exists,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 只有等级有效时才添加
        if self.declared_level is not None:
            payload["declared_level"] = self.declared_level

        try:
            response = httpx.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            print(f"✅ 心跳发送成功 [{self.component_id}] level={self.declared_level}")
            return True
        except httpx.HTTPError as e:
            print(f"❌ 心跳发送失败 [{self.component_id}]: {e}")
            return False
        except Exception as e:
            print(f"❌ 心跳发送异常 [{self.component_id}]: {e}")
            return False

    def simulate_level_change(self, new_level: int) -> None:
        """模拟等级变更"""
        if 1 <= new_level <= 4:
            old_level = self.declared_level
            self.declared_level = new_level
            print(f"🔄 等级变更 [{self.component_id}]: {old_level} -> {new_level}")
        else:
            print(f"⚠️ 无效的等级 [{self.component_id}]: {new_level} (应为1-4)")

    def simulate_crash(self) -> None:
        """模拟进程崩溃"""
        self.process_exists = False
        print(f"💥 进程崩溃模拟 [{self.component_id}]")

    def simulate_recovery(self) -> None:
        """模拟进程恢复"""
        self.process_exists = True
        print(f"🔄 进程恢复模拟 [{self.component_id}]")

    def stop(self) -> None:
        """停止模拟组件"""
        self._running = False
        print(f"🛑 停止模拟组件 [{self.component_id}]")

    def run(self, max_iterations: Optional[int] = None) -> None:
        """
        运行模拟组件

        Args:
            max_iterations: 最大心跳次数，None表示无限循环
        """
        self._running = True
        iteration = 0

        print(f"🚀 启动模拟组件 [{self.component_id}]")
        print(f"   API: {self.api_base}")
        print(f"   心跳间隔: {self.heartbeat_interval}秒")
        print(f"   初始等级: {self.declared_level}")

        try:
            while self._running:
                # 发送心跳
                self.send_heartbeat()

                iteration += 1
                if max_iterations is not None and iteration >= max_iterations:
                    print(f"⏹️ 达到最大迭代次数 [{self.component_id}]")
                    break

                # 等待下次心跳
                time.sleep(self.heartbeat_interval)

        except KeyboardInterrupt:
            print(f"\n⏹️ 模拟组件被中断 [{self.component_id}]")
        finally:
            self._running = False


def main():
    """
    命令行入口，可启动多个模拟组件

    用法：
        python -m app.sim.component_sim trade_engine --level 4 --interval 30
        python -m app.sim.component_sim risk_checker --level 4 --interval 60
    """
    parser = argparse.ArgumentParser(
        description="模拟交易组件 - 用于测试监控系统"
    )

    parser.add_argument(
        "component_id",
        help="组件ID（如: trade_engine, risk_checker）"
    )

    parser.add_argument(
        "--level",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="初始运行等级 (1-4, 默认: 1)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="心跳间隔秒数 (默认: 30)"
    )

    parser.add_argument(
        "--api-base",
        default="http://localhost:8000/api/v1",
        help="监控API基础URL (默认: http://localhost:8000/api/v1)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="最大心跳次数，默认无限循环"
    )

    args = parser.parse_args()

    # 创建并启动模拟组件
    component = SimulatedComponent(
        component_id=args.component_id,
        api_base=args.api_base,
        heartbeat_interval=args.interval
    )

    # 设置初始等级
    component.declared_level = args.level

    # 启动
    try:
        component.run(max_iterations=args.max_iterations)
    except Exception as e:
        print(f"❌ 模拟组件异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
