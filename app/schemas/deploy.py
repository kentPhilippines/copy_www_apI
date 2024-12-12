from pydantic import BaseModel
from typing import Optional

class DeployRequest(BaseModel):
    """部署请求模型"""
    domain: str  # 站点域名
    enable_ssl: bool = False  # 是否启用SSL证书
    ssl_email: Optional[str] = None  # SSL证书申请邮箱
    proxy_port: int = 9099  # 反向代理端口
    custom_config: Optional[str] = None  # 自定义Nginx配置

class DeployResponse(BaseModel):
    """部署响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None