from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SSLCertRequest(BaseModel):
    """SSL证书申请请求"""
    domain: str
    email: Optional[str] = None
    staging: bool = False
    force_renewal: bool = False

class SSLCertInfo(BaseModel):
    """SSL证书信息"""
    domain: str
    issuer: str
    valid_from: datetime
    valid_to: datetime
    is_valid: bool

class SSLResponse(BaseModel):
    """SSL操作响应"""
    success: bool
    message: str 