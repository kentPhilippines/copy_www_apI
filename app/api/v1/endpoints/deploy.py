from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.deploy_service import DeployService
from app.schemas.deploy import (
    DeployRequest,
    DeployStatus,
    DeployResponse,
    SiteInfo
)
from app.core.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
deploy_service = DeployService()

@router.post("/sites", response_model=DeployResponse)
async def deploy_site(request: DeployRequest):
    """部署新站点"""
    try:
        logger.info(f"开始部署站点: {request.domain}")
        return await deploy_service.deploy_site(request)
    except Exception as e:
        logger.error(f"部署失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites", response_model=List[SiteInfo])
async def list_sites():
    """获取所有已部署的站点"""
    try:
        return await deploy_service.list_sites()
    except Exception as e:
        logger.error(f"获取站点列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=DeployResponse)
async def remove_site(domain: str):
    """移除站点"""
    try:
        logger.info(f"开始移除站点: {domain}")
        return await deploy_service.remove_site(domain)
    except Exception as e:
        logger.error(f"移除站点失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites/{domain}/status", response_model=DeployStatus)
async def get_site_status(domain: str):
    """获取站点状态"""
    try:
        return await deploy_service.get_site_status(domain)
    except Exception as e:
        logger.error(f"获取站点状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 