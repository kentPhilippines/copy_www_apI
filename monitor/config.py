import os

# WebSocket配置
WS_CONFIG = {
    'URL': os.getenv('WS_URL', 'ws://localhost:9001/ws'),
    'SERVER_ID': int(os.getenv('SERVER_ID', '1')),
    'INTERVAL': int(os.getenv('MONITOR_INTERVAL', '60')),  # 监控间隔（秒）
}

# 日志配置
LOG_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE': 'logs/server_monitor.log'
}

# 监控服务列表
MONITOR_SERVICES = [
    'nginx',
    'mysql',
    'redis',
    # 添加其他需要监控的服务
]

# 日志文件配置
LOG_FILES = {
    'nginx': '/var/log/nginx/error.log',
    'system': '/var/log/syslog',
    # 添加其他需要监控的日志文件
} 