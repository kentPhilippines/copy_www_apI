import os
from typing import Optional
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.schemas.deploy import DeployRequest, DeployResponse
from app.schemas.nginx import NginxSite, SSLInfo
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()
        self.logger = logger

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 如果需要SSL，先申请证书
            ssl_info = None
            if request.enable_ssl:
                if not request.ssl_email:
                    return DeployResponse(
                        success=False,
                        message="启用SSL时必须提供邮箱地址"
                    )
                    
                ssl_result = await self.ssl_service.create_certificate(
                    domain=request.domain,
                    email=request.ssl_email
                )
                
                if not ssl_result["success"]:
                    return DeployResponse(
                        success=False,
                        message=f"SSL证书申请失败: {ssl_result['message']}"
                    )
                    
                ssl_info = SSLInfo(
                    cert_path=ssl_result["cert_path"],
                    key_path=ssl_result["key_path"],
                    cert_exists=True,
                    key_exists=True
                )

            # 创建Nginx站点配置
            site = NginxSite(
                domain=request.domain,
                root_path=f"/var/www/{request.domain}",
                ssl_enabled=request.enable_ssl,
                ssl_info=ssl_info,
                proxy_port=request.proxy_port,
                custom_config=request.custom_config
            )
            
            result = await self.nginx_service.create_site(site)
            return DeployResponse(
                success=result.success,
                message=result.message,
                data=result.data
            )

        except Exception as e:
            self.logger.error(f"部署站点失败: {str(e)}")
            return DeployResponse(
                success=False,
                message=f"部署失败: {str(e)}"
            )

    async def remove_site(self, domain: str) -> DeployResponse:
        """移除站点"""
        try:
            # 删除Nginx配置
            config_path = f"/etc/nginx/conf.d/{domain}.conf"
            if os.path.exists(config_path):
                os.remove(config_path)
                
            # 删除站点目录
            site_root = f"/var/www/{domain}"
            if os.path.exists(site_root):
                os.system(f"rm -rf {site_root}")
                
            # 如果有SSL证书，删除证书
            await self.ssl_service.delete_certificate(domain)
            
            # 重启Nginx
            await self.nginx_service.restart_nginx()
            
            return DeployResponse(
                success=True,
                message=f"站点 {domain} 已删除"
            )
            
        except Exception as e:
            self.logger.error(f"删除站点失败: {str(e)}")
            return DeployResponse(
                success=False,
                message=f"删除失败: {str(e)}"
            )