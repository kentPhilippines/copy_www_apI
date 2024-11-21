from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.services.nginx_service import NginxService
from app.schemas.nginx import (
    NginxConfig, 
    NginxSite,
    NginxStatus,
    NginxResponse
)

router = APIRouter()
nginx_service = NginxService()

@router.get("/status", response_model=NginxStatus)
async def get_nginx_status():
    """获取Nginx运行状态"""
    return await nginx_service.get_status()

@router.post("/sites", response_model=NginxResponse)
async def create_site(site: NginxSite):
    """创建新的网站配置"""
    try:
        return await nginx_service.create_site(site)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=NginxResponse)
async def delete_site(domain: str):
    """删除网站配置"""
    try:
        return await nginx_service.delete_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites", response_model=List[NginxSite])
async def list_sites():
    """获取所有网站配置"""
    return await nginx_service.list_sites()

@router.post("/reload", response_model=NginxResponse)
async def reload_nginx():
    """重新加载Nginx配置"""
    try:
        return await nginx_service.reload()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 