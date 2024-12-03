from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.services.deploy_service import DeployService
from app.schemas.deploy import (
    DeployRequest,
    DeployResponse,
    SiteUpdateRequest,
    SiteBackupInfo,
    SiteListResponse,
    MirrorRequest,
    MirrorResponse,
    LogResponse
)
from app.schemas.nginx import NginxSiteInfo

router = APIRouter()
deploy_service = DeployService()

@router.post("/sites", response_model=DeployResponse)
async def deploy_site(request: DeployRequest):
    """部署新站点"""
    try:
        return await deploy_service.deploy_site(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites", response_model=SiteListResponse)
async def list_sites():
    """获取所有已部署的站点"""
    try:
        return await deploy_service.list_sites()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites/{domain}", response_model=NginxSiteInfo)
async def get_site(domain: str):
    """获取单个站点信息"""
    try:
        site = await deploy_service.get_site_info(domain)
        if not site:
            raise HTTPException(status_code=404, detail=f"站点 {domain} 不存在")
        return site
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/sites/{domain}", response_model=DeployResponse)
async def update_site(domain: str, request: SiteUpdateRequest):
    """更新站点配置"""
    try:
        return await deploy_service.update_site(domain, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=DeployResponse)
async def remove_site(domain: str):
    """移除站点"""
    try:
        return await deploy_service.remove_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sites/{domain}/backup", response_model=DeployResponse)
async def backup_site(domain: str):
    """备份站点"""
    try:
        return await deploy_service.backup_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    

@router.get("/sites/{domain}/logs", response_model=LogResponse)
async def get_site_logs(domain: str):
    """获取站点日志"""
    try:
        return await deploy_service.get_site_logs(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/sites/mirror", response_model=MirrorResponse)
async def mirror_site(request: MirrorRequest):
    """镜像站点"""
    try:
        return await deploy_service.mirror_site(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))