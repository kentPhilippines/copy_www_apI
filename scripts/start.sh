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

# 检查并创建虚拟环境
setup_venv() {
    if [ ! -d "venv" ]; then
        info "创建虚拟环境..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            error "创建虚拟环境失败"
            exit 1
        fi
        
        info "安装依赖..."
        source venv/bin/activate
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            error "安装依赖失败"
            exit 1
        fi
    else
        source venv/bin/activate
    fi
}

# 检查必要的命令
check_commands() {
    info "检查必要的命令..."
    
    # 检查并安装 lsof
    if ! command -v lsof &> /dev/null; then
        warn "正在安装 lsof..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y lsof
        elif command -v yum &> /dev/null; then
            sudo yum install -y lsof
        else
            error "无法安装 lsof，请手动安装"
            exit 1
        fi
    fi
}

# 检查是否在虚拟环境中
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        if [ -d "venv" ]; then
            info "激活虚拟环境..."
            source venv/bin/activate
        else
            error "虚拟环境不存在，请先运行 install.sh"
            exit 1
        fi
    fi
}

# 检查必要的服务
check_services() {
    info "检查必要的服务..."
    
    # 检查Nginx
    if ! systemctl is-active --quiet nginx; then
        warn "Nginx未运行，尝试启动..."
        sudo systemctl start nginx
    fi
    
    # 检查目录权限
    if [ ! -w "/etc/nginx/conf.d" ]; then
        error "没有Nginx配置目录的写入权限"
        exit 1
    fi
}

# 创建必要的目录
setup_directories() {
    info "检查必要的目录..."
    
    # 创建数据和日志目录
    mkdir -p data logs
    
    # 设置权限
    chmod 755 data logs
}

# 检查端口占用
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            error "端口 $port 已被占用"
            #如果占用 kill掉
            sudo kill -9 $(lsof -Pi :$port -sTCP:LISTEN -t)
        fi
    else
        warn "lsof 未安装，跳过端口检查"
    fi
}

# 启动API服务
start_api() {
    info "启动API服务..."
    
    # 检查端口
    check_port 8000
    
    # 确保requirements.txt中的依赖已安装
    pip install -r requirements.txt
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动服务 - 使用更好的后台运行方式
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &
    
    # 保存PID
    echo $! > .api.pid
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否启动
    if ! ps -p $(cat .api.pid) > /dev/null; then
        error "API服务启动失败，请检查 logs/api.log"
        exit 1
    fi
    
    # 检查端口是否正常监听
    if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
        error "API服务端口未正常监听，请检查 logs/api.log"
        exit 1
    fi
    
    #获取外网地址
    IP=$(host myip.opendns.com resolver1.opendns.com | grep "has address" | awk '{ print $4 }')

    info "API服务启动成功!"
    info "API地址: http://$IP:8000"
    info "管理界面: http://$IP:8001"
    info "日志文件: $(pwd)/logs/api.log"
    
    # 显示日志尾部
    info "最近的日志输出:"
    tail -n 5 logs/api.log
}

 
 

# 修改主函数，支持命令行参数
main() {
  
            info "启动 Nginx Deploy API 服务..."
            check_commands
            check_venv
            setup_venv
            check_services
            setup_directories
            start_api
}

# 执行主函数，传入命令行参数
main  