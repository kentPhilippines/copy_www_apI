from app.schemas.nginx import NginxSite

def generate_nginx_config(site: NginxSite) -> str:
    """生成Nginx配置文件内容"""
    return f"""
server {{
    listen 80;
    server_name {site.domain};
    root {site.root_path};
    index index.html index.htm index.php;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \.php$ {{
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }}
}}
""" 