import os
import aiofiles
from typing import Dict, Any, Optional
from app.schemas.nginx import NginxSite, NginxResponse, SSLInfo
from app.utils.shell import run_command
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class NginxService:
    """Nginx服务管理"""

    async def create_site(self, site: NginxSite) -> NginxResponse:
        """创建站点配置"""
        try:
            # 检查SSL配置
            if site.ssl_enabled and site.ssl_info is None:
                return NginxResponse(
                    success=False,
                    message="启用SSL但未提供证书信息"
                )
            
            # 确保站点目录存在
            site_root = f"/var/www/{site.domain}"
            os.makedirs(site_root, exist_ok=True)
            await run_command(f"chown -R nginx:nginx {site_root}")
            await run_command(f"chmod -R 755 {site_root}")
            
            # 生成配置文件
            config_content = self._generate_site_config(site)
            config_path = f"/etc/nginx/conf.d/{site.domain}.conf"
            
            # 写入配置文件
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(config_content)
            
            # 设置配置文件权限
            await run_command(f"chown nginx:nginx {config_path}")
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

    def _generate_site_config(self, site: NginxSite) -> str:
        """生成站点配置"""
        config = ""
        
        # HTTP配置(用于SSL验证或重定向)
        http_config = """
server {
    listen 80;
    listen [::]:80;
    server_name %s;
    
    # Let's Encrypt验证目录
    location /.well-known/acme-challenge/ {
        root %s;
        allow all;
    }
    
    # 如果启用了SSL，其他请求重定向到HTTPS
    %s
}
""" % (
            site.domain,
            site.root_path,
            "return 301 https://$server_name$request_uri;" if site.ssl_enabled else ""
        )
        
        config += http_config

        # 如果启用了SSL，添加HTTPS配置
        if site.ssl_enabled and site.ssl_info:
            https_config = """
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name %s;

    # SSL配置
    ssl_certificate %s;
    ssl_certificate_key %s;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # 反向代理配置
    location / {
        proxy_pass http://127.0.0.1:%d;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 添加自定义配置
    %s
}
""" % (
                site.domain,
                site.ssl_info.cert_path,
                site.ssl_info.key_path,
                site.proxy_port,
                site.custom_config if site.custom_config else ''
            )
            config += https_config

        return config

    async def restart_nginx(self):
        """重启Nginx服务"""
        try:
            await run_command("systemctl restart nginx")
            await run_command("sleep 2")  # 等待服务启动
            logger.info("Nginx服务重启成功")
        except Exception as e:
            logger.error(f"Nginx服务重启失败: {str(e)}")
            raise