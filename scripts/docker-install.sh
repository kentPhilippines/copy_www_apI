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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        info "安装Docker..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
    else
        info "Docker已安装"
    fi
}

# 检查Docker Compose是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        info "安装Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        info "Docker Compose已安装"
    fi
}

# 创建必要的目录
setup_directories() {
    info "创建必要的目录..."
    mkdir -p data logs
    chmod 755 data logs
}

# 启动服务
start_services() {
    info "启动服务..."
    docker-compose up -d --build
}

# 主流程
main() {
    info "开始安装 Nginx Deploy API (Docker版本)..."
    
    # 检查Docker
    check_docker
    
    # 检查Docker Compose
    check_docker_compose
    
    # 创建目录
    setup_directories
    
    # 启动服务
    start_services
    
    info "安装完成！"
    info "API服务运行在: http://localhost:8000"
    info "API文档地址: http://localhost:8000/docs"
}

# 执行
main 