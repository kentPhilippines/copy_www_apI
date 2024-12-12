from fastapi import APIRouter, HTTPException
from app.services.deploy_service import DeployService
from app.schemas.deploy import DeployRequest, DeployResponse

router = APIRouter()
deploy_service = DeployService()

@router.post("/sites", response_model=DeployResponse)
async def deploy_site(request: DeployRequest):
    """
    部署新站点
    
    请求参数:
    - domain: 站点域名,如 example.com
    - enable_ssl: 是否启用SSL证书,布尔值
    - ssl_email: SSL证书申请邮箱(enable_ssl为true时必填)
    - proxy_port: 反向代理端口,默认9099
    - custom_config: 自定义Nginx配置(可选)
    
    返回数据:    ```json
    {
        "success": true,
        "message": "站点部署成功",
        "data": {
            "domain": "example.com",
            "config_file": "/etc/nginx/conf.d/example.com.conf",
            "root_path": "/var/www/example.com"
        }
    }    ```
    
    注意事项:
    1. 域名必须已解析到服务器IP
    2. 启用SSL时会自动申请Let's Encrypt证书
    3. 会自动配置反向代理到指定端口
    4. 支持WebSocket
    """
    try:
        return await deploy_service.deploy_site(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=DeployResponse)
async def remove_site(domain: str):
    """
    删除站点
    
    参数:
    - domain: 站点域名
    
    返回数据:    ```json
    {
        "success": true,
        "message": "站点删除成功"
    }    ```
    
    执行操作:
    1. 删除Nginx配置文件
    2. 删除站点目录
    3. 删除SSL证书(如果有)
    4. 重启Nginx服务
    """
    try:
        return await deploy_service.remove_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
