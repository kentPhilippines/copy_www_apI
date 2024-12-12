from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    """系统配置"""
    
    # 项目信息
    PROJECT_NAME: str = "Nginx Deploy API"
    API_V1_STR: str = "/api/v1"
    
    # 路径配置
    NGINX_CONF_DIR: str = "/etc/nginx/conf.d"
    WWW_ROOT: str = "/var/www"
    SSL_DIR: str = "/etc/letsencrypt/live"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # SSL配置
    SSL_EMAIL: str = "admin@example.com"
    
    class Config:
        case_sensitive = True

# 创建设置实例
settings = Settings() 