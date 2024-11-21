#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

# 查看容器日志
view_logs() {
    local service=$1
    local lines=$2
    
    case $service in
        "api")
            docker-compose logs --tail="$lines" api
            ;;
        "nginx")
            docker exec nginx-deploy-api tail -n "$lines" /var/log/nginx/error.log
            ;;
        "all")
            info "API日志:"
            docker-compose logs --tail="$lines" api
            echo
            info "Nginx错误日志:"
            docker exec nginx-deploy-api tail -n "$lines" /var/log/nginx/error.log
            ;;
        *)
            echo "用法: $0 [api|nginx|all] [行数]"
            exit 1
            ;;
    esac
}

# 主流程
main() {
    local service=${1:-"all"}
    local lines=${2:-100}
    
    view_logs "$service" "$lines"
}

# 执行
main "$@" 