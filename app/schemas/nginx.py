from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any

class SSLInfo(BaseModel):
    """SSL证书信息"""
    cert_path: str
    key_path: str
    cert_exists: bool = False
    key_exists: bool = False

class LogPaths(BaseModel):
    """日志路径"""
    access_log: str
    error_log: str

class AccessUrls(BaseModel):
    """访问地址"""
    http: List[str]
    https: Optional[List[str]] = None

class NginxSite(BaseModel):
    """Nginx站点配置模型"""
    domain: str
    root_path: Optional[str] = None
    ssl_enabled: bool = False
    ssl_info: Optional[SSLInfo] = None
    custom_config: Optional[str] = None
    deploy_type: str = 'static'
    status: str = 'active'
    config_file: Optional[str] = None
    logs: Optional[LogPaths] = None
    access_urls: Optional[AccessUrls] = None

class DeployInfo(BaseModel):
    """部署信息"""
    deployed: bool = False
    deploy_time: Optional[str] = None
    git_info: Optional[Dict[str, str]] = None
    web_server: str = "nginx"
    server_type: str = "unknown"
    error: Optional[str] = None

class NginxSiteInfo(NginxSite):
    """完整的站点信息"""
    deploy_info: Optional[DeployInfo] = None

class NginxStatus(BaseModel):
    """Nginx状态信息"""
    running: bool
    processes: List[Dict[str, Any]]
    version: str
    config_test: str
    resources: Dict[str, Any]

class NginxResponse(BaseModel):
    """Nginx操作响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class NginxConfig(BaseModel):
    """Nginx配置生成模型"""
    server_name: str
    root_path: str
    ports: List[int] = [80]
    ssl_enabled: bool = False
    ssl_info: Optional[SSLInfo] = None
    logs: Optional[LogPaths] = None
    custom_config: Optional[str] = None