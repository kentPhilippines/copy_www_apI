from fastapi import APIRouter, HTTPException, Depends, WebSocket, Query, WebSocketDisconnect
from typing import List, Optional
from app.services.deploy_service import DeployService
from app.schemas.nginx import (
    NginxSite,
)

router = APIRouter()
deploy_service = DeployService()    




@router.get("/sites/{domain}", response_model=NginxSite)
async def sites(domain: str = Query(..., description="站点域名")):
    """获取当前站点"""
    return await deploy_service.get_site_info(domain)  ;




