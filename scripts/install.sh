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

# 检测系统类型并安装依赖
install_system_deps() {
    info "安装系统依赖..."
    
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL/Alibaba Cloud Linux系统
        info "检测到 RHEL 系列系统"
        
        # 添加EPEL仓库
        yum install -y epel-release
        
        # 更新系统
        yum update -y
        
        # 卸载可能冲突的包
        yum remove -y python3-urllib3 python3-requests python3-six certbot

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
            lsof \
            make \
            openssl \
            openssl-devel \
            bind-utils

        # 使用pip安装指定版本的certbot和依赖  
        pip3 install --upgrade pip
        pip3 install \
            'certbot==1.20.0' \
            'certbot-nginx==1.20.0' \
            'requests==2.27.1' \
            'urllib3==1.26.6' \
            'six==1.16.0' \
            'cryptography==3.3.2' \
            'pyOpenSSL==20.0.1' \
            'acme==1.20.0'

        # 创建certbot命令的软链接
        ln -sf /usr/local/bin/certbot /usr/bin/certbot

    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu系统
        info "检测到 Debian/Ubuntu 系统"
        
        # 更新包列表
        apt-get update
        
        # 卸载可能冲突的包
        apt-get remove -y python3-urllib3 python3-requests python3-six certbot

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
            lsof \
            libssl-dev \
            dnsutils

        # 使用pip安装指定版本的certbot和依赖
        pip3 install --upgrade pip
        pip3 install \
            'certbot==1.20.0' \
            'certbot-nginx==1.20.0' \
            'requests==2.27.1' \
            'urllib3==1.26.6' \
            'six==1.16.0' \
            'cryptography==3.3.2' \
            'pyOpenSSL==20.0.1' \
            'acme==1.20.0'

        # 创建certbot命令的软链接
        ln -sf /usr/local/bin/certbot /usr/bin/certbot
    else
        error "不支持的操作系统"
        exit 1
    fi

    # 确保certbot可执行
    chmod +x /usr/local/bin/certbot

    # 创建必要的目录
    mkdir -p /etc/letsencrypt
    mkdir -p /var/log/letsencrypt
    chmod 755 /etc/letsencrypt
    chmod 755 /var/log/letsencrypt

    info "系统依赖安装完成"
}

# 配置Python环境
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
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << EOF
[global]
timeout = 60
index-url = https://mirrors.aliyun.com/pypi/simple/
extra-index-url = 
    https://pypi.tuna.tsinghua.edu.cn/simple
    https://mirrors.cloud.tencent.com/pypi/simple
    https://mirrors.huaweicloud.com/repository/pypi/simple

[install]
trusted-host =
    mirrors.aliyun.com
    pypi.tuna.tsinghua.edu.cn
    mirrors.cloud.tencent.com
    mirrors.huaweicloud.com
EOF
    
    # 先安装关键依赖
    info "安装关键依赖..."
    pip install pydantic==1.8.2
    pip install fastapi==0.65.2
    pip install uvicorn==0.13.4
    
    # 安装其他依赖
    info "安装其他依赖..."
    pip install -r requirements.txt --no-deps
}

# 配置项目目录
setup_project_dirs() {
    info "配置项目目录..."
    
    # 创建必要的目录
    mkdir -p data logs
    mkdir -p app/{core,db,api/v1/endpoints,schemas,models,services,utils,static,templates}
    
    # 创建必要的文件
    find app -type d -exec touch {}/__init__.py \;
    
    # 设置权限
    chmod 755 data logs
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
    
    # 配置项目目录
    setup_project_dirs
    
    # 验证安装
    verify_installation
    
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


#  直接执行
#   source venv/bin/activate && ./scripts/install.sh

#   ./scripts/install.sh