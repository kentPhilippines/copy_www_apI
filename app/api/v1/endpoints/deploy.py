from fastapi import APIRouter, HTTPException
from app.services.deploy_service import DeployService
from app.schemas.deploy import DeployRequest, DeployResponse

router = APIRouter()
deploy_service = DeployService()

@router.post("/sites", response_model=DeployResponse)
async def deploy_site(request: DeployRequest):
    """部署新站点"""
    try:
        return await deploy_service.deploy_site(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=DeployResponse)
async def remove_site(domain: str):
    """移除站点"""
    try:
        return await deploy_service.remove_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
