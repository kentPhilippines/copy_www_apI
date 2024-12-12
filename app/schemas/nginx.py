from pydantic import BaseModel
from typing import Optional, List

class SSLInfo(BaseModel):
    """SSL证书信息"""
    cert_path: str
    key_path: str
    cert_exists: bool = False
    key_exists: bool = False

class NginxSite(BaseModel):
    """Nginx站点配置模型"""
    domain: str
    root_path: str
    ssl_enabled: bool = False
    ssl_info: Optional[SSLInfo] = None
    proxy_port: int = 9099  # 反向代理端口
    custom_config: Optional[str] = None

class NginxResponse(BaseModel):
    """Nginx操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None