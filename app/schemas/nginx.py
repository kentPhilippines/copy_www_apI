from pydantic import BaseModel
from typing import Optional, List

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

class NginxResponse(BaseModel):
    """Nginx操作响应"""
    success: bool
    message: str 