import asyncio
from server_monitor import ServerMonitor
from config import WS_CONFIG
import logging
import os
import sys

class MonitorService:
    def __init__(self):
        self.logger = logging.getLogger("monitor_service")
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/monitor.log'),
                logging.StreamHandler()
            ]
        )

    async def start(self):
        """启动监控服务"""
        try:
            self.logger.info("Starting monitor service...")
            monitor = ServerMonitor(
                ws_url=WS_CONFIG['URL'],
                server_id=WS_CONFIG['SERVER_ID'],
                interval=WS_CONFIG['INTERVAL']
            )
            await monitor.run()
        except Exception as e:
            self.logger.error(f"Monitor service failed: {str(e)}")
            raise

def start_monitor_service():
    """启动监控服务的入口函数"""
    service = MonitorService()
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(service.start())
    except KeyboardInterrupt:
        logging.info("Monitor service stopped by user")
    except Exception as e:
        logging.error(f"Monitor service error: {str(e)}")
    finally:
        loop.close()

if __name__ == "__main__":
    start_monitor_service() 