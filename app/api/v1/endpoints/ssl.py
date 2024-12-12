from fastapi import APIRouter, HTTPException
from app.services.ssl_service import SSLService
from app.schemas.ssl import SSLRequest, SSLResponse

router = APIRouter()
ssl_service = SSLService()

@router.post("/certificates", response_model=SSLResponse)
async def create_certificate(request: SSLRequest):
    """
    申请SSL证书
    
    请求参数:
    - domain: 站点域名
    - email: 证书申请邮箱
    
    返回数据:    ```json
    {
        "success": true,
        "message": "证书申请成功",
        "data": {
            "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
            "key_path": "/etc/letsencrypt/live/example.com/privkey.pem"
        }
    }    ```
    
    注意事项:
    1. 域名必须已解析到服务器IP
    2. 申请过程中会临时停止Nginx服务
    3. 证书有效期90天,建议设置自动续期
    4. 使用Let's Encrypt免费证书
    """
    try:
        result = await ssl_service.create_certificate(
            domain=request.domain,
            email=request.email
        )
        return SSLResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/certificates/{domain}", response_model=SSLResponse)
async def delete_certificate(domain: str):
    """
    删除SSL证书
    
    参数:
    - domain: 站点域名
    
    返回数据:    ```json
    {
        "success": true,
        "message": "证书删除成功"
    }    ```
    
    执行操作:
    1. 删除证书文件
    2. 删除证书配置
    3. 从Let's Encrypt注销证书
    """
    try:
        result = await ssl_service.delete_certificate(domain)
        return SSLResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 