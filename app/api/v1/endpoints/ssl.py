from fastapi import APIRouter, HTTPException
from app.services.ssl_service import SSLService
from app.schemas.ssl import SSLRequest, SSLResponse

router = APIRouter()
ssl_service = SSLService()

@router.post("/certificates", response_model=SSLResponse)
async def create_certificate(request: SSLRequest):
    """申请SSL证书"""
    try:
        result = await ssl_service.create_certificate(
            domain=request.domain,
            email=request.email
        )
        return SSLResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/certificates/{domain}", response_model=SSLResponse)
async def delete_certificate(domain: str):
    """删除SSL证书"""
    try:
        result = await ssl_service.delete_certificate(domain)
        return SSLResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 