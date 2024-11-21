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

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    error "请使用root权限运行此脚本"
    exit 1
fi

# 检测系统类型
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | cut -d' ' -f1)
    else
        error "无法检测操作系统类型"
        exit 1
    fi

    info "检测到操作系统: $OS $VERSION"
}

# 安装基础依赖
install_dependencies() {
    info "开始安装基础依赖..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt-get update
        apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            nginx \
            certbot \
            python3-certbot-nginx \
            curl \
            wget \
            git \
            python3-dev \
            gcc
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Alibaba"* ]] || [[ "$OS" == *"Aliyun"* ]]; then
        # 添加EPEL仓库
        yum install -y epel-release
        
        # 更新系统
        yum update -y
        
        # 安装SCL仓库以获取更新的Python版本
        yum install -y centos-release-scl
        
        # 安装Python 3.8
        yum install -y \
            rh-python38 \
            rh-python38-python-devel \
            gcc \
            nginx \
            certbot \
            python3-certbot-nginx \
            curl \
            wget \
            git

        # 设置Python 3.8为默认版本
        source /opt/rh/rh-python38/enable
        echo "source /opt/rh/rh-python38/enable" >> ~/.bashrc
    else
        error "不支持的操作系统: $OS"
        exit 1
    fi
}

# 配置Python虚拟环境
setup_python_env() {
    info "配置Python虚拟环境..."
    
    # 检查Python版本
    PYTHON_VERSION=$(python3 -V 2>&1 | awk '{print $2}')
    info "Python版本: $PYTHON_VERSION"
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
    
    # 设置阿里云PyPI镜像
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com
    
    # 安装项目依赖
    pip install -r requirements.txt
}

# 配置Nginx
setup_nginx() {
    info "配置Nginx..."
    
    # 创建必要的目录
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    mkdir -p /var/www
    
    # 设置目录权限
    chown -R nginx:nginx /var/www
    chmod -R 755 /var/www
    
    # 启动Nginx
    systemctl enable nginx
    systemctl start nginx
}

# 配置SSL
setup_ssl() {
    info "配置SSL..."
    
    # 创建SSL目录
    mkdir -p /etc/letsencrypt
    chmod 755 /etc/letsencrypt
}

# 创建数据和日志目录
setup_directories() {
    info "创建必要的目录..."
    
    # 创建数据目录
    mkdir -p data
    mkdir -p logs
    
    # 设置权限
    chmod 755 data logs
}

# 主安装流程
main() {
    info "开始安装 Nginx Deploy API..."
    
    # 检测系统
    detect_os
    
    # 安装依赖
    install_dependencies
    
    # 配置Python环境
    setup_python_env
    
    # 配置Nginx
    setup_nginx
    
    # 配置SSL
    setup_ssl
    
    # 创建必要的目录
    setup_directories
    
    info "安装完成！"
    info "你现在可以使用以下命令启动服务："
    info "source venv/bin/activate && ./scripts/start.sh"
}

# 执行安装
main

# 检查安装结果
if [ $? -eq 0 ]; then
    info "==================================="
    info "安装成功！"
    info "请检查以下服务是否正常运行："
    echo ""
    echo "Nginx状态：$(systemctl is-active nginx)"
    echo "Python版本：$(python3 --version)"
    echo ""
    info "你可以通过以下命令启动API服务："
    echo "cd $(pwd)"
    echo "source venv/bin/activate"
    echo "./scripts/start.sh"
    info "==================================="
else
    error "安装过程中出现错误，请检查日志"
    exit 1
fi 