from typing import Dict, Any, Optional
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
        """初始化服务器监控器
        
        Args:
            ws_url: WebSocket服务器地址
            server_id: 服务器ID
            interval: 监控间隔（秒）
        """
        self.ws_url = ws_url
        self.server_id = server_id
        self.interval = interval
        self.hostname = socket.gethostname()
        
        # 配置日志
        self.logger = logging.getLogger("server_monitor")
        self.websocket = None

    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
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

    async def send_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """发送数据到WebSocket服务器
        
        Args:
            data_type: 数据类型
            data: 要发送的数据
        """
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

    async def run(self) -> None:
        """运行监控服务"""
        self.logger.info(f"开始监控服务器 {self.hostname}")
        
        while True:
            try:
                # 收集并发送系统指标
                metrics = self.get_system_metrics()
                if metrics:
                    await self.send_data('metrics', metrics)

                # 收集并发送服务状态
                services = self.get_service_status()
                if services:
                    await self.send_data('services', {'services': services})

            except Exception as e:
                self.logger.error(f"监控循环发生错误: {str(e)}")
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                await asyncio.sleep(5)
            
            await asyncio.sleep(self.interval) 