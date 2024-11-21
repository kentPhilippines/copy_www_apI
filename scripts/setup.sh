#!/bin/bash

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "请以root权限运行此脚本"
    exit 1
fi

# 安装系统依赖
apt-get update
apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3-pip \
    python3-venv

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 初始化配置
cp .env.example .env

# 启动服务
systemctl enable nginx
systemctl start nginx

echo "安装完成！" 