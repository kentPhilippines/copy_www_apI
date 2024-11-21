#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 等待依赖服务就绪
wait_for_services() {
    info "等待依赖服务就绪..."
    
    # 启动Nginx
    nginx

    # 检查Nginx是否启动成功
    if ! pgrep -x "nginx" > /dev/null; then
        error "Nginx启动失败"
        exit 1
    fi
}

# 初始化应用
init_application() {
    info "初始化应用..."
    
    # 创建必要的目录
    mkdir -p /app/data /app/logs
    chown -R www-data:www-data /app/data /app/logs
    
    # 初始化数据库
    python -c "from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())"
}

# 启动应用
start_application() {
    info "启动应用..."
    
    # 使用uvicorn启动应用
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
}

# 主流程
main() {
    info "启动 Nginx Deploy API 服务..."
    
    # 等待依赖服务
    wait_for_services
    
    # 初始化应用
    init_application
    
    # 启动应用
    start_application
}

# 优雅退出
cleanup() {
    info "正在关闭服务..."
    nginx -s quit
    kill -TERM "$child" 2>/dev/null
}

# 注册退出钩子
trap cleanup SIGTERM SIGINT

# 执行主流程
main "$@" &
child=$!
wait "$child" 