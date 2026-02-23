#!/usr/bin/env python3
"""
Market Data Feeder Simulator
=============================

模拟 market_data_feeder 组件，支持文件监控测试场景。

Usage:
    python sim/market_data_sim.py

Features:
    - 自动创建 ./data/market_data.csv
    - 每 30 秒发送心跳（declared_level=2）
    - 每 4 分钟更新文件内容，模拟真实数据写入
    - 记录关键事件日志

Requirements:
    - Python 3.10+
    - requests library (pip install requests)
    - FastAPI backend running on localhost:8000

Author: Generated for testing file monitoring
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import requests

# =============================================================================
# Configuration
# =============================================================================

COMPONENT_ID = "market_data_feeder"
API_BASE = "http://localhost:8000/api/v1"
HEARTBEAT_INTERVAL = 30  # seconds
FILE_UPDATE_INTERVAL = 240  # 4 minutes (slightly less than 5min cron cycle)

# File path (relative to project root)
DATA_FILE = "./data/market_data.csv"
DECLARED_LEVEL = 2

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def ensure_file_exists(file_path: str) -> bool:
    """
    Ensure the data file exists. Create directory and file if not present.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file exists or was created successfully
    """
    try:
        # Create directory if needed
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        
        # Create file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("timestamp,symbol,price,volume\n")
                f.write(f"{datetime.now(timezone.utc).isoformat()},AAPL,150.00,1000\n")
            logger.info(f"Created initial file: {file_path}")
        
        return True
        
    except OSError as e:
        logger.error(f"Failed to create file {file_path}: {e}")
        return False


def update_file(file_path: str) -> bool:
    """
    Update the data file with new content and fresh mtime.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if update was successful
    """
    try:
        # Generate new data row
        now = datetime.now(timezone.utc)
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        import random
        symbol = random.choice(symbols)
        price = round(random.uniform(100, 500), 2)
        volume = random.randint(1000, 100000)
        
        # Append new data
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{now.isoformat()},{symbol},{price},{volume}\n")
        
        # Update file mtime by touching it
        os.utime(file_path, None)
        
        logger.info(f"File updated: {file_path} - Added {symbol} @ ${price}")
        return True
        
    except (OSError, IOError) as e:
        logger.error(f"Failed to update file {file_path}: {e}")
        return False


def send_heartbeat(component_id: str, level: int, api_base: str) -> bool:
    """
    Send heartbeat to FastAPI backend.
    
    Args:
        component_id: Component identifier
        level: Declared run level
        api_base: API base URL
        
    Returns:
        True if heartbeat was sent successfully
    """
    url = f"{api_base}/heartbeat/{component_id}"
    
    payload = {
        "process_exists": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "declared_level": level
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5.0,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Heartbeat sent: {component_id} (level={level})")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.warning(f"Cannot connect to backend at {api_base}")
        return False
    except requests.exceptions.Timeout:
        logger.warning("Heartbeat request timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Heartbeat failed: {e}")
        return False


# =============================================================================
# Main Loop
# =============================================================================

def main():
    """Main execution loop."""
    logger.info("=" * 60)
    logger.info(f"Starting {COMPONENT_ID} simulator")
    logger.info(f"  API Base: {API_BASE}")
    logger.info(f"  Data File: {DATA_FILE}")
    logger.info(f"  Heartbeat Interval: {HEARTBEAT_INTERVAL}s")
    logger.info(f"  File Update Interval: {FILE_UPDATE_INTERVAL}s")
    logger.info("=" * 60)
    
    # Ensure data file exists
    if not ensure_file_exists(DATA_FILE):
        logger.error("Failed to initialize data file. Exiting.")
        sys.exit(1)
    
    # Track last execution times
    last_heartbeat = 0
    last_file_update = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Send heartbeat every HEARTBEAT_INTERVAL seconds
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat(COMPONENT_ID, DECLARED_LEVEL, API_BASE)
                last_heartbeat = current_time
            
            # Update file every FILE_UPDATE_INTERVAL seconds
            if current_time - last_file_update >= FILE_UPDATE_INTERVAL:
                update_file(DATA_FILE)
                last_file_update = current_time
            
            # Small sleep to prevent CPU spinning
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
