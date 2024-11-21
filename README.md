# Nginx 站点部署管理系统

基于 FastAPI 的 Nginx 站点自动化部署和管理系统，支持多站点管理、SSL 证书自动化和站点监控。

## 主要功能
 

### 站点管理
- 一键部署新站点
- 自动生成 Nginx 配置
- 自动创建站点目录和测试页面
- 站点删除和清理

### SSL 证书管理
- Let's Encrypt 证书自动申请
- 证书自动续期（每天检查）
- HTTPS 配置自动化
- HTTP 自动跳转 HTTPS

### 站点监控
- 站点可用性监控（每5分钟）
- Nginx 服务状态监控
- 自动异常告警
- 性能指标收集

## 系统要求

- Python 3.6+
- Nginx
- CentOS/RHEL 或 Debian/Ubuntu
- Let's Encrypt certbot

## 快速开始

### 1. 安装

```bash
git clone https://github.com/kentPhilippines/copy_www_apI.git
cd copy_www_apI
```
### 2. 初始化
```bash
chmod +x /scripts/start.sh
chmod +x /scripts/install.sh
./scripts/install.sh
```
### 3. 启动服务
bash
启动API服务
./scripts/start.sh
### 4. 使用示例

#### 部署新站点
bash
curl -X POST http://localhost:8000/api/v1/deploy/sites \
-H "Content-Type: application/json" \
-d '{
"domain": "example.com",
"enable_ssl": true,
"ssl_email": "admin@example.com"
}'
#### 删除站点
```bash
curl -X DELETE http://localhost:8000/api/v1/deploy/sites/example.com
```

## 配置文件结构

### Nginx 配置
- 站点配置: `/etc/nginx/conf.d/{domain}.conf`
- 站点目录: `/var/www/{domain}/`
- 日志文件: `/var/log/nginx/{domain}.access.log`

### SSL 证书
- 证书目录: `/etc/letsencrypt/live/{domain}/`
- 证书文件: `fullchain.pem`
- 私钥文件: `privkey.pem`

## 主要功能模块

### 1. 部署服务 (DeployService)
- 站点配置生成
- 目录创建和权限设置
- SSL 证书申请和配置
- 站点清理和删除

### 2. SSL 服务 (SSLService)
- 证书申请和管理
- 证书续期
- 域名验证

### 3. 监控服务 (MonitorService)
- 站点状态监控
- Nginx 服务监控
- 性能指标收集

### 4. 续期服务 (RenewalService)
- 证书过期检查
- 自动续期
- 续期日志记录
## 日志

- 应用日志: `logs/app.log`
- Nginx 访问日志: `/var/log/nginx/access.log`
- Nginx 错误日志: `/var/log/nginx/error.log`

## 注意事项

1. 确保域名已正确解析到服务器
2. 需要 root 权限运行安装脚本
3. 80 和 443 端口必须可用
4. 确保服务器可以访问 Let's Encrypt 服务

## 常见问题

1. SSL 证书申请失败
   - 检查域名解析
   - 确认 80 端口可访问
   - 查看 Let's Encrypt 日志

2. 站点无法访问
   - 检查 Nginx 配置
   - 确认目录权限
   - 查看错误日志

## 贡献指南

欢迎提交 Issue 和 Pull Request。

## 许可证

[License Type] - 查看 LICENSE 文件了解更多信息。