# Nginx Deploy API

一个基于 FastAPI 的 Nginx 部署管理 API 服务，提供 Nginx 配置、SSL 证书和站点部署的自动化管理。

## 功能特性

- Nginx 服务管理
  - 配置文件管理
  - 站点部署
  - 服务状态监控
  
- SSL 证书管理
  - 自动申请证书
  - 证书续期
  - 证书状态查看
  
- 站点部署
  - 支持静态站点
  - 支持 PHP 站点
  - 自动配置 HTTPS

## 环境要求

- Python 3.6+
- Nginx
- Certbot

## 快速开始

1. 克隆项目：

```bash
git clone https://github.com/kentPhilippines/copy_www_apI.git
cd copy_www_apI
```

## API 文档

启动服务后访问：http://localhost:8000/docs

### 主要接口

#### Nginx 管理
- GET /api/v1/nginx/status - 获取 Nginx 状态
- POST /api/v1/nginx/sites - 创建站点配置
- GET /api/v1/nginx/sites - 获取所有站点
- DELETE /api/v1/nginx/sites/{domain} - 删除站点

#### SSL 证书管理
- POST /api/v1/ssl/certificates - 申请证书
- GET /api/v1/ssl/certificates - 获取证书列表
- POST /api/v1/ssl/certificates/{domain}/renew - 续期证书

#### 站点部署
- POST /api/v1/deploy/sites - 部署新站点
- GET /api/v1/deploy/sites - 获取已部署站点
- DELETE /api/v1/deploy/sites/{domain} - 移除站点

## 使用示例
### 部署静态站点
curl -X POST http://localhost:8000/api/v1/deploy/sites \
-H "Content-Type: application/json" \
-d '{
"domain": "example.com",
"deploy_type": "static",
"enable_ssl": true,
"ssl_email": "admin@example.com"
}'

### 部署 PHP 站点
bash
curl -X POST http://localhost:8000/api/v1/deploy/sites \
-H "Content-Type: application/json" \
-d '{
"domain": "example.com",
"deploy_type": "php",
"source_path": "/path/to/php/files",
"enable_ssl": true
}'
## 目录结构
copy_www_apI/
├── app/
│ ├── api/ # API 接口
│ ├── services/ # 业务逻辑
│ ├── schemas/ # 数据模型
│ └── utils/ # 工具函数
├── scripts/ # 脚本文件
└── tests/ # 测试文件

## 开发指南

1. 创建虚拟环境：
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
2. 安装依赖：pip install -r requirements.txt
3. 运行测试：pytest

## 常见问题

### 1. 权限问题
确保运行程序的用户有权限操作以下目录：
- /etc/nginx/
- /var/www/
- /etc/letsencrypt/

### 2. 端口占用
默认使用的端口：
- 8000: API 服务
- 80: HTTP
- 443: HTTPS

### 3. SSL 证书申请失败
- 确保域名已正确解析
- 检查 80/443 端口是否开放
- 查看 certbot 日志

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交改动
4. 发起 Pull Request

## 许可证

MIT License

## 联系方式

- 作者：musk
- 项目地址：https://github.com/kentPhilippines/copy_www_apI
