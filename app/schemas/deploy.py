from pydantic import BaseModel
from typing import Optional, Dict, Any

class DeployRequest(BaseModel):
    """部署请求"""
    domain: str
    deploy_type: str  # 'static' 或 'php'
    source_path: Optional[str] = None
    enable_ssl: bool = True
    ssl_email: Optional[str] = None

    @property
    def is_php(self) -> bool:
        return self.deploy_type == 'php'

    @property
    def is_static(self) -> bool:
        return self.deploy_type == 'static'

class DeployStatus(BaseModel):
    """部署状态"""
    nginx_configured: bool
    ssl_configured: bool
    is_accessible: bool
    error_message: Optional[str] = None

class DeployResponse(BaseModel):
    """部署响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SiteInfo(BaseModel):
    """站点信息"""
    domain: str
    deploy_type: str
    path: str
    status: DeployStatus