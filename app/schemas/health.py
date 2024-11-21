from pydantic import BaseModel
from typing import Optional, Dict

class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str
    nginx_running: Optional[bool] = None
    system_info: Optional[Dict[str, float]] = None
    error: Optional[str] = None 