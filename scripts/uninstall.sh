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

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    error "请使用root权限运行此脚本"
    exit 1
fi

# 停止服务
stop_services() {
    info "停止服务..."
    
    # 停止可能运行的uvicorn进程
    pkill -f uvicorn || true
    
    # 停止Nginx（如果需要）
    read -p "是否停止Nginx服务？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl stop nginx
    fi
}

# 清理文件
cleanup_files() {
    info "清理文件..."
    
    # 删除虚拟环境
    rm -rf venv
    
    # 删除数据和日志
    read -p "是否删除数据和日志？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf data logs
    fi
    
    # 清理Nginx配置
    read -p "是否清理Nginx配置？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f /etc/nginx/sites-enabled/*
        rm -f /etc/nginx/sites-available/*
    fi
}

# 卸载依赖
uninstall_dependencies() {
    info "卸载依赖..."
    
    read -p "是否卸载系统依赖（nginx, certbot等）？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f /etc/debian_version ]; then
            apt-get remove -y nginx certbot python3-certbot-nginx
        elif [ -f /etc/redhat-release ]; then
            yum remove -y nginx certbot python3-certbot-nginx
        fi
    fi
}

# 主流程
main() {
    info "开始卸载 Nginx Deploy API..."
    
    # 确认卸载
    read -p "此操作将删除所有相关文件和配置，是否继续？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "取消卸载"
        exit 0
    fi
    
    # 停止服务
    stop_services
    
    # 清理文件
    cleanup_files
    
    # 卸载依赖
    uninstall_dependencies
    
    info "卸载完成！"
}

# 执行
main 