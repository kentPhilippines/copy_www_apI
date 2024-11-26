import asyncio
from server_monitor import ServerMonitor
from config import WS_CONFIG
import logging
import os

async def start_monitor():
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    monitor = ServerMonitor(
        ws_url=WS_CONFIG['URL'],
        server_id=WS_CONFIG['SERVER_ID'],
        interval=WS_CONFIG['INTERVAL']
    )
    await monitor.run()

def run_monitor():
    try:
        asyncio.run(start_monitor())
    except KeyboardInterrupt:
        logging.info("监控程序已停止") 