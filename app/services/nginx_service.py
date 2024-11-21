import os
import aiofiles
from typing import List, Optional
from app.schemas.nginx import NginxSite, NginxStatus, NginxResponse
from app.utils.shell import run_command
from app.utils.nginx import (
    generate_nginx_config,
    get_nginx_config_path,
    get_nginx_enabled_path,
    create_nginx_directories,
    get_site_root_path,
    get_nginx_user
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class NginxService:
    """Nginx服务管理"""

    async def get_status(self) -> NginxStatus:
        """获取Nginx状态"""
        try:
            # 检查Nginx进程
            is_running = False
            pid = None
            version = None

            try:
                # 使用 ps 命令检查 Nginx 进程
                ps_result = await run_command("ps aux | grep nginx | grep -v grep")
                is_running = bool(ps_result.strip())
                
                if is_running:
                    # 获取主进程PID
                    pid_result = await run_command("pidof nginx")
                    pid = pid_result.strip()
                    
                    # 获取Nginx版本
                    version_result = await run_command("nginx -v 2>&1")
                    version = version_result.strip()
            except Exception:
                # 如果命令失败，假设Nginx未运行
                pass

            return NginxStatus(
                is_running=is_running,
                pid=pid,
                version=version
            )
        except Exception as e:
            logger.error(f"获取Nginx状态失败: {str(e)}")
            raise

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建站点配置"""
        try:
            # 创建必要的目录
            create_nginx_directories()
            
            # 获取正确的Nginx用户
            nginx_user = await get_nginx_user()
            
            # 确保站点目录存在并设置权限
            site_root = get_site_root_path(site.domain)
            os.makedirs(site_root, exist_ok=True)
            await run_command(f"chown -R {nginx_user} {site_root}")
            await run_command(f"chmod -R 755 {site_root}")
            
            # 生成配置文件
            config_content = generate_nginx_config(site)
            config_path = get_nginx_config_path(site.domain)
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 创建软链接
            enabled_path = get_nginx_enabled_path(site.domain)
            if not os.path.exists(enabled_path):
                os.symlink(config_path, enabled_path)
            
            # 测试配置
            try:
                await run_command("nginx -t")
            except Exception as e:
                logger.error(f"Nginx配置测试失败: {str(e)}")
                # 如果配置测试失败，删除配置文件和软链接
                os.remove(config_path)
                if os.path.exists(enabled_path):
                    os.remove(enabled_path)
                raise
            
            # 重新加载配置
            await self.reload()
            
            return NginxResponse(
                success=True,
                message=f"站点 {site.domain} 创建成功"
            )
            
        except Exception as e:
            logger.error(f"创建站点失败: {str(e)}")
            raise

    async def delete_site(self, domain: str) -> NginxResponse:
        """删除站点配置"""
        try:
            config_path = get_nginx_config_path(domain)
            enabled_path = get_nginx_enabled_path(domain)
            site_root = get_site_root_path(domain)
            
            # 删除配置文件
            if os.path.exists(config_path):
                os.remove(config_path)
            
            # 删除软链接
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
            
            # 删除站点目录（可选）
            if os.path.exists(site_root):
                await run_command(f"rm -rf {site_root}")
            
            # 重新加载配置
            await self.reload()
            
            # 清理缓存（可选）
            try:
                await run_command("nginx -s flush_cache")
            except:
                pass
            
            return NginxResponse(
                success=True,
                message=f"站点 {domain} 删除成功"
            )
            
        except Exception as e:
            logger.error(f"删除站点失败: {str(e)}")
            raise

    async def list_sites(self) -> List[NginxSite]:
        """获取所有站点配置"""
        sites = []
        try:
            sites_path = "/etc/nginx/sites-enabled"
            if os.path.exists(sites_path):
                for filename in os.listdir(sites_path):
                    if filename.endswith('.conf'):
                        domain = filename[:-5]  # 移除.conf后缀
                        config_path = os.path.join(sites_path, filename)
                        
                        async with aiofiles.open(config_path, 'r') as f:
                            content = await f.read()
                            
                        # 解析配置文件获取信息
                        sites.append(NginxSite(
                            domain=domain,
                            root_path=get_site_root_path(domain),
                            php_enabled='php' in content.lower()
                        ))
            return sites
            
        except Exception as e:
            logger.error(f"获取站点列表失败: {str(e)}")
            raise

    async def reload(self) -> NginxResponse:
        """重新加载Nginx配置"""
        try:
            await run_command("nginx -s reload")
            return NginxResponse(
                success=True,
                message="Nginx配置重新加载成功"
            )
        except Exception as e:
            logger.error(f"重新加载Nginx配置失败: {str(e)}")
            raise 