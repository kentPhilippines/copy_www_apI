import os
from typing import Optional
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.schemas.deploy import DeployRequest, DeployResponse
from app.schemas.nginx import NginxSite, SSLInfo
from app.core.logger import setup_logger
import aiofiles
import re

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

    async def get_site_info(self, domain: str) -> Optional[NginxSite]:
        """获取站点信息"""
        try:
            config_file = f"/etc/nginx/conf.d/{domain}.conf"
            if not os.path.exists(config_file):
                return None
            
            # 读取配置文件
            async with aiofiles.open(config_file, 'r') as f:
                config = await f.read()
            
            # 解析配置获取信息
            ssl_enabled = 'ssl' in config
            proxy_port = 9099  # 默认端口
            
            # 尝试从配置中提取代理端口
            port_match = re.search(r'proxy_pass\s+http://127\.0\.0\.1:(\d+)', config)
            if port_match:
                proxy_port = int(port_match.group(1))
            
            # 检查SSL证书
            ssl_info = None
            if ssl_enabled:
                cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
                ssl_info = SSLInfo(
                    cert_path=cert_path,
                    key_path=key_path,
                    cert_exists=os.path.exists(cert_path),
                    key_exists=os.path.exists(key_path)
                )
            
            return NginxSite(
                domain=domain,
                root_path=f"/var/www/{domain}",
                ssl_enabled=ssl_enabled,
                ssl_info=ssl_info,
                proxy_port=proxy_port
            )
            
        except Exception as e:
            self.logger.error(f"获取站点信息失败: {str(e)}")
            return None