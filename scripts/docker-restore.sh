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

# 恢复备份
restore_backup() {
    local BACKUP_FILE=$1
    
    if [ ! -f "$BACKUP_FILE" ]; then
        error "备份文件不存在: $BACKUP_FILE"
        exit 1
    }
    
    info "开始恢复备份: $BACKUP_FILE"
    
    # 停止服务
    docker-compose down
    
    # 根据文件名确定恢复类型
    if [[ $BACKUP_FILE == *"data"* ]]; then
        # 恢复数据
        tar -xzf "$BACKUP_FILE" -C ./
    elif [[ $BACKUP_FILE == *"nginx"* ]]; then
        # 恢复Nginx配置
        tar -xzf "$BACKUP_FILE" -C /
    elif [[ $BACKUP_FILE == *"ssl"* ]]; then
        # 恢复SSL证书
        tar -xzf "$BACKUP_FILE" -C /
    else
        error "未知的备份类型"
        exit 1
    fi
    
    # 重启服务
    docker-compose up -d
    
    info "恢复完成"
}

# 主流程
main() {
    if [ -z "$1" ]; then
        error "请指定要恢复的备份文件"
        echo "用法: $0 <backup_file.tar.gz>"
        exit 1
    fi
    
    restore_backup "$1"
}

# 执行
main "$@" 