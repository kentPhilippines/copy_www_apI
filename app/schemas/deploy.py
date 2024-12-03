from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.schemas.nginx import NginxSiteInfo

class DeployRequest(BaseModel):
    """部署请求模型"""
    domain: str  # 站点域名
    enable_ssl: bool = False  # 是否启用SSL证书
    deploy_type: str = 'static'  # 部署类型: static/php/node
    ssl_email: Optional[str] = None  # SSL证书申请邮箱
    root_path: Optional[str] = None  # 自定义站点根目录
    custom_config: Optional[str] = None  # 自定义Nginx配置

class DeployResponse(BaseModel):
    """部署响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SiteUpdateRequest(BaseModel):
    """站点更新请求模型"""
    ssl_enabled: Optional[bool] = None  # 是否启用SSL
    root_path: Optional[str] = None  # 站点根目录
    custom_config: Optional[str] = None  # 自定义配置

class SiteBackupInfo(BaseModel):
    """站点备份信息"""
    backup_path: str  # 备份文件路径
    backup_time: str  # 备份时间
    site_info: NginxSiteInfo  # 站点配置信息
    files_included: List[str]  # 包含的文件列表
    size: int  # 备份文件大小(字节)

class SiteListResponse(BaseModel):
    """站点列表响应"""
    total: int
    sites: List[NginxSiteInfo]
    errors: Optional[List[Dict[str, str]]] = None

class MirrorRequest(BaseModel):
    """镜像请求模型"""
    domain: str  # 源站点域名
    path: str  # 源站点路径
    target_domain: str  # 目标站点域名
    target_path: str  # 目标存放路径  这里就是当前源站点的路径
    # 是否覆盖
    overwrite: bool = False
    #蜘蛛地图
    sitemap: bool = False
    # tdk替换
    tdk: bool = False
    #tdk替换规则
    tdk_rules: Optional[Dict[str, str]] = None
   
class MirrorResponse(BaseModel):
    """镜像响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None