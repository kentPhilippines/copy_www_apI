import os
import aiofiles
from typing import List, Optional
from app.schemas.nginx import NginxSite, NginxStatus, NginxResponse
from app.utils.shell import run_command
from app.utils.nginx import generate_nginx_config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class NginxService:
    """Nginx服务管理"""

    async def _ensure_nginx_user(self) -> str:
        """确保Nginx用户存在"""
        return "nginx:nginx"

    async def restart_nginx(self):
        """重启Nginx服务"""
        try:
            # 先测试配置
            await run_command("nginx -t")
            # 重启服务
            await run_command("systemctl restart nginx")
            await run_command("sleep 2")  # 等待服务启动
            logger.info("Nginx服务重启成功")
        except Exception as e:
            logger.error(f"Nginx服务重启失败: {str(e)}")
            raise

    async def _init_nginx_config(self):
        """初始化Nginx配置"""
        try:
            # 确保Nginx用户存在
            nginx_user = await self._ensure_nginx_user()
            logger.info(f"使用Nginx用户: {nginx_user}")
            
            # 创建必要的目录结构
            dirs = [
                "/etc/nginx/conf.d",
                "/var/www",
                "/var/log/nginx"
            ]
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)
                await run_command(f"chown -R {nginx_user} {dir_path}")
                await run_command(f"chmod -R 755 {dir_path}")

            # 创建主配置文件
            main_config = f"""
user nginx;
worker_processes auto;
pid /run/nginx.pid;

events {{
    worker_connections 1024;
    multi_accept on;
    use epoll;
}}

http {{
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    # 日志配置
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip压缩
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}}
"""
            # 写入主配置文件
            nginx_conf_path = "/etc/nginx/nginx.conf"
            async with aiofiles.open(nginx_conf_path, 'w') as f:
                await f.write(main_config)

            # 设置配置文件权限
            await run_command(f"chown {nginx_user} {nginx_conf_path}")
            await run_command(f"chmod 644 {nginx_conf_path}")

            # 删除默认配置
            default_conf = "/etc/nginx/conf.d/default.conf"
            if os.path.exists(default_conf):
                os.remove(default_conf)
                logger.info("删除默认配置")

            # 创建新的默认配置
            default_conf = """
# 默认服务器配置
server {
    listen 80;
    server_name _;

    # 拒绝未知域名的访问
    location / {
        return 444;
    }

    # 禁止访问隐藏文件
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
"""
            default_conf_path = "/etc/nginx/conf.d/default.conf"
            async with aiofiles.open(default_conf_path, 'w') as f:
                await f.write(default_conf)

            # 设置默认配置文件权限
            await run_command(f"chown {nginx_user} {default_conf_path}")
            await run_command(f"chmod 644 {default_conf_path}")

            # 测试配置
            await run_command("nginx -t")

            # 重启Nginx以应用新配置
            await run_command("systemctl restart nginx")
            await run_command("sleep 2")  # 等待服务启动

            logger.info("Nginx配置初始化完成")

        except Exception as e:
            logger.error(f"初始化Nginx配置失败: {str(e)}")
            raise

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建站点配置"""
        try:
            # 初始化Nginx配置
            await self._init_nginx_config()
            
            # 获取正确的Nginx用户
            nginx_user = await self._ensure_nginx_user()
            
            # 确保站点目录存在并设置权限
            site_root = f"/var/www/{site.domain}"
            os.makedirs(site_root, exist_ok=True)
            await run_command(f"chown -R {nginx_user} {site_root}")
            await run_command(f"chmod -R 755 {site_root}")
            
            # 生成配置文件
            config_content = generate_nginx_config(site)
            config_path = f"/etc/nginx/conf.d/{site.domain}.conf"
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 设置配置文件权限
            await run_command(f"chown {nginx_user} {config_path}")
            await run_command(f"chmod 644 {config_path}")
            
            # 测试配置
            try:
                await run_command("nginx -t")
            except Exception as e:
                logger.error(f"Nginx配置测试失败: {str(e)}")
                if os.path.exists(config_path):
                    os.remove(config_path)
                raise
            
            # 重启Nginx
            await self.restart_nginx()
            
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
            # 先停止Nginx服务
            await run_command("systemctl stop nginx")
            logger.info("Nginx服务已停止")

            # 删除所有相关文件和目录
            paths_to_delete = [
                # Nginx配置文件
                f"/etc/nginx/sites-available/{domain}.conf",
                f"/etc/nginx/sites-enabled/{domain}.conf",
                f"/etc/nginx/conf.d/{domain}.conf",
                # 站点目录
                f"/var/www/{domain}",
                # 日志文件
                f"/var/log/nginx/{domain}.access.log",
                f"/var/log/nginx/{domain}.error.log"
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
                "/var/tmp/nginx"
            ]

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    await run_command(f"rm -rf {cache_dir}/*")
                    logger.info(f"清理缓存目录: {cache_dir}")
                    # 重新创建目录
                    os.makedirs(cache_dir, exist_ok=True)

            # 重新启动Nginx
            await run_command("systemctl start nginx")
            await run_command("sleep 2")  # 等待服务启动
            
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