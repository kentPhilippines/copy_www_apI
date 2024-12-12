from fastapi import APIRouter, HTTPException, Depends, WebSocket, Query, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from app.services.deploy_service import DeployService
from app.schemas.nginx import (
    NginxSite,
)
import os
from app.core.logger import setup_logger

router = APIRouter()
deploy_service = DeployService()    
logger = setup_logger(__name__)




@router.get("/", response_model=List[Dict[str, Any]])
async def list_sites():
    """
    获取所有站点列表
    
    响应示例:    ```json
    [
        {
            "domain": "example.com",
            "status": "active",
            "ssl_enabled": true,
            "proxy_port": 9099,
            "config_file": "/etc/nginx/conf.d/example.com.conf",
            "root_path": "/var/www/example.com"
        },
        {
            "domain": "test.com",
            "status": "active",
            "ssl_enabled": false,
            "proxy_port": 8080,
            "config_file": "/etc/nginx/conf.d/test.com.conf",
            "root_path": "/var/www/test.com"
        }
    ]    ```
    
    失败响应示例:    ```json
    {
        "detail": "获取站点列表失败: 权限不足"
    }    ```
    """
    logger.info("[站点列表] 接收到请求")
    try:
        sites = []
        conf_dir = "/etc/nginx/conf.d"
        for conf_file in os.listdir(conf_dir):
            if conf_file.endswith('.conf'):
                domain = conf_file.replace('.conf', '')
                logger.debug(f"[站点列表] 获取站点信息 - 域名: {domain}")
                site_info = await deploy_service.get_site_info(domain)
                if site_info:
                    sites.append({
                        "domain": site_info.domain,
                        "status": "active",
                        "ssl_enabled": site_info.ssl_enabled,
                        "proxy_port": site_info.proxy_port,
                        "config_file": f"{conf_dir}/{conf_file}",
                        "root_path": f"/var/www/{domain}"
                    })
        logger.info(f"[站点列表] 成功 - 共获取到 {len(sites)} 个站点")
        return sites
    except Exception as e:
        error_msg = f"获取站点列表失败: {str(e)}"
        logger.error(f"[站点列表] 异常 - 错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@router.get("/{domain}", response_model=Dict[str, Any])
async def get_site(domain: str):
    """
    获取站点详情
    
    参数:
    - domain: 站点域名
    
    返回数据:    ```json
    {
        "domain": "example.com",
        "status": "active",
        "ssl_enabled": true,
        "proxy_port": 9099,
        "config_file": "/etc/nginx/conf.d/example.com.conf",
        "root_path": "/var/www/example.com",
        "ssl_info": {
            "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
            "key_path": "/etc/letsencrypt/live/example.com/privkey.pem",
            "cert_exists": true,
            "key_exists": true
        }
    }    ```
    """
    logger.info(f"收到获取站点详情请求: {domain}")
    try:
        site = await deploy_service.get_site_info(domain)
        if not site:
            error_msg = f"站点不存在: {domain}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        result = {
            "domain": site.domain,
            "status": "active",
            "ssl_enabled": site.ssl_enabled,
            "proxy_port": site.proxy_port,
            "config_file": f"/etc/nginx/conf.d/{domain}.conf",
            "root_path": f"/var/www/{domain}",
            "ssl_info": site.ssl_info.dict() if site.ssl_info else None
        }
        logger.info(f"获取站点详情成功: {result}")
        return result
    except Exception as e:
        error_msg = f"获取站点详情失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)





