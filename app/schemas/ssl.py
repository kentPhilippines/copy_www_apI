from pydantic import BaseModel
from typing import Optional

class SSLRequest(BaseModel):
    """SSL证书申请请求"""
    domain: str
    email: str

class SSLResponse(BaseModel):
    """SSL证书操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None 