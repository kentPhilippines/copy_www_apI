from __future__ import annotations
from typing import Dict, Any, Optional
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import websockets
import asyncio
import json
import logging
from datetime import datetime
import socket
import psutil
import os
import platform

class ServerMonitor:
    def __init__(self, ws_url: str, server_id: int, interval: int = 60) -> None:
        self.ws_url = ws_url
        self.server_id = server_id
        self.interval = interval
        self.hostname = socket.gethostname()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.websocket = None
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        try:
            self.websocket = await websockets.connect(
                f"{self.ws_url}/{self.server_id}",
                max_size=None,
                ping_interval=20,
                ping_timeout=60
            )
            await self.register_server()
            self.logger.info(f"WebSocket连接成功: {self.ws_url}")
            return True
        except Exception as e:
            self.logger.error(f"WebSocket连接失败: {str(e)}")
            return False

    async def register_server(self) -> None:
        """注册服务器信息"""
        system_info = {
            'hostname': self.hostname,
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'total_memory': psutil.virtual_memory().total,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        await self.send_data('register', system_info)

    def get_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            metrics = {
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
                },
                'memory': psutil.virtual_memory()._asdict(),
                'disk': {
                    'usage': {disk.mountpoint: psutil.disk_usage(disk.mountpoint)._asdict() 
                             for disk in psutil.disk_partitions(all=False)},
                    'io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                },
                'network': {
                    'connections': len(psutil.net_connections()),
                    'io': psutil.net_io_counters()._asdict()
                },
                'system': {
                    'boot_time': psutil.boot_time(),
                    'users': len(psutil.users())
                }
            }
            return metrics
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {str(e)}")
            return {}

    def get_service_status(self) -> Dict[str, Any]:
        """获取关键服务状态"""
        try:
            services = {
                'nginx': self._check_service_status('nginx'),
                'mysql': self._check_service_status('mysql'),
                'redis': self._check_service_status('redis'),
                # 添加其他需要监控的服务
            }
            return services
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {str(e)}")
            return {}

    def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """检查特定服务的状态"""
        try:
            service_pids = []
            for proc in psutil.process_iter(['name', 'pid', 'status']):
                if service_name in proc.info['name'].lower():
                    service_pids.append({
                        'pid': proc.info['pid'],
                        'status': proc.info['status']
                    })
            return {
                'running': len(service_pids) > 0,
                'processes': service_pids
            }
        except Exception as e:
            self.logger.error(f"检查服务 {service_name} 状态失败: {str(e)}")
            return {'running': False, 'error': str(e)}

    def collect_system_logs(self) -> Dict[str, Any]:
        """收集系统日志"""
        try:
            log_files = {
                'nginx': '/var/log/nginx/error.log',
                'system': '/var/log/syslog',
                # 添加其他需要监控的日志文件
            }
            
            logs = {}
            for log_name, log_path in log_files.items():
                if os.path.exists(log_path):
                    with open(log_path, 'r') as f:
                        # 只读取最后1000行
                        logs[log_name] = self._tail_file(f, 1000)
            return logs
        except Exception as e:
            self.logger.error(f"收集系统日志失败: {str(e)}")
            return {}

    def _tail_file(self, file, lines: int) -> list:
        """读取文件最后N行"""
        try:
            file.seek(0, 2)
            block_size = 1024
            blocks = []
            total_lines = 0
            
            while total_lines < lines and file.tell() > 0:
                seek_size = min(file.tell(), block_size)
                file.seek(-seek_size, 1)
                blocks.append(file.read(seek_size))
                total_lines += blocks[-1].count(b'\n')
                file.seek(-seek_size, 1)
                
            all_lines = ''.join(reversed(blocks)).splitlines()[-lines:]
            return all_lines
        except Exception as e:
            self.logger.error(f"读取文件失败: {str(e)}")
            return []

    async def send_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        if not self.websocket:
            if not await self.connect():
                return False
        
        try:
            message = {
                'type': data_type,
                'server_id': self.server_id,
                'hostname': self.hostname,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f"发送数据失败: {str(e)}")
            self.websocket = None
            return False

    async def run(self) -> None:
        self.logger.info(f"开始监控服务器 {self.hostname}")
        
        while True:
            try:
                async with self._lock:
                    await self._collect_and_send_data()
            except Exception as e:
                self.logger.error(f"监控循环发生错误: {str(e)}")
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                await asyncio.sleep(5)
            
            await asyncio.sleep(self.interval)

    async def _collect_and_send_data(self):
        """收集并发送所有监控数据"""
        metrics = self.get_system_metrics()
        if metrics:
            await self.send_data('metrics', metrics)

        services = self.get_service_status()
        if services:
            await self.send_data('services', {'services': services})

        logs = self.collect_system_logs()
        if logs:
            await self.send_data('logs', {'logs': logs})

def main():
    # 配置参数
    WS_URL = "ws://your-server:9001/ws"
    SERVER_ID = 1
    INTERVAL = 60  # 监控间隔（秒）

    # 启动监控
    loop = asyncio.get_event_loop()
    try:
        monitor = ServerMonitor(WS_URL, SERVER_ID, INTERVAL)
        loop.run_until_complete(monitor.run())
    except KeyboardInterrupt:
        print("监控程序已停止")
    finally:
        loop.close()

if __name__ == "__main__":
    main() 