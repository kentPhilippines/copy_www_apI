# 脚本使用说明

## 安装脚本
sudo ./scripts/install.sh
### 1. install.sh - 标准安装 

功能：
- 检测系统环境
- 安装系统依赖
- 配置Python环境
- 配置Nginx
- 配置SSL环境
- 创建必要目录

### 2. docker-install.sh - Docker安装

功能：
- 安装Docker和Docker Compose
- 创建必要目录
- 构建并启动容器
- 配置自动启动

## 启动脚本

### 1. start.sh - 标准启动

功能：
- 检查环境
- 启动Nginx
- 启动API服务
- 检查服务状态

通常不需要手动执行，由Docker自动调用
### 2. docker-entrypoint.sh - Docker启动

功能：
- 等待依赖服务
- 初始化应用
- 启动Nginx和API服务
- 处理优雅退出

## 备份和恢复

### 1. docker-backup.sh - 数据备份
创建完整备份
./scripts/docker-backup.sh
备份将保存在 backups/ 目录：
- data_YYYYMMDD_HHMMSS.tar.gz # 数据备份
- nginx_YYYYMMDD_HHMMSS.tar.gz # Nginx配置备份
- ssl_YYYYMMDD_HHMMSS.tar.gz # SSL证书备份

功能：
- 备份数据目录
- 备份Nginx配置
- 备份SSL证书
- 自动清理旧备份（保留7天）

### 2. docker-restore.sh - 数据恢复
bash
恢复数据备份
./scripts/docker-restore.sh backups/data_20240120_120000.tar.gz
恢复Nginx配置
./scripts/docker-restore.sh backups/nginx_20240120_120000.tar.gz
恢复SSL证书
./scripts/docker-restore.sh backups/ssl_20240120_120000.tar.gz

功能：
- 自动识别备份类型
- 停止相关服务
- 恢复指定数据
- 重启相关服务

## 日志管理

### docker-logs.sh - 日志查看

bash
查看API日志（最后100行）
./scripts/docker-logs.sh api 100
查看Nginx日志（最后100行）
./scripts/docker-logs.sh nginx 100
查看所有日志（最后100行）
./scripts/docker-logs.sh all 100

功能：
- 查看API服务日志
- 查看Nginx错误日志
- 支持指定行数
- 彩色输出

## 卸载脚本

### uninstall.sh - 系统卸载

功能：
- 停止所有服务
- 删除配置文件
- 清理数据目录
- 可选卸载系统依赖

## 注意事项

1. 权限要求
- install.sh 和 uninstall.sh 需要 root 权限
- 其他脚本一般不需要 root 权限

2. 备份建议
- 定期执行备份
- 可以设置cron任务自动备份

3. 日志管理
- 定期检查日志
- 设置日志轮转
- 及时处理错误

4. 安全建议
- 定期更新系统
- 及时更新SSL证书
- 保护好备份文件

## 故障排除

1. 安装失败
- 检查系统要求
- 查看详细日志
- 确保网络连接

2. 备份/恢复失败
- 检查磁盘空间
- 确保目录权限
- 验证备份文件完整性

3. 日志查看失败
- 确保服务正在运行
- 检查容器状态
- 验证日志文件存在