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

- Python 3.8+
- Nginx
- Certbot
- Docker (可选)

## 快速开始

### 使用 Docker（推荐）

1. 克隆项目： 