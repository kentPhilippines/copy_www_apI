from pydantic import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Settings(BaseSettings):
    """系统配置"""
    
    # 项目信息
    PROJECT_NAME: str = "Nginx Deploy API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 路径配置
    NGINX_SITES_PATH: str = "/etc/nginx/sites-available"
    NGINX_ENABLED_PATH: str = "/etc/nginx/sites-enabled"
    WWW_ROOT: str = "/var/www"
    DATA_DIR: str = "data"
    LOG_DIR: str = "logs"
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/nginx_deploy.db"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # SSL配置
    SSL_EMAIL: str = "admin@example.com"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# 创建设置实例
settings = Settings() 