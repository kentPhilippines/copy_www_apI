#!/bin/bash

# 检查必要的服务
services=("nginx" "certbot")
for service in "${services[@]}"; do
    if ! command -v $service &> /dev/null; then
        echo "$service 未安装，请先运行 setup.sh"
        exit 1
    fi
done

# 启动 Nginx
if ! systemctl is-active --quiet nginx; then
    echo "启动 Nginx..."
    systemctl start nginx
fi

# 启动 API 服务
echo "启动 API 服务..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 