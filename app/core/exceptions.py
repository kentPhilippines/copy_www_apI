from fastapi import HTTPException
from typing import Any

class NginxError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "Nginx operation failed")

class SSLError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "SSL operation failed")

class DeployError(HTTPException):
    def __init__(self, detail: Any = None):
        super().__init__(status_code=400, detail=detail or "Deployment failed") 