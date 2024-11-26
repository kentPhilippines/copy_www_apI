#!/bin/bash

# 安装Python依赖
pip install -r requirements.txt

# 创建必要的目录
mkdir -p logs

# 设置权限
chmod +x monitor/run.py 