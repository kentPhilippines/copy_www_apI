from fastapi import APIRouter, HTTPException
from app.services.deploy_service import DeployService
from app.schemas.deploy import DeployRequest, DeployResponse
from app.core.logger import setup_logger

router = APIRouter()
deploy_service = DeployService()
logger = setup_logger(__name__)

@router.post("/sites", response_model=DeployResponse)
async def deploy_site(request: DeployRequest):
    """
    部署新站点
    
    请求示例:    ```json
    {
        "domain": "example.com",
        "enable_ssl": true,
        "ssl_email": "admin@example.com",
        "proxy_ip": "192.168.1.100",     # 可选,默认127.0.0.1
        "proxy_port": 9099,              # 可选,默认9099
        "proxy_host": "api.example.com", # 可选,默认使用domain
        "custom_config": "client_max_body_size 100M;"
    }    ```
    
    成功响应示例:    ```json
    {
        "success": true,
        "message": "站点部署成功",
        "data": {
            "domain": "example.com",
            "config_file": "/etc/nginx/conf.d/example.com.conf",
            "root_path": "/var/www/example.com",
            "ssl_enabled": true,
            "proxy_ip": "192.168.1.100",
            "proxy_port": 9099,
            "proxy_host": "api.example.com"
        }
    }    ```
    
    失败响应示例:    ```json
    {
        "success": false,
        "message": "部署失败: SSL证书申请失败",
        "data": null
    }    ```
    """
    logger.info(f"[部署站点] 接收到请求 - 域名: {request.domain}, SSL: {request.enable_ssl}, "
                f"代理IP: {request.proxy_ip}, 端口: {request.proxy_port}, "
                f"Host: {request.proxy_host or request.domain}")
    try:
        result = await deploy_service.deploy_site(request)
        if result.success:
            logger.info(f"[部署站点] 成功 - 域名: {request.domain}, "
                       f"配置文件: {result.data.get('config_file')}, "
                       f"站点目录: {result.data.get('root_path')}, "
                       f"代理目标: {request.proxy_ip}:{request.proxy_port}")
        else:
            logger.error(f"[部署站点] 失败 - 域名: {request.domain}, 原因: {result.message}")
        return result
    except Exception as e:
        error_msg = f"部署失败: {str(e)}"
        logger.error(f"[部署站点] 异常 - 域名: {request.domain}, 错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@router.delete("/sites/{domain}", response_model=DeployResponse)
async def remove_site(domain: str):
    """
    删除站点
    
    请求示例:
    DELETE /api/v1/deploy/sites/example.com
    
    成功响应示例:    ```json
    {
        "success": true,
        "message": "站点删除成功",
        "data": {
            "domain": "example.com",
            "config_removed": true,
            "files_removed": true,
            "ssl_removed": true
        }
    }    ```
    
    失败响应示例:    ```json
    {
        "success": false,
        "message": "删除失败: 配置文件不存在",
        "data": null
    }    ```
    """
    logger.info(f"[删除站点] 接收到请求 - 域名: {domain}")
    try:
        result = await deploy_service.remove_site(domain)
        if result.success:
            logger.info(f"[删除站点] 成功 - 域名: {domain}")
        else:
            logger.error(f"[删除站点] 失败 - 域名: {domain}, 原因: {result.message}")
        return result
    except Exception as e:
        error_msg = f"删除失败: {str(e)}"
        logger.error(f"[删除站点] 异常 - 域名: {domain}, 错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
