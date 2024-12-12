from fastapi import APIRouter, HTTPException
from app.services.ssl_service import SSLService
from app.schemas.ssl import SSLRequest, SSLResponse
from app.core.logger import setup_logger

router = APIRouter()
ssl_service = SSLService()
logger = setup_logger(__name__)

@router.post("/certificates", response_model=SSLResponse)
async def create_certificate(request: SSLRequest):
    """
    申请SSL证书
    
    请求示例:    ```json
    {
        "domain": "example.com",
        "email": "admin@example.com"
    }    ```
    
    成功响应示例:    ```json
    {
        "success": true,
        "message": "证书申请成功",
        "data": {
            "domain": "example.com",
            "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
            "key_path": "/etc/letsencrypt/live/example.com/privkey.pem",
            "expires": "2024-03-20T12:00:00Z"
        }
    }    ```
    
    失败响应示例:    ```json
    {
        "success": false,
        "message": "证书申请失败: DNS验证失败",
        "data": null
    }    ```
    """
    logger.info(f"[申请证书] 接收到请求 - 域名: {request.domain}, 邮箱: {request.email}")
    try:
        result = await ssl_service.create_certificate(
            domain=request.domain,
            email=request.email
        )
        if result["success"]:
            logger.info(f"[申请证书] 成功 - 域名: {request.domain}, "
                       f"证书路径: {result.get('cert_path')}")
        else:
            logger.error(f"[申请证书] 失败 - 域名: {request.domain}, "
                        f"原因: {result.get('message')}")
        return SSLResponse(**result)
    except Exception as e:
        error_msg = f"证书申请失败: {str(e)}"
        logger.error(f"[申请证书] 异常 - 域名: {request.domain}, 错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@router.delete("/certificates/{domain}", response_model=SSLResponse)
async def delete_certificate(domain: str):
    """
    删除SSL证书
    
    请求示例:
    DELETE /api/v1/ssl/certificates/example.com
    
    成功响应示例:    ```json
    {
        "success": true,
        "message": "证书删除成功",
        "data": {
            "domain": "example.com",
            "cert_removed": true,
            "key_removed": true
        }
    }    ```
    
    失败响应示例:    ```json
    {
        "success": false,
        "message": "证书删除失败: 证书文件不存在",
        "data": null
    }    ```
    """
    logger.info(f"[删除证书] 接收到请求 - 域名: {domain}")
    try:
        result = await ssl_service.delete_certificate(domain)
        if result["success"]:
            logger.info(f"[删除证书] 成功 - 域名: {domain}")
        else:
            logger.error(f"[删除证书] 失败 - 域名: {domain}, 原因: {result['message']}")
        return SSLResponse(**result)
    except Exception as e:
        error_msg = f"证书删除失败: {str(e)}"
        return SSLResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 