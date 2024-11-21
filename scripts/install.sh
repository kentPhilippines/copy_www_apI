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

# 配置pip源
setup_pip() {
    info "配置pip源..."
    
    # 创建pip配置目录
    mkdir -p ~/.pip
    
    # 写入配置文件
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
}

# 安装Python包
install_package() {
    package=$1
    max_retries=3
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if pip install "$package"; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        warn "安装 $package 失败，尝试重试 ($retry_count/$max_retries)"
        sleep 2
    done
    
    error "安装 $package 失败"
    return 1
}

# 主安装流程
main() {
    info "开始安装..."
    
    # 配置pip源
    setup_pip
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装基础依赖
    basic_packages=(
        "wheel"
        "setuptools"
        "fastapi==0.65.2"
        "uvicorn==0.13.4"
        "pydantic==1.8.2"
    )
    
    for package in "${basic_packages[@]}"; do
        info "安装 $package"
        if ! install_package "$package"; then
            error "基础依赖安装失败"
            exit 1
        fi
    done
    
    # 安装其他依赖
    info "安装项目依赖..."
    if ! pip install -r requirements.txt; then
        # 如果整体安装失败，尝试逐个安装
        while read -r package; do
            # 跳过注释和空行
            [[ $package =~ ^#.*$ ]] && continue
            [[ -z $package ]] && continue
            
            info "安装 $package"
            install_package "$package"
        done < requirements.txt
    fi
    
    info "安装完成"
}

# 执行安装
main 