import os
import shutil
from typing import List
from app.schemas.deploy import DeployRequest, DeployStatus, DeployResponse, SiteInfo
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.utils.shell import run_command

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()
        self.sites_root = "/var/www"

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 1. 创建站点目录
            site_path = os.path.join(self.sites_root, request.domain)
            os.makedirs(site_path, exist_ok=True)

            # 2. 部署代码
            if request.deploy_type == "static":
                await self._deploy_static(request, site_path)
            elif request.deploy_type == "php":
                await self._deploy_php(request, site_path)
            else:
                raise ValueError(f"Unsupported deploy type: {request.deploy_type}")

            # 3. 配置Nginx
            await self.nginx_service.create_site({
                "domain": request.domain,
                "root_path": site_path,
                "php_enabled": request.deploy_type == "php"
            })

            # 4. 配置SSL（如果需要）
            if request.enable_ssl:
                await self.ssl_service.create_certificate({
                    "domain": request.domain,
                    "email": request.ssl_email
                })

            return DeployResponse(
                success=True,
                message=f"Site {request.domain} deployed successfully"
            )

        except Exception as e:
            # 清理失败的部署
            await self._cleanup_failed_deploy(request.domain)
            raise Exception(f"Deploy failed: {str(e)}")

    async def list_sites(self) -> List[SiteInfo]:
        """获取所有已部署的站点"""
        sites = []
        try:
            for domain in os.listdir(self.sites_root):
                site_path = os.path.join(self.sites_root, domain)
                if os.path.isdir(site_path):
                    # 获取站点信息
                    status = await self.get_site_status(domain)
                    sites.append(SiteInfo(
                        domain=domain,
                        deploy_type=self._detect_deploy_type(site_path),
                        path=site_path,
                        status=status
                    ))
            return sites
        except Exception as e:
            raise Exception(f"Failed to list sites: {str(e)}")

    async def remove_site(self, domain: str) -> DeployResponse:
        """移除站点"""
        try:
            # 1. 删除SSL证书（如果存在）
            try:
                await self.ssl_service.delete_certificate(domain)
            except Exception:
                pass  # 忽略SSL删除错误

            # 2. 删除Nginx配置
            await self.nginx_service.delete_site(domain)

            # 3. 删除站点文件
            site_path = os.path.join(self.sites_root, domain)
            if os.path.exists(site_path):
                shutil.rmtree(site_path)

            return DeployResponse(
                success=True,
                message=f"Site {domain} removed successfully"
            )
        except Exception as e:
            raise Exception(f"Failed to remove site: {str(e)}")

    async def get_site_status(self, domain: str) -> DeployStatus:
        """获取站点状态"""
        try:
            # 检查Nginx配置是否存在
            nginx_config_exists = os.path.exists(
                f"/etc/nginx/sites-enabled/{domain}.conf"
            )

            # 检查SSL证书是否存在
            ssl_exists = os.path.exists(
                f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            )

            # 检查站点是否可访问
            try:
                await run_command(f"curl -sI https://{domain}")
                is_accessible = True
            except:
                is_accessible = False

            return DeployStatus(
                nginx_configured=nginx_config_exists,
                ssl_configured=ssl_exists,
                is_accessible=is_accessible
            )
        except Exception as e:
            raise Exception(f"Failed to get site status: {str(e)}")

    async def _deploy_static(self, request: DeployRequest, site_path: str):
        """部署静态站点"""
        # 复制静态文件到站点目录
        if request.source_path and os.path.exists(request.source_path):
            for item in os.listdir(request.source_path):
                s = os.path.join(request.source_path, item)
                d = os.path.join(site_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        else:
            # 创建默认索引页
            index_path = os.path.join(site_path, "index.html")
            with open(index_path, "w") as f:
                f.write(f"<h1>Welcome to {request.domain}</h1>")

    async def _deploy_php(self, request: DeployRequest, site_path: str):
        """部署PHP站点"""
        # 1. 确保PHP-FPM已安装
        try:
            await run_command("which php-fpm")
        except:
            await run_command("apt-get update && apt-get install -y php-fpm")

        # 2. 部署PHP文件
        if request.source_path and os.path.exists(request.source_path):
            for item in os.listdir(request.source_path):
                s = os.path.join(request.source_path, item)
                d = os.path.join(site_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        else:
            # 创建默认PHP文件
            index_path = os.path.join(site_path, "index.php")
            with open(index_path, "w") as f:
                f.write("<?php phpinfo(); ?>")

        # 3. 设置目录权限
        await run_command(f"chown -R www-data:www-data {site_path}")
        await run_command(f"chmod -R 755 {site_path}")

    async def _cleanup_failed_deploy(self, domain: str):
        """清理失败的部署"""
        try:
            await self.remove_site(domain)
        except:
            pass  # 忽略清理错误 