from pydantic import BaseModel, Field
from typing import Optional

class DeployRequest(BaseModel):
    """部署请求参数"""
    domain: str
    enable_ssl: bool = False
    ssl_email: Optional[str] = None
    proxy_ip: Optional[str] = Field(default="127.0.0.1", description="反向代理目标IP")
    proxy_port: int = Field(default=9099, description="反向代理目标端口")
    proxy_host: Optional[str] = Field(default=None, description="反向代理Host头")
    custom_config: Optional[str] = None

class DeployResponse(BaseModel):
    """部署响应"""
    success: bool
    message: str
    data: Optional[dict] = None