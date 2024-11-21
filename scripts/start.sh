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

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        error "虚拟环境不存在，请先运行 install.sh"
        exit 1
    fi
fi

# 检查必要的服务
check_services() {
    info "检查必要的服务..."
    
    # 检查Nginx
    if ! systemctl is-active --quiet nginx; then
        warn "Nginx未运行，尝试启动..."
        systemctl start nginx
    fi
    
    # 检查目录权限
    if [ ! -w "/etc/nginx/sites-available" ]; then
        error "没有Nginx配置目录的写入权限"
        exit 1
    fi
}

# 创建必要的目录
setup_directories() {
    info "检查必要的目录..."
    
    # 创建数据和日志目录
    mkdir -p data logs
    
    # 设置权限
    chmod 755 data logs
}

# 启动API服务
start_api() {
    info "启动API服务..."
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        error "端口8000已被占用"
        exit 1
    fi
    
    # 启动服务
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# 主流程
main() {
    info "启动 Nginx Deploy API 服务..."
    
    # 检查服务
    check_services
    
    # 检查目录
    setup_directories
    
    # 启动API
    start_api
}

# 执行
main