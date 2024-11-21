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

    def add_root(self, path: str):
        self.config_parts.append(f"    root {path};")
        return self

    def add_index(self, *files):
        self.config_parts.append(f"    index {' '.join(files)};")
        return self

    def add_ssl_config(self, cert_path: str, key_path: str):
        self.config_parts.extend([
            f"    ssl_certificate {cert_path};",
            f"    ssl_certificate_key {key_path};",
            "    ssl_protocols TLSv1.2 TLSv1.3;",
            "    ssl_ciphers HIGH:!aNULL:!MD5;"
        ])
        return self

    def add_php_config(self):
        self.config_parts.extend([
            "    location ~ \\.php$ {",
            "        include fastcgi_params;",
            "        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;",
            "        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;",
            "        fastcgi_param PATH_INFO $fastcgi_path_info;",
            "    }"
        ])
        return self

    def add_location(self, path: str, config: Dict[str, str]):
        self.config_parts.append(f"    location {path} {{")
        for key, value in config.items():
            self.config_parts.append(f"        {key} {value};")
        self.config_parts.append("    }")
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
        
        # HTTP配置
        builder.add_server() \
            .add_listen(80) \
            .add_server_name(site.domain)

        # 添加基本配置
        builder.config_parts.extend([
            f"    root {site.root_path};",
            "    index index.html index.htm index.php;",
            "    charset utf-8;",
            "",
            f"    access_log /var/log/nginx/{site.domain}.access.log main;",
            f"    error_log /var/log/nginx/{site.domain}.error.log;",
            "",
            "    # 基本设置",
            "    client_max_body_size 100m;",
            "    client_body_buffer_size 128k;",
            "    client_header_buffer_size 1k;",
            "",
            "    # 安全设置",
            "    add_header X-Frame-Options SAMEORIGIN;",
            "    add_header X-Content-Type-Options nosniff;",
            "    add_header X-XSS-Protection \"1; mode=block\";",
            "",
            "    # 主目录配置",
            "    location / {",
            "        try_files $uri $uri/ /index.html;",
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
            "",
            "    # 静态文件缓存",
            "    location ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {",
            "        expires 30d;",
            "        add_header Cache-Control \"public, no-transform\";",
            "    }",
            ""
        ])

        if site.php_enabled:
            builder.config_parts.extend([
                "    # PHP配置",
                "    location ~ \\.php$ {",
                "        fastcgi_split_path_info ^(.+\\.php)(/.+)$;",
                "        fastcgi_pass unix:/var/run/php-fpm/php-fpm.sock;",
                "        fastcgi_index index.php;",
                "        include fastcgi_params;",
                "        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;",
                "        fastcgi_param PATH_INFO $fastcgi_path_info;",
                "        fastcgi_intercept_errors on;",
                "        fastcgi_buffer_size 128k;",
                "        fastcgi_buffers 4 256k;",
                "        fastcgi_busy_buffers_size 256k;",
                "    }",
                ""
            ])

        builder.end_server()

        # HTTPS配置
        if site.ssl_enabled and site.ssl_certificate and site.ssl_certificate_key:
            builder.add_server() \
                .add_listen(443, ssl=True) \
                .add_server_name(site.domain)

            # SSL配置
            builder.config_parts.extend([
                f"    root {site.root_path};",
                "    index index.html index.htm index.php;",
                "    charset utf-8;",
                "",
                "    # SSL配置",
                f"    ssl_certificate {site.ssl_certificate};",
                f"    ssl_certificate_key {site.ssl_certificate_key};",
                "    ssl_protocols TLSv1.2 TLSv1.3;",
                "    ssl_ciphers HIGH:!aNULL:!MD5;",
                "    ssl_prefer_server_ciphers on;",
                "    ssl_session_cache shared:SSL:10m;",
                "    ssl_session_timeout 10m;",
                "",
                "    location / {",
                "        try_files $uri $uri/ /index.html =404;",
                "    }",
                ""
            ])

            if site.php_enabled:
                builder.config_parts.extend([
                    "    location ~ \\.php$ {",
                    "        fastcgi_split_path_info ^(.+\\.php)(/.+)$;",
                    "        fastcgi_pass unix:/var/run/php-fpm/php-fpm.sock;",
                    "        fastcgi_index index.php;",
                    "        include fastcgi_params;",
                    "        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;",
                    "        fastcgi_param PATH_INFO $fastcgi_path_info;",
                    "        fastcgi_param HTTPS on;",
                    "    }",
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