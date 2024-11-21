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
        
        # HTTP配置
        builder.add_server() \
            .add_listen(80) \
            .add_server_name(site.domain)

        # 添加基本配置
        builder.config_parts.extend([
            f"    root /var/www/{site.domain};",
            "    index index.html index.htm;",
            "",
            f"    access_log /var/log/nginx/{site.domain}.access.log main;",
            f"    error_log /var/log/nginx/{site.domain}.error.log;",
            "",
            "    # 主目录配置",
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