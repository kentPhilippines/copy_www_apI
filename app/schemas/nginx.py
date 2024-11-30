from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class NginxStatus(BaseModel):
    running: bool
    processes: List[Dict[str, Any]]
    version: str
    config_test: str
    resources: Dict[str, Any]

class NginxSite(BaseModel):
    domain: str
    port: int = 80
    ssl: bool = False
    root_path: Optional[str] = None

class NginxResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None