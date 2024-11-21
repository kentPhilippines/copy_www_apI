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

# 设置备份目录
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份
create_backup() {
    info "创建备份..."
    
    # 创建备份目录
    mkdir -p "${BACKUP_DIR}"
    
    # 备份数据目录
    tar -czf "${BACKUP_DIR}/data_${TIMESTAMP}.tar.gz" data/
    
    # 备份Nginx配置
    tar -czf "${BACKUP_DIR}/nginx_${TIMESTAMP}.tar.gz" /etc/nginx/
    
    # 备份SSL证书
    if [ -d "/etc/letsencrypt" ]; then
        tar -czf "${BACKUP_DIR}/ssl_${TIMESTAMP}.tar.gz" /etc/letsencrypt/
    fi
    
    info "备份完成: ${BACKUP_DIR}/*_${TIMESTAMP}.tar.gz"
}

# 清理旧备份
cleanup_old_backups() {
    info "清理旧备份..."
    
    # 保留最近7天的备份
    find "${BACKUP_DIR}" -name "*.tar.gz" -type f -mtime +7 -delete
}

# 主流程
main() {
    info "开始备份..."
    
    # 创建备份
    create_backup
    
    # 清理旧备份
    cleanup_old_backups
    
    info "备份过程完成"
}

# 执行
main 