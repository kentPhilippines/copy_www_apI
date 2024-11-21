import os
import aiofiles
import asyncio
from typing import List
from app.schemas.nginx import NginxSite, NginxStatus, NginxResponse
from app.utils.shell import run_command
from app.utils.nginx import generate_nginx_config

class NginxService:
    NGINX_SITES_PATH = "/etc/nginx/sites-available"
    NGINX_ENABLED_PATH = "/etc/nginx/sites-enabled"

    async def get_status(self) -> NginxStatus:
        """获取Nginx状态"""
        try:
            result = await run_command("systemctl is-active nginx")
            is_running = result.strip() == "active"
            
            # 获取进程信息
            if is_running:
                pid = await run_command("pidof nginx")
                version = await run_command("nginx -v 2>&1")
            else:
                pid = None
                version = None
                
            return NginxStatus(
                is_running=is_running,
                pid=pid.strip() if pid else None,
                version=version.strip() if version else None
            )
        except Exception as e:
            raise Exception(f"Failed to get nginx status: {str(e)}")

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建网站配置"""
        try:
            # 生成配置文件
            config_content = generate_nginx_config(site)
            config_path = f"{self.NGINX_SITES_PATH}/{site.domain}.conf"
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 创建软链接
            enabled_path = f"{self.NGINX_ENABLED_PATH}/{site.domain}.conf"
            if not os.path.exists(enabled_path):
                os.symlink(config_path, enabled_path)
            
            # 测试配置
            await run_command("nginx -t")
            
            # 重新加载配置
            await self.reload()
            
            return NginxResponse(
                success=True,
                message=f"Site {site.domain} created successfully"
            )
            
        except Exception as e:
            raise Exception(f"Failed to create site: {str(e)}")

    async def delete_site(self, domain: str) -> NginxResponse:
        """删除网站配置"""
        try:
            config_path = f"{self.NGINX_SITES_PATH}/{domain}.conf"
            enabled_path = f"{self.NGINX_ENABLED_PATH}/{domain}.conf"
            
            # 删除配置文件
            if os.path.exists(config_path):
                os.remove(config_path)
            
            # 删除软链接
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
            
            # 重新加载配置
            await self.reload()
            
            return NginxResponse(
                success=True,
                message=f"Site {domain} deleted successfully"
            )
            
        except Exception as e:
            raise Exception(f"Failed to delete site: {str(e)}")

    async def list_sites(self) -> List[NginxSite]:
        """获取所有网站配置"""
        sites = []
        try:
            for filename in os.listdir(self.NGINX_SITES_PATH):
                if filename.endswith('.conf'):
                    domain = filename[:-5]  # 移除.conf后缀
                    config_path = f"{self.NGINX_SITES_PATH}/{filename}"
                    
                    async with aiofiles.open(config_path, 'r') as f:
                        content = await f.read()
                        
                    # 解析配置文件获取信息
                    # 这里需要实现配置文件解析逻辑
                    sites.append(NginxSite(
                        domain=domain,
                        root_path="/var/www/html/" + domain,
                        # 其他配置信息...
                    ))
            return sites
            
        except Exception as e:
            raise Exception(f"Failed to list sites: {str(e)}")

    async def reload(self) -> NginxResponse:
        """重新加载Nginx配置"""
        try:
            await run_command("systemctl reload nginx")
            return NginxResponse(
                success=True,
                message="Nginx configuration reloaded successfully"
            )
        except Exception as e:
            raise Exception(f"Failed to reload nginx: {str(e)}") 