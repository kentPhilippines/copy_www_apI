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

    async def _init_nginx_config(self):
        """初始化Nginx配置"""
        try:
            # 禁用默认站点
            default_site = "/etc/nginx/sites-enabled/default"
            if os.path.exists(default_site):
                os.remove(default_site)
                logger.info("已禁用默认站点")

            # 确保配置目录存在
            dirs = [
                "/etc/nginx/sites-available",
                "/etc/nginx/sites-enabled",
                "/var/www",
                "/var/log/nginx"
            ]
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)

            # 设置正确的权限
            nginx_user = await get_nginx_user()
            for dir_path in dirs:
                await run_command(f"chown -R {nginx_user} {dir_path}")
                await run_command(f"chmod -R 755 {dir_path}")

        except Exception as e:
            logger.error(f"初始化Nginx配置失败: {str(e)}")
            raise

    async def verify_site_access(self, domain: str) -> bool:
        """验证站点是否可以访问"""
        try:
            # 使用curl检查站点访问
            result = await run_command(f"curl -s -I http://{domain}")
            if "200 OK" in result:
                # 获取页面内容
                content = await run_command(f"curl -s http://{domain}")
                if "部署状态" in content:
                    logger.info(f"站点 {domain} 可以正常访问测试页面")
                    return True
                else:
                    logger.warning(f"站点 {domain} 返回了非预期的内容")
            else:
                logger.warning(f"站点 {domain} 返回了非200状态码")
            return False
        except Exception as e:
            logger.error(f"验证站点访问失败: {str(e)}")
            return False

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建站点配置"""
        try:
            # 初始化Nginx配置
            await self._init_nginx_config()
            
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
            
            # 确保配置目录存在
            config_dir = os.path.dirname(config_path)
            os.makedirs(config_dir, exist_ok=True)
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 设置配置文件权限
            await run_command(f"chown {nginx_user} {config_path}")
            await run_command(f"chmod 644 {config_path}")
            
            # 创建软链接
            enabled_path = get_nginx_enabled_path(site.domain)
            enabled_dir = os.path.dirname(enabled_path)
            os.makedirs(enabled_dir, exist_ok=True)
            
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
            os.symlink(config_path, enabled_path)
            
            # 测试配置
            try:
                await run_command("nginx -t")
            except Exception as e:
                logger.error(f"Nginx配置测试失败: {str(e)}")
                # 如果配置测试失败，删除配置文件和软链接
                if os.path.exists(config_path):
                    os.remove(config_path)
                if os.path.exists(enabled_path):
                    os.remove(enabled_path)
                raise
            
            # 重启Nginx
            await self.restart_nginx()
            
            # 等待几秒让服务完全启动
            await run_command("sleep 3")
            
            # 验证站点访问
            if not await self.verify_site_access(site.domain):
                logger.error(f"站点 {site.domain} 无法访问，尝试重新加载配置")
                # 尝试重新加载配置
                await run_command("nginx -s reload")
                await run_command("sleep 2")
                
                # 再次验证
                if not await self.verify_site_access(site.domain):
                    raise Exception(f"站点 {site.domain} 部署后无法访问")
            
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
            # 先停止Nginx服务
            await run_command("systemctl stop nginx")
            logger.info("Nginx服务已停止")

            # 删除所有相关文件和目录
            paths_to_delete = [
                # Nginx配置文件
                f"/etc/nginx/sites-available/{domain}.conf",
                f"/etc/nginx/sites-enabled/{domain}.conf",
                # 站点目录
                f"/var/www/{domain}",
                # 日志文件
                f"/var/log/nginx/{domain}.access.log",
                f"/var/log/nginx/{domain}.error.log",
                # 可能的SSL证书目录
                f"/etc/letsencrypt/live/{domain}",
                f"/etc/letsencrypt/archive/{domain}",
                f"/etc/letsencrypt/renewal/{domain}.conf"
            ]

            for path in paths_to_delete:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        await run_command(f"rm -rf {path}")
                    else:
                        os.remove(path)
                    logger.info(f"删除: {path}")

            # 清理Nginx缓存
            cache_dirs = [
                "/var/cache/nginx",
                "/var/tmp/nginx",
                "/run/nginx"  # 添加运行时目录
            ]

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    await run_command(f"rm -rf {cache_dir}/*")
                    logger.info(f"清理缓存目录: {cache_dir}")
                    # 重新创建目录
                    os.makedirs(cache_dir, exist_ok=True)

            # 重新设置缓存目录权限
            nginx_user = await get_nginx_user()
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    await run_command(f"chown -R {nginx_user} {cache_dir}")
                    await run_command(f"chmod -R 755 {cache_dir}")

            # 检查并删除可能存在的其他配置引用
            nginx_conf = "/etc/nginx/nginx.conf"
            if os.path.exists(nginx_conf):
                # 创建备份
                await run_command(f"cp {nginx_conf} {nginx_conf}.bak")
                # 删除包含该域名的行
                await run_command(f"sed -i '/{domain}/d' {nginx_conf}")

            # 重新启动Nginx前，测试配置
            try:
                await run_command("nginx -t")
            except Exception as e:
                logger.error(f"Nginx配置测试失败: {str(e)}")
                # 如果测试失败，恢复备份
                if os.path.exists(f"{nginx_conf}.bak"):
                    await run_command(f"mv {nginx_conf}.bak {nginx_conf}")
                raise

            # 完全停止并重启Nginx
            await run_command("systemctl stop nginx")
            await run_command("sleep 2")  # 等待服务完全停止
            await run_command("systemctl start nginx")
            await run_command("sleep 2")  # 等待服务完全启动
            logger.info("Nginx服务已重启")

            # 验证域名是否确实无法访问
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    result = await run_command(f"curl -s -I --connect-timeout 5 http://{domain} || true")
                    if "200 OK" in result or "301 Moved Permanently" in result:
                        logger.warning(f"警告：域名 {domain} 仍然可以访问，尝试强制重载配置")
                        # 强制重载配置
                        await run_command("systemctl stop nginx")
                        await run_command("sleep 2")
                        await run_command("systemctl start nginx")
                        await run_command("sleep 2")
                        retry_count += 1
                    else:
                        logger.info(f"域名 {domain} 已无法访问")
                        break
                except Exception:
                    logger.info(f"域名 {domain} 已无法访问")
                    break

                if retry_count == max_retries:
                    raise Exception(f"无法完全删除站点 {domain} 的访问")

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