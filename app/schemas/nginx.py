from pydantic import BaseModel
from typing import Optional, List

class NginxConfig(BaseModel):
    """Nginx配置基础模型"""
    server_name: str
    root_path: str
    index: List[str] = ["index.html", "index.htm"]
    php_enabled: bool = False
    ssl_enabled: bool = False
    ssl_certificate: Optional[str] = None
    ssl_certificate_key: Optional[str] = None

class NginxSite(BaseModel):
    """Nginx站点配置"""
    domain: str
    root_path: str
    php_enabled: bool = False
    ssl_enabled: bool = False

class NginxStatus(BaseModel):
    """Nginx状态"""
    is_running: bool
    pid: Optional[str]
    version: Optional[str]
    worker_count: Optional[int]
    error_log_path: Optional[str]
    access_log_path: Optional[str]

class NginxResponse(BaseModel):
    """Nginx操作响应"""
    success: bool
    message: str