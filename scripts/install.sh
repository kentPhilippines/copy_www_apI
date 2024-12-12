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

# 安装系统依赖
install_system_deps() {
    info "安装系统依赖..."
    
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL系统
        info "检测到 RHEL 系列系统"
        
        # 添加EPEL仓库
        yum install -y epel-release
        
        # 安装基础依赖
        yum install -y \
            nginx \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            curl \
            wget \
            git \
            openssl \
            openssl-devel

        # 安装certbot
        pip3 install --upgrade pip
        pip3 install \
            'certbot==1.20.0' \
            'certbot-nginx==1.20.0'

    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu系统
        info "检测到 Debian/Ubuntu 系统"
        
        # 更新包列表
        apt-get update
        
        # 安装依赖
        apt-get install -y \
            nginx \
            python3 \
            python3-pip \
            python3-venv \
            build-essential \
            curl \
            wget \
            git \
            openssl \
            libssl-dev

        # 安装certbot
        pip3 install --upgrade pip
        pip3 install \
            'certbot==1.20.0' \
            'certbot-nginx==1.20.0'
    else
        error "不支持的操作系统"
        exit 1
    fi

    # 创建必要的目录
    mkdir -p /etc/letsencrypt
    mkdir -p /var/log/letsencrypt
    chmod 755 /etc/letsencrypt
    chmod 755 /var/log/letsencrypt

    # 设置Nginx目录权限
    mkdir -p /etc/nginx/conf.d
    chown -R nginx:nginx /etc/nginx/conf.d
    chmod -R 755 /etc/nginx/conf.d

    # 设置网站目录权限  
    mkdir -p /var/www
    chown -R nginx:nginx /var/www
    chmod -R 755 /var/www

    info "系统依赖安装完成"
}

# 配置Python环境
setup_python_env() {
    info "配置Python虚拟环境..."
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
    
    # 安装项目依赖
    pip install -r requirements.txt
}

# 配置systemd服务
setup_service() {
    info "配置系统服务..."
    
    # 创建服务文件
    cat > /etc/systemd/system/nginx-deploy.service << EOF
[Unit]
Description=Nginx Deploy API Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/nginx-deploy
Environment=PYTHONPATH=/opt/nginx-deploy
ExecStart=/opt/nginx-deploy/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable nginx-deploy
}

# 验证安装
verify_installation() {
    info "验证安装..."
    
    # 检查Python
    python3 --version || warn "Python3 检查失败"
    
    # 检查Nginx
    nginx -v || warn "Nginx 检查失败"
    
    # 检查服务状态
    systemctl status nginx || warn "Nginx 服务检查失败"
    
    # 检查虚拟环境
    source venv/bin/activate && python -c "import fastapi" || warn "FastAPI 检查失败"
}

# 主安装流程
main() {
    info "开始安装 Nginx Deploy API..."
    
    # 安装系统依赖
    install_system_deps
    
    # 配置Python环境
    setup_python_env
    
    # 配置系统服务
    setup_service
    
    # 验证安装
    verify_installation
    
    info "安装完成！"
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
    echo "API服务状态：$(systemctl is-active nginx-deploy)"
    echo ""
    info "API服务已配置为系统服务并已启用"
    info "可以使用以下命令管理服务："
    echo "systemctl start nginx-deploy    # 启动服务"
    echo "systemctl stop nginx-deploy     # 停止服务"
    echo "systemctl restart nginx-deploy  # 重启服务"
    echo "systemctl status nginx-deploy   # 查看状态"
    info "==================================="
else
    error "安装过程中出现错误，请检查日志"
    exit 1
fi