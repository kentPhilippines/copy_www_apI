from fastapi import APIRouter, HTTPException, Depends, WebSocket, Query, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from app.services.deploy_service import DeployService
from app.schemas.nginx import (
    NginxSite,
)

router = APIRouter()
deploy_service = DeployService()    




@router.get("/{domain}", response_model=Dict[str, Any])
async def get_site(domain: str):
    """获取站点详情"""
    try:
        site = await deploy_service.get_site_info(domain)
        if not site:
            raise HTTPException(status_code=404, detail="站点不存在")
        
        return {
            "domain": site.domain,
            "status": site.status,
            "config_file": site.config_file,
            "root_path": site.root_path,
            "root_exists": site.root_exists,
            "ports": site.ports,
            "ssl_ports": site.ssl_ports,
            "ssl_enabled": site.ssl_enabled,
            "ssl_info": site.ssl_info.dict() if site.ssl_info else None,
            "logs": site.logs.dict() if site.logs else None,
            "access_urls": site.access_urls.dict() if site.access_urls else {
                "http": [],
                "https": []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





