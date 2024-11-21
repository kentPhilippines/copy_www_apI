from pydantic import BaseModel
from typing import Optional, Literal

class DeployRequest(BaseModel):
    """部署请求"""
    domain: str
    deploy_type: Literal["static", "php"]
    source_path: Optional[str] = None
    enable_ssl: bool = True
    ssl_email: Optional[str] = None

class DeployStatus(BaseModel):
    """部署状态"""
    nginx_configured: bool
    ssl_configured: bool
    is_accessible: bool

class DeployResponse(BaseModel):
    """部署响应"""
    success: bool
    message: str

class SiteInfo(BaseModel):
    """站点信息"""
    domain: str
    deploy_type: str
    path: str
    status: DeployStatus 