import os
import shutil
from typing import List
from app.schemas.deploy import DeployRequest, DeployStatus, DeployResponse, SiteInfo
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.utils.shell import run_command
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 创建Nginx配置
            nginx_site = {
                "domain": request.domain,
                "root_path": f"/var/www/{request.domain}",
                "php_enabled": request.deploy_type == "php",
                "ssl_enabled": request.enable_ssl
            }
            
            # 创建站点
            await self.nginx_service.create_site(nginx_site)

            # 如果需要SSL，配置证书
            if request.enable_ssl:
                try:
                    await self.ssl_service.create_certificate(
                        domain=request.domain,
                        email=request.ssl_email
                    )
                except Exception as e:
                    logger.error(f"SSL证书配置失败: {str(e)}")
                    # 继续部署，但不启用SSL

            return DeployResponse(
                success=True,
                message=f"站点 {request.domain} 部署成功"
            )

        except Exception as e:
            logger.error(f"部署失败: {str(e)}")
            # 清理失败的部署
            await self._cleanup_failed_deploy(request.domain)
            raise

    async def _cleanup_failed_deploy(self, domain: str):
        """清理失败的部署"""
        try:
            await self.nginx_service.delete_site(domain)
        except Exception as e:
            logger.error(f"清理失败的部署时出错: {str(e)}")

    async def list_sites(self) -> List[SiteInfo]:
        """获取所有已部署的站点"""
        try:
            nginx_sites = await self.nginx_service.list_sites()
            sites = []
            for site in nginx_sites:
                status = await self.get_site_status(site.domain)
                sites.append(SiteInfo(
                    domain=site.domain,
                    deploy_type="php" if site.php_enabled else "static",
                    path=site.root_path,
                    status=status
                ))
            return sites
        except Exception as e:
            logger.error(f"获取站点列表失败: {str(e)}")
            raise

    async def get_site_status(self, domain: str) -> DeployStatus:
        """获取站点状态"""
        try:
            nginx_config_exists = os.path.exists(f"/etc/nginx/sites-enabled/{domain}.conf")
            ssl_exists = os.path.exists(f"/etc/letsencrypt/live/{domain}/fullchain.pem")
            
            # 检查站点是否可访问
            is_accessible = False
            try:
                await run_command(f"curl -sI http://{domain}")
                is_accessible = True
            except:
                pass

            return DeployStatus(
                nginx_configured=nginx_config_exists,
                ssl_configured=ssl_exists,
                is_accessible=is_accessible
            )
        except Exception as e:
            logger.error(f"获取站点状态失败: {str(e)}")
            raise

    async def remove_site(self, domain: str) -> DeployResponse:
        """移除站点"""
        try:
            await self.nginx_service.delete_site(domain)
            return DeployResponse(
                success=True,
                message=f"站点 {domain} 已移除"
            )
        except Exception as e:
            logger.error(f"移除站点失败: {str(e)}")
            raise 