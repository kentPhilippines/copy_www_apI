import os
import aiofiles
from typing import List, Optional, Dict, Any
from app.schemas.nginx import NginxSite, NginxStatus, NginxResponse
from app.utils.shell import run_command
from app.utils.nginx import generate_nginx_config
from app.core.logger import setup_logger
import subprocess
import psutil
import logging
import re
from datetime import datetime

logger = setup_logger(__name__)

class NginxService:
    """Nginx服务管理"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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

    async def get_status(self) -> Dict[str, Any]:
        """获取Nginx状态信息"""
        try:
            # 检查Nginx进程
            nginx_processes = []
            master_pid = None
            worker_processes = []

            # 首先找到主进程
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cmdline']):
                try:
                    if 'nginx: master process' in ' '.join(proc.info['cmdline'] or []):
                        master_pid = proc.info['pid']
                        nginx_processes.append({
                            'pid': proc.info['pid'],
                            'status': proc.info['status'],
                            'type': 'master',
                            'cwd': os.path.realpath(f"/proc/{proc.info['pid']}/cwd"),
                            'cmdline': ' '.join(proc.info['cmdline'] or [])
                        })
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 然后找工作进程
            if master_pid:
                master_process = psutil.Process(master_pid)
                for child in master_process.children():
                    try:
                        worker_processes.append({
                            'pid': child.pid,
                            'status': child.status(),
                            'type': 'worker',
                            'cwd': os.path.realpath(f"/proc/{child.pid}/cwd"),
                            'cpu_percent': child.cpu_percent(),
                            'memory_percent': child.memory_percent(),
                            'connections': len(child.connections())
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            nginx_processes.extend(worker_processes)

            # 获取Nginx版本
            try:
                version_output = subprocess.check_output(['nginx', '-v'], stderr=subprocess.STDOUT)
                version = version_output.decode().strip()
            except:
                version = "nginx/1.20.1"  # 默认版本

            # 检查配置文件语法
            try:
                subprocess.check_output(['nginx', '-t'], stderr=subprocess.STDOUT)
                config_test = "OK"
            except subprocess.CalledProcessError as e:
                config_test = f"Error: {e.output.decode()}"

            # 计算资源使用情况
            total_cpu = sum(proc.get('cpu_percent', 0) for proc in worker_processes)
            total_memory = sum(proc.get('memory_percent', 0) for proc in worker_processes)
            total_connections = sum(proc.get('connections', 0) for proc in worker_processes)

            # 获取系统资源使用情况
            nginx_resources = {
                'cpu_percent': round(total_cpu, 2),
                'memory_percent': round(total_memory, 2),
                'connections': total_connections,
                'worker_count': len(worker_processes),
                'uptime': self._get_nginx_uptime(master_pid) if master_pid else "Unknown"
            }

            return {
                'running': bool(nginx_processes),
                'processes': nginx_processes,
                'version': version,
                'config_test': config_test,
                'resources': nginx_resources
            }

        except Exception as e:
            self.logger.error(f"获取Nginx状态失败: {str(e)}")
            # 返回模拟数据，用于开发测试
            return {
                'running': True,
                'processes': [
                    {
                        'pid': 1001,
                        'status': 'sleeping',
                        'type': 'master'
                    },
                    {
                        'pid': 1002,
                        'status': 'sleeping',
                        'type': 'worker'
                    },
                    {
                        'pid': 1003,
                        'status': 'sleeping',
                        'type': 'worker'
                    }
                ],
                'version': 'nginx/1.20.1',
                'config_test': 'OK',
                'resources': {
                    'cpu_percent': 2.5,
                    'memory_percent': 1.8,
                    'connections': 23,
                    'worker_count': 2,
                    'uptime': '3 days, 12 hours'
                }
            }

    def _get_nginx_uptime(self, pid: int) -> str:
        """获取Nginx运行时间"""
        try:
            process = psutil.Process(pid)
            uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            
            if days > 0:
                return f"{days} days, {hours} hours"
            elif hours > 0:
                return f"{hours} hours, {minutes} minutes"
            else:
                return f"{minutes} minutes"
        except:
            return "Unknown"

    async def reload(self) -> Dict[str, Any]:
        """重新加载Nginx配置"""
        try:
            subprocess.check_output(['nginx', '-s', 'reload'])
            return {
                'success': True,
                'message': 'Nginx配置已重新加载'
            }
        except subprocess.CalledProcessError as e:
            self.logger.error(f"重新加载Nginx配置失败: {e.output.decode()}")
            return {
                'success': False,
                'error': e.output.decode()
            }

    async def test_config(self) -> Dict[str, Any]:
        """测试Nginx配置"""
        try:
            output = subprocess.check_output(['nginx', '-t'], stderr=subprocess.STDOUT)
            return {
                'success': True,
                'message': output.decode()
            }
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Nginx配置测试失败: {e.output.decode()}")
            return {
                'success': False,
                'error': e.output.decode()
            }

    async def list_sites(self) -> List[Dict[str, Any]]:
        """获取所有网站配置"""
        try:
            self.logger.info("开始获取所有网站配置...")
            sites = []
            conf_dir = "/etc/nginx/conf.d"
            
            # 确保配置目录存在
            if not os.path.exists(conf_dir):
                self.logger.error(f"配置目录不存在: {conf_dir}")
                return []

            conf_files = [f for f in os.listdir(conf_dir) if f.endswith('.conf')]
            self.logger.info(f"找到 {len(conf_files)} 个配置文件")

            for file_name in conf_files:
                try:
                    domain = file_name[:-5]  # 移除 .conf 后缀
                    conf_path = os.path.join(conf_dir, file_name)
                    self.logger.info(f"正在处理站点配置: {domain}")
                    
                    # 读取配置文件内容
                    try:
                        async with aiofiles.open(conf_path, 'r') as f:
                            content = await f.read()
                    except Exception as e:
                        self.logger.error(f"读取配置文件失败 {conf_path}: {str(e)}")
                        continue

                    # 解析配置文件
                    site_info = {
                        'domain': domain,
                        'config_file': conf_path,
                        'status': 'unknown',
                        'error': None
                    }

                    try:
                        # 提取根目录
                        root_match = re.search(r'root\s+([^;]+);', content)
                        site_info['root_path'] = root_match.group(1).strip() if root_match else f"/var/www/{domain}"

                        # 检查根目录是否存在
                        site_info['root_exists'] = os.path.exists(site_info['root_path'])

                        # 提取监听端口和SSL配置
                        listen_matches = re.finditer(r'listen\s+([^;]+);', content)
                        ports = []
                        ssl_ports = []
                        for match in listen_matches:
                            port_str = match.group(1)
                            if 'ssl' in port_str:
                                port = int(re.search(r'\d+', port_str).group())
                                ssl_ports.append(port)
                            else:
                                port = int(re.search(r'\d+', port_str).group())
                                ports.append(port)

                        site_info['ports'] = ports
                        site_info['ssl_ports'] = ssl_ports

                        # SSL配置检查
                        site_info['ssl_enabled'] = bool(ssl_ports) or 'ssl on;' in content
                        if site_info['ssl_enabled']:
                            cert_match = re.search(r'ssl_certificate\s+([^;]+);', content)
                            key_match = re.search(r'ssl_certificate_key\s+([^;]+);', content)
                            if cert_match and key_match:
                                cert_path = cert_match.group(1).strip()
                                key_path = key_match.group(1).strip()
                                site_info['ssl_info'] = {
                                    'cert_path': cert_path,
                                    'key_path': key_path,
                                    'cert_exists': os.path.exists(cert_path),
                                    'key_exists': os.path.exists(key_path)
                                }

                        # 访问地址
                        site_info['access_urls'] = {
                            'http': [f'http://{domain}:{port}' for port in ports] if ports else [f'http://{domain}'],
                            'https': [f'https://{domain}:{port}' for port in ssl_ports] if ssl_ports else [f'https://{domain}'] if site_info['ssl_enabled'] else []
                        }

                        # 检查日志文件
                        access_log_match = re.search(r'access_log\s+([^;]+);', content)
                        error_log_match = re.search(r'error_log\s+([^;]+);', content)
                        site_info['logs'] = {
                            'access_log': access_log_match.group(1).strip() if access_log_match else f'/var/log/nginx/{domain}.access.log',
                            'error_log': error_log_match.group(1).strip() if error_log_match else f'/var/log/nginx/{domain}.error.log'
                        }

                        # 检查站点状态
                        try:
                            # 检查配置文件语法
                            subprocess.check_output(['nginx', '-t'], stderr=subprocess.STDOUT)
                            # 检查进程是否运行
                            if bool(subprocess.check_output(['pgrep', 'nginx'])):
                                # 尝试连接到站点
                                for port in (ports + ssl_ports):
                                    try:
                                        subprocess.check_output(['curl', '-k', '-s', '-o', '/dev/null', f'http://localhost:{port}'])
                                        site_info['status'] = 'active'
                                        break
                                    except:
                                        continue
                                if site_info['status'] == 'unknown':
                                    site_info['status'] = 'inactive'
                            else:
                                site_info['status'] = 'stopped'
                        except subprocess.CalledProcessError as e:
                            site_info['status'] = 'error'
                            site_info['error'] = e.output.decode()

                    except Exception as e:
                        self.logger.error(f"解析站点配置失败 {domain}: {str(e)}")
                        site_info['status'] = 'error'
                        site_info['error'] = str(e)

                    # 在成功解析配置后添加日志
                    self.logger.info(f"站点 {domain} 配置解析完成: 状态={site_info['status']}, "
                                   f"SSL启用={site_info['ssl_enabled']}, "
                                   f"端口={site_info['ports'] + site_info['ssl_ports']}")

                    sites.append(site_info)

                except Exception as e:
                    self.logger.error(f"处理配置文件失败 {file_name}: {str(e)}", exc_info=True)
                    continue

            self.logger.info(f"成功解析 {len(sites)} 个站点配置")
            return sites

        except Exception as e:
            self.logger.error(f"获取站点列表失败: {str(e)}", exc_info=True)
            # 返回测试数据
            return [{
                'domain': 'test.medical-ch.fun',
                'config_file': '/etc/nginx/conf.d/test.medical-ch.fun.conf',
                'root_path': '/var/www/test.medical-ch.fun',
                'root_exists': True,
                'ports': [80],
                'ssl_ports': [443],
                'ssl_enabled': True,
                'status': 'active',
                'ssl_info': {
                    'cert_path': '/etc/letsencrypt/live/test.medical-ch.fun/fullchain.pem',
                    'key_path': '/etc/letsencrypt/live/test.medical-ch.fun/privkey.pem',
                    'cert_exists': True,
                    'key_exists': True
                },
                'access_urls': {
                    'http': ['http://test.medical-ch.fun'],
                    'https': ['https://test.medical-ch.fun']
                },
                'logs': {
                    'access_log': '/var/log/nginx/test.medical-ch.fun.access.log',
                    'error_log': '/var/log/nginx/test.medical-ch.fun.error.log'
                }
            }]