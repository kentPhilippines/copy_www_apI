from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Nginx Deploy API"
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

settings = Settings() 