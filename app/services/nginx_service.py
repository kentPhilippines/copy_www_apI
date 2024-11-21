import os
import aiofiles
from typing import List, Optional
from app.schemas.nginx import NginxSite, NginxResponse
from app.utils.shell import run_command
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class NginxService:
    """Nginx服务管理"""

    async def _ensure_nginx_user(self) -> str:
        """确保Nginx用户存在"""
        return "nginx:nginx"

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建站点配置"""
        try:
            nginx_user = await self._ensure_nginx_user()
            
            # 创建站点目录
            site_root = f"/var/www/{site.domain}"
            os.makedirs(site_root, exist_ok=True)
            await run_command(f"chown -R {nginx_user} {site_root}")
            await run_command(f"chmod -R 755 {site_root}")
            
            # 生成并写入配置文件
            config_content = generate_nginx_config(site)
            config_path = f"/etc/nginx/conf.d/{site.domain}.conf"
            
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            await run_command(f"chown {nginx_user} {config_path}")
            await run_command(f"chmod 644 {config_path}")
            
            # 重启Nginx
            await run_command("nginx -s reload")
            
            return NginxResponse(
                success=True,
                message=f"站点 {site.domain} 创建成功",
                data={
                    "domain": site.domain,
                    "config_file": config_path,
                    "root_path": site_root
                }
            )
            
        except Exception as e:
            logger.error(f"创建站点失败: {str(e)}")
            raise

    async def delete_site(self, domain: str) -> NginxResponse:
        """删除站点配置"""
        try:
            # 删除配置文件和站点目录
            config_path = f"/etc/nginx/conf.d/{domain}.conf"
            site_root = f"/var/www/{domain}"
            
            if os.path.exists(config_path):
                os.remove(config_path)
            
            if os.path.exists(site_root):
                await run_command(f"rm -rf {site_root}")
            
            # 重启Nginx
            await run_command("nginx -s reload")
            
            return NginxResponse(
                success=True,
                message=f"站点 {domain} 删除成功"
            )
            
        except Exception as e:
            logger.error(f"删除站点失败: {str(e)}")
            raise 