from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.schemas.nginx import NginxSiteInfo

class DeployRequest(BaseModel):
    """部署请求模型"""
    domain: str
    enable_ssl: bool = False
    deploy_type: str = 'static'
    ssl_email: Optional[str] = None
    root_path: Optional[str] = None
    custom_config: Optional[str] = None

class DeployResponse(BaseModel):
    """部署响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SiteUpdateRequest(BaseModel):
    """站点更新请求模型"""
    ssl_enabled: Optional[bool] = None
    root_path: Optional[str] = None
    custom_config: Optional[str] = None

class SiteBackupInfo(BaseModel):
    """站点备份信息"""
    backup_path: str
    backup_time: str
    site_info: NginxSiteInfo
    files_included: List[str]
    size: int

class SiteListResponse(BaseModel):
    """站点列表响应"""
    total: int
    sites: List[NginxSiteInfo]
    errors: Optional[List[Dict[str, str]]] = None