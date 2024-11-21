from typing import Dict, Optional
import re
from app.core.config import settings
from app.core.logger import setup_logger
from app.core.exceptions import NginxError

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

def generate_nginx_config(
    domain: str,
    root_path: str,
    php_enabled: bool = False,
    ssl_enabled: bool = False,
    ssl_cert: Optional[str] = None,
    ssl_key: Optional[str] = None
) -> str:
    """生成Nginx配置"""
    try:
        builder = NginxConfigBuilder()
        
        # HTTP配置
        builder.add_server() \
            .add_listen(80) \
            .add_server_name(domain) \
            .add_root(root_path) \
            .add_index("index.html", "index.htm", "index.php" if php_enabled else "")

        if php_enabled:
            builder.add_php_config()

        # 基础location配置
        builder.add_location("/", {
            "try_files": "$uri $uri/ /index.php?$query_string" if php_enabled else "$uri $uri/ =404"
        })

        builder.end_server()

        # HTTPS配置
        if ssl_enabled and ssl_cert and ssl_key:
            builder.add_server() \
                .add_listen(443, ssl=True) \
                .add_server_name(domain) \
                .add_root(root_path) \
                .add_index("index.html", "index.htm", "index.php" if php_enabled else "") \
                .add_ssl_config(ssl_cert, ssl_key)

            if php_enabled:
                builder.add_php_config()

            builder.add_location("/", {
                "try_files": "$uri $uri/ /index.php?$query_string" if php_enabled else "$uri $uri/ =404"
            })

            builder.end_server()

        return builder.build()

    except Exception as e:
        logger.error(f"Failed to generate nginx config: {str(e)}")
        raise NginxError(f"Failed to generate nginx config: {str(e)}")

def validate_domain(domain: str) -> bool:
    """验证域名格式"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain)) 