from fastapi import HTTPException
from typing import Any, Dict, Optional

class NginxError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "Nginx operation failed")

class SSLError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "SSL operation failed")

class DeployError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "Deployment failed")

class DatabaseError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=500, detail=detail or "Database operation failed")

class ValidationError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=422, detail=detail or "Validation failed")

class APIError(HTTPException):
    """通用API错误"""
    def __init__(
        self,
        status_code: int = 400,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail or "API operation failed",
            headers=headers
        ) 