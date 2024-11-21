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

    async def restart_nginx(self):
        """重启Nginx服务"""
        try:
            # 先测试配置
            await run_command("nginx -t")
            # 重启服务
            await run_command("systemctl restart nginx")
            logger.info("Nginx服务重启成功")
        except Exception as e:
            logger.error(f"Nginx服务重启失败: {str(e)}")
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
            
            # 设置目录权限
            await run_command(f"chown -R {nginx_user} {site_root}")
            await run_command(f"chmod -R 755 {site_root}")
            
            # 确保日志目录存在
            log_dir = "/var/log/nginx"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            await run_command(f"chown -R {nginx_user} {log_dir}")
            
            # 生成配置文件
            config_content = generate_nginx_config(site)
            config_path = get_nginx_config_path(site.domain)
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 设置配置文件权限
            await run_command(f"chown {nginx_user} {config_path}")
            await run_command("chmod 644 {config_path}")
            
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
            
            # 重启Nginx
            await self.restart_nginx()
            
            # 验证站点是否可访问
            try:
                await run_command(f"curl -s -I http://{site.domain} || true")
            except Exception as e:
                logger.warning(f"站点访问测试失败: {str(e)}")
            
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
                logger.info(f"删除配置文件: {config_path}")
            
            # 删除软链接
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
                logger.info(f"删除软链接: {enabled_path}")
            
            # 删除站点目录
            if os.path.exists(site_root):
                await run_command(f"rm -rf {site_root}")
                logger.info(f"删除站点目录: {site_root}")
            
            # 删除日志文件
            log_files = [
                f"/var/log/nginx/{domain}.access.log",
                f"/var/log/nginx/{domain}.error.log"
            ]
            for log_file in log_files:
                if os.path.exists(log_file):
                    os.remove(log_file)
                    logger.info(f"删除日志文件: {log_file}")

            # 清理Nginx缓存
            try:
                # 停止Nginx
                await run_command("systemctl stop nginx")
                logger.info("Nginx服务已停止")

                # 清理缓存目录
                cache_dirs = [
                    "/var/cache/nginx",
                    "/var/tmp/nginx"
                ]
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        await run_command(f"rm -rf {cache_dir}/*")
                        logger.info(f"清理缓存目录: {cache_dir}")

                # 重新创建缓存目录
                for cache_dir in cache_dirs:
                    os.makedirs(cache_dir, exist_ok=True)
                    nginx_user = await get_nginx_user()
                    await run_command(f"chown -R {nginx_user} {cache_dir}")
                    await run_command(f"chmod -R 755 {cache_dir}")

                # 启动Nginx
                await run_command("systemctl start nginx")
                logger.info("Nginx服务已重启")

            except Exception as e:
                logger.error(f"清理缓存失败: {str(e)}")
                # 确保Nginx重新启动
                try:
                    await run_command("systemctl start nginx")
                except:
                    pass
                raise

            # 验证域名是否已经无法访问
            try:
                result = await run_command(f"curl -s -I http://{domain} || true")
                if "200 OK" in result or "301 Moved Permanently" in result:
                    logger.warning(f"警告：域名 {domain} 仍然可以访问")
                    # 强制重新加载Nginx配置
                    await run_command("systemctl reload nginx")
            except:
                pass

            return NginxResponse(
                success=True,
                message=f"站点 {domain} 删除成功"
            )
            
        except Exception as e:
            logger.error(f"删除站点失败: {str(e)}")
            # 确保Nginx在发生错误时也能重新启动
            try:
                await run_command("systemctl start nginx")
            except:
                pass
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