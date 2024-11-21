from typing import Dict, Optional
import re
import os
from app.core.config import settings
from app.core.logger import setup_logger
from app.core.exceptions import NginxError
from app.schemas.nginx import NginxSite, NginxConfig
from app.utils.shell import run_command
 


logger = setup_logger("nginx_utils")

class NginxConfigBuilder:
    """Nginx配置生成器"""
    
    def __init__(self):
        self.config_parts = []

    def add_server(self):
        self.config_parts.append("server {")
        return self

    def add_listen(self, port: int = 80, ssl: bool = False):
        self.config_parts.append(f"    listen {port}{' ssl' if ssl else ''};")
        return self

    def add_server_name(self, domain: str):
        self.config_parts.append(f"    server_name {domain};")
        return self

    def end_server(self):
        self.config_parts.append("}")
        return self

    def build(self) -> str:
        return "\n".join(self.config_parts)

def generate_nginx_config(site: NginxSite) -> str:
    """生成Nginx配置文件内容"""
    try:
        builder = NginxConfigBuilder()
        
        # 基础配置
        builder.add_server() \
            .add_listen(80) \
            .add_server_name(site.domain)

        builder.config_parts.extend([
            f"    root /var/www/{site.domain};",
            "    index index.html index.htm;",
            "",
            f"    access_log /var/log/nginx/{site.domain}.access.log main;",
            f"    error_log /var/log/nginx/{site.domain}.error.log;",
            "",
            "    # Let's Encrypt 验证配置",
            "    location ^~ /.well-known/acme-challenge/ {",
            f"        root /var/www/{site.domain};",  # 使用站点自己的目录
            "        try_files $uri =404;",
            "        allow all;",
            "    }",
            "",
            "    location / {",
            "        try_files $uri $uri/ /index.html;",
            "    }",
            "",
            "    # 静态文件缓存",
            "    location ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {",
            "        expires 30d;",
            "        add_header Cache-Control \"public, no-transform\";",
            "    }",
            "",
            "    # 禁止访问隐藏文件",
            "    location ~ /\\. {",
            "        deny all;",
            "        access_log off;",
            "        log_not_found off;",
            "    }",
            ""
        ])

        # 检查SSL证书是否存在
        cert_path = f"/etc/letsencrypt/live/{site.domain}/fullchain.pem"
        key_path = f"/etc/letsencrypt/live/{site.domain}/privkey.pem"
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            # 只有在证书文件存在时才添加SSL配置
            builder.config_parts.extend([
                "    # SSL配置",
                f"    ssl_certificate {cert_path};",
                f"    ssl_certificate_key {key_path};",
                "    ssl_session_timeout 1d;",
                "    ssl_session_cache shared:SSL:50m;",
                "    ssl_session_tickets off;",
                "",
                "    # SSL协议和加密套件",
                "    ssl_protocols TLSv1.2 TLSv1.3;",
                "    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;",
                "    ssl_prefer_server_ciphers off;",
                "",
                "    # HSTS配置",
                "    add_header Strict-Transport-Security \"max-age=63072000\" always;",
                "",
                "    # OCSP Stapling",
                "    ssl_stapling on;",
                "    ssl_stapling_verify on;",
                "    resolver 8.8.8.8 8.8.4.4 valid=300s;",
                "    resolver_timeout 5s;",
                ""
            ])

        builder.end_server()

        return builder.build()

    except Exception as e:
        logger.error(f"生成Nginx配置失败: {str(e)}")
        raise

def validate_domain(domain: str) -> bool:
    """验证域名格式"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def get_nginx_config_path(domain: str) -> str:
    """获取Nginx配置文件路径"""
    return os.path.join(settings.NGINX_SITES_PATH, f"{domain}.conf")

def get_nginx_enabled_path(domain: str) -> str:
    """获取Nginx启用配置文件路径"""
    return os.path.join(settings.NGINX_ENABLED_PATH, f"{domain}.conf")

def create_nginx_directories():
    """创建Nginx必要目录"""
    os.makedirs(settings.NGINX_SITES_PATH, exist_ok=True)
    os.makedirs(settings.NGINX_ENABLED_PATH, exist_ok=True)
    os.makedirs(settings.WWW_ROOT, exist_ok=True)

def get_site_root_path(domain: str) -> str:
    """获取站点根目录路径"""
    return os.path.join(settings.WWW_ROOT, domain)

async def get_nginx_user() -> str:
    """获取Nginx运行用户"""
    try:
        # 尝试从nginx配置中获取用户
        result = await run_command("nginx -T 2>/dev/null | grep 'user' | head -n1")
        if result and 'user' in result:
            user = result.split()[1].strip(';')
            return user
        
        # 如果无法从配置获取，检查进程
        result = await run_command("ps aux | grep 'nginx: master' | grep -v grep | awk '{print $1}' | head -n1")
        if result:
            return result.strip()
        
        # 根据系统类型返回默认用户
        if os.path.exists('/etc/redhat-release'):
            return 'nginx:nginx'  # CentOS/RHEL
        else:
            return 'www-data:www-data'  # Debian/Ubuntu
    except:
        # 如果都失败了，返回系统相关的默认值
        if os.path.exists('/etc/redhat-release'):
            return 'nginx:nginx'
        return 'www-data:www-data' 