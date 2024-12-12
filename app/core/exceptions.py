from fastapi import HTTPException
from typing import Any, Dict, Optional

class NginxError(Exception):
    """Nginx相关错误"""
    pass

class SSLError(Exception):
    """SSL证书相关错误"""
    pass

class DeployError(Exception):
    """部署相关错误"""
    pass

class APIError(Exception):
    """通用API错误"""
    def __init__(self, message: str = "API操作失败"):
        self.message = message
        super().__init__(self.message) 