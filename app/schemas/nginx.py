from pydantic import BaseModel
from typing import Optional, List

class SSLInfo(BaseModel):
    """SSL证书信息"""
    cert_path: str
    key_path: str
    cert_exists: bool = False
    key_exists: bool = False

class NginxSite(BaseModel):
    """Nginx站点配置"""
    domain: str
    root_path: str
    ssl_enabled: bool = False
    ssl_info: Optional[SSLInfo] = None
    proxy_ip: str = "127.0.0.1"
    proxy_port: int = 9099
    proxy_host: Optional[str] = None
    custom_config: Optional[str] = None

class NginxResponse(BaseModel):
    """Nginx操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None