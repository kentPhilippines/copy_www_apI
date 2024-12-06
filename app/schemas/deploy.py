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
    target_domain: str  # 目标站点域名
    target_path: str  # 目标存放路径
    overwrite: bool = False  # 是否覆盖已存在的文件
    sitemap: bool = False  # 是否生成站点地图
    tdk: bool = False  # 是否替换TDK信息
    tdk_rules: Optional[Dict[str, str]] = None  # TDK替换规则

class MirrorResponse(BaseModel):
    """镜像响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class LogResponse(BaseModel):
    """日志响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    logs: Optional[Dict[str, List[str]]] = None