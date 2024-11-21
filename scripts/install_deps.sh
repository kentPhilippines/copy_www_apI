#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    error "请使用root权限运行此脚本"
    exit 1
fi

# 检测系统类型
if [ -f /etc/redhat-release ]; then
    # CentOS/RHEL系统
    info "检测到 CentOS/RHEL 系统"
    yum update -y
    yum install -y epel-release
    yum install -y nginx certbot python3-certbot-nginx curl wget
elif [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    info "检测到 Debian/Ubuntu 系统"
    apt-get update
    apt-get install -y nginx certbot python3-certbot-nginx curl wget
else
    error "不支持的操作系统"
    exit 1
fi

# 启动Nginx
systemctl enable nginx
systemctl start nginx

info "依赖安装完成" 