from fastapi import APIRouter, HTTPException
from typing import List
from app.services.ssl_service import SSLService
from app.schemas.ssl import (
    SSLCertRequest,
    SSLCertInfo,
    SSLResponse
)

router = APIRouter()
ssl_service = SSLService()

@router.post("/certificates", response_model=SSLResponse)
async def create_certificate(request: SSLCertRequest):
    """申请SSL证书"""
    try:
        return await ssl_service.create_certificate(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/certificates", response_model=List[SSLCertInfo])
async def list_certificates():
    """获取所有证书信息"""
    return await ssl_service.list_certificates()

@router.delete("/certificates/{domain}", response_model=SSLResponse)
async def delete_certificate(domain: str):
    """删除证书"""
    try:
        return await ssl_service.delete_certificate(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/certificates/{domain}/renew", response_model=SSLResponse)
async def renew_certificate(domain: str):
    """续期证书"""
    try:
        return await ssl_service.renew_certificate(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 