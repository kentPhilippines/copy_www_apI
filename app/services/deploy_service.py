import os
import aiofiles
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.deploy import DeployRequest, DeployResponse, SiteUpdateRequest, SiteBackupInfo, SiteListResponse,MirrorRequest,MirrorResponse
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.schemas.nginx import NginxSite, NginxSiteInfo, SSLInfo, LogPaths, AccessUrls, DeployInfo
from app.core.logger import setup_logger
from app.core.config import settings
from bs4 import BeautifulSoup
import shutil
import subprocess
import requests
import json
from urllib.parse import urljoin, urlparse

logger = setup_logger(__name__)

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()
        self.logger = logger

    async def get_site_info(self, domain: str) -> Optional[NginxSiteInfo]:
        """获取单个站点的详细信息"""
        try:
            sites = await self.list_sites()
            for site in sites.sites:
                if site.domain == domain:
                    return site
            return None
        except Exception as e:
            self.logger.error(f"获取站点信息失败 {domain}: {str(e)}")
            return None

    async def update_site(self, domain: str, updates: SiteUpdateRequest) -> DeployResponse:
        """更新站点配置"""
        try:
            site_info = await self.get_site_info(domain)
            if not site_info:
                raise ValueError(f"站点不存在: {domain}")

            # 备份原配置
            backup_path = f"{site_info.config_file}.bak"
            shutil.copy2(site_info.config_file, backup_path)

            try:
                # 更新配置
                if updates.ssl_enabled is not None and updates.ssl_enabled != site_info.ssl_enabled:
                    if updates.ssl_enabled:
                        # 启用SSL
                        ssl_result = await self.ssl_service.create_certificate(domain=domain)
                        if ssl_result.success:
                            site_info.ssl_info = SSLInfo(**ssl_result.data)
                    else:
                        # 禁用SSL
                        await self.ssl_service.delete_certificate(domain)
                        site_info.ssl_info = None

                # 更新其他配置
                if updates.root_path:
                    site_info.root_path = updates.root_path
                
                # 重新生成配置文件
                nginx_site = NginxSite(
                    domain=domain,
                    root_path=site_info.root_path,
                    ssl_enabled=site_info.ssl_enabled,
                    ssl_info=site_info.ssl_info
                )
                await self.nginx_service.create_site(nginx_site)

                # 测试配置
                test_result = await self.nginx_service.test_config()
                if not test_result.success:
                    raise ValueError(test_result.message)

                # 重载Nginx
                reload_result = await self.nginx_service.reload()
                if not reload_result.success:
                    raise ValueError(reload_result.message)

                # 删除备份
                os.remove(backup_path)

                return DeployResponse(
                    success=True,
                    message=f"站点 {domain} 更新成功",
                    data=site_info.dict()
                )

            except Exception as e:
                # 发生错误时恢复备份
                if os.path.exists(backup_path):
                    shutil.move(backup_path, site_info.config_file)
                raise

        except Exception as e:
            self.logger.error(f"更新站点失败 {domain}: {str(e)}")
            return DeployResponse(
                success=False,
                message=str(e)
            )

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 步骤1: 创建基础站点配置（不包含SSL）
            logger.info(f"步骤1: 创建基础站点配置 - {request.domain}")
            
            # 创建站点目录
            site_root = f"/var/www/{request.domain}"
            os.makedirs(site_root, exist_ok=True)

            # 创建测试页面
            if request.deploy_type == 'static':
                await self._create_static_page(site_root, request.domain)
            elif request.deploy_type == 'php':
                await self._create_php_page(site_root, request.domain)
            elif request.deploy_type == 'node':
                await self._create_node_page(site_root, request.domain)
            else:
                await self._create_static_page(site_root, request.domain)  # 默认创建静态页面

            # 设置目录权限
            os.system(f"chown -R nginx:nginx {site_root}")
            os.system(f"chmod -R 755 {site_root}")

            # 创建Nginx配置
            nginx_site = NginxSite(
                domain=request.domain,
                root_path=site_root,
                ssl_enabled=False  # 初始不启用SSL
            )
            
            # 创建基础站点
            result = await self.nginx_service.create_site(nginx_site)

            # 步骤2: 如果需要SSL，申请证书
            ssl_info = None
            if request.enable_ssl:
                logger.info(f"步骤2: 申请SSL证书 - {request.domain}")
                try:
                    # 检查域名DNS解析
                    if await self.ssl_service.verify_domain(request.domain):
                        ssl_result = await self.ssl_service.create_certificate(
                            domain=request.domain,
                            email=request.ssl_email
                        )
                        
                        if ssl_result.get("success"):
                            ssl_info = {
                                "cert_path": ssl_result["cert_path"],
                                "key_path": ssl_result["key_path"]
                            }
                            logger.info(f"SSL证书申请成功 - {request.domain}")

                            # 步骤3: 更新Nginx配置，添加SSL
                            logger.info(f"步骤3: 更新Nginx配置，添加SSL - {request.domain}")
                            nginx_site.ssl_enabled = True
                            nginx_site.ssl_certificate = ssl_result["cert_path"]
                            nginx_site.ssl_certificate_key = ssl_result["key_path"]
                            
                            # 重新生成配置并重载Nginx
                            await self.nginx_service.create_site(nginx_site)
                        else:
                            logger.warning(f"SSL证书申请失败 - {request.domain}")
                    else:
                        logger.warning(f"域名DNS未解析，跳过SSL配置 - {request.domain}")
                except Exception as e:
                    logger.error(f"SSL配置失败: {str(e)}")

            # 准备访问URL
            access_urls = {
                "http": [f"http://{request.domain}"],
                "https": [f"https://{request.domain}"] if ssl_info else []
            }

            return DeployResponse(
                success=True,
                message=f"站点 {request.domain} 部署成功",
                data={
                    "domain": request.domain,
                    "root_path": site_root,
                    "deploy_type": request.deploy_type,
                    "ssl_enabled": bool(ssl_info),
                    "ssl_info": ssl_info,
                    "access_urls": access_urls
                }
            )

        except Exception as e:
            logger.error(f"部署站点失败 {request.domain}: {str(e)}")
            return DeployResponse(
                success=False,
                message=str(e)
            )

    async def remove_site(self, domain: str) -> DeployResponse:
        """移除站点"""
        try:
            # 尝试删除SSL证书（如果存在）
            try:
                await self.ssl_service.delete_certificate(domain)
            except Exception as e:
                logger.warning(f"删除SSL证书失败: {str(e)}")

            # 删除站点配置和文件
            result = await self.nginx_service.delete_site(domain)
            
            return DeployResponse(
                success=True,
                message=f"站点 {domain} 已移除"
            )
        except Exception as e:
            logger.error(f"移除站点失败: {str(e)}")
            raise 

    async def list_sites(self) -> SiteListResponse:
        """获取所有已部署的站点信息"""
        try:
            nginx_sites = await self.nginx_service.list_sites()
            site_infos = []
            errors = []

            for site in nginx_sites:
                try:
                    site_info = NginxSiteInfo(
                        domain=site['domain'],
                        config_file=site['config_file'],
                        root_path=site['root_path'],
                        root_exists=site.get('root_exists', False),
                        ports=site.get('ports', [80]),
                        ssl_ports=site.get('ssl_ports', []),
                        ssl_enabled=site.get('ssl_enabled', False),
                        status=site.get('status', 'unknown'),
                        error=site.get('error'),
                        ssl_info=SSLInfo(**site['ssl_info']) if site.get('ssl_info') else None,
                        access_urls=AccessUrls(**site['access_urls']) if site.get('access_urls') else None,
                        logs=LogPaths(**site['logs']) if site.get('logs') else None,
                        deploy_info=DeployInfo(
                            deployed=True,
                            deploy_time=self._get_deploy_time(site['config_file']),
                            git_info=await self._get_git_info(site['root_path']) if site.get('root_exists') else None,
                            web_server='nginx',
                            server_type=self._detect_server_type(site['root_path']) if site.get('root_exists') else 'unknown'
                        )
                    )
                    site_infos.append(site_info)
                except Exception as e:
                    errors.append({
                        'domain': site['domain'],
                        'error': str(e)
                    })

            return SiteListResponse(
                total=len(site_infos),
                sites=site_infos,
                errors=errors if errors else None
            )

        except Exception as e:
            self.logger.error(f"获取站点列表失败: {str(e)}")
            return SiteListResponse(
                total=0,
                sites=[],
                errors=[{'domain': 'global', 'error': str(e)}]
            )

    def _get_deploy_time(self, config_file: str) -> str:
        """获取站点部署时间"""
        try:
            import os
            import datetime
            stat = os.stat(config_file)
            return datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return 'unknown'

    async def _get_git_info(self, root_path: str) -> Dict[str, str]:
        """获取Git仓库信息"""
        try:
            import subprocess
            git_dir = os.path.join(root_path, '.git')
            if not os.path.exists(git_dir):
                return None

            # 获取当前分支
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=root_path
            ).decode().strip()

            # 获取最后提交
            commit = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=root_path
            ).decode().strip()

            # 获取最后更新时间
            last_update = subprocess.check_output(
                ['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M:%S'],
                cwd=root_path
            ).decode().strip()

            return {
                'branch': branch,
                'commit': commit,
                'last_update': last_update
            }
        except:
            return None

    def _detect_server_type(self, root_path: str) -> str:
        """检测站点类型"""
        try:
            # 检查常见的项目标识文件
            if os.path.exists(os.path.join(root_path, 'package.json')):
                return 'node'
            elif os.path.exists(os.path.join(root_path, 'requirements.txt')):
                return 'python'
            elif os.path.exists(os.path.join(root_path, 'composer.json')):
                return 'php'
            elif os.path.exists(os.path.join(root_path, 'index.html')):
                return 'static'
            else:
                return 'unknown'
        except:
            return 'unknown'

    async def backup_site(self, domain: str) -> DeployResponse:
        """备份站点"""
        try:
            site_info = await self.get_site_info(domain)
            if not site_info:
                raise ValueError(f"站点不存在: {domain}")

            # 创建备份目录
            backup_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(settings.BACKUP_DIR, domain, backup_time)
            os.makedirs(backup_dir, exist_ok=True)

            files_included = []
            total_size = 0

            # 备份配置文件
            config_backup = os.path.join(backup_dir, os.path.basename(site_info.config_file))
            shutil.copy2(site_info.config_file, config_backup)
            files_included.append(config_backup)
            total_size += os.path.getsize(config_backup)

            # 备份网站文件
            if os.path.exists(site_info.root_path):
                www_backup = os.path.join(backup_dir, 'www')
                shutil.copytree(site_info.root_path, www_backup)
                files_included.append(www_backup)
                total_size += sum(os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, _, filenames in os.walk(www_backup)
                                for filename in filenames)

            # 创建备份信息
            backup_info = SiteBackupInfo(
                backup_path=backup_dir,
                backup_time=backup_time,
                site_info=site_info,
                files_included=files_included,
                size=total_size
            )

            return DeployResponse(
                success=True,
                message=f"站点 {domain} 备份成功",
                data=backup_info.dict()
            )

        except Exception as e:
            self.logger.error(f"备份站点失败 {domain}: {str(e)}")
            return DeployResponse(
                success=False,
                message=str(e)
            )



    async def _create_static_page(self, site_root: str, domain: str):
        """创建静态测试页面"""
        index_path = os.path.join(site_root, 'index.html')
        with open(index_path, 'w') as f:
            f.write(f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain} - 站点信息</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 40px 20px;
            background: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .info-section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .info-section h2 {{
            color: #007bff;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .info-item {{
            padding: 15px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .info-item strong {{
            display: block;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .info-item span {{
            color: #666;
            word-break: break-all;
        }}
        .status {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            background: #28a745;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }}
        .path {{
            font-family: monospace;
            padding: 8px;
            background: #f1f3f5;
            border-radius: 4px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{domain}</h1>
        
        <div class="info-section">
            <h2>基础信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>部署状态</strong>
                    <span class="status">已部署</span>
                </div>
                <div class="info-item">
                    <strong>部署时间</strong>
                    <span>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <div class="info-item">
                    <strong>站点类型</strong>
                    <span>静态网站</span>
                </div>
            </div>
        </div>

        <div class="info-section">
            <h2>路径配置</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>站点根目录</strong>
                    <div class="path">{site_root}</div>
                </div>
                <div class="info-item">
                    <strong>配置文件</strong>
                    <div class="path">/etc/nginx/conf.d/{domain}.conf</div>
                </div>
                <div class="info-item">
                    <strong>访问日志</strong>
                    <div class="path">/var/log/nginx/{domain}.access.log</div>
                </div>
                <div class="info-item">
                    <strong>错误日志</strong>
                    <div class="path">/var/log/nginx/{domain}.error.log</div>
                </div>
            </div>
        </div>

        <div class="info-section">
            <h2>服务器信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Web服务器</strong>
                    <span>Nginx</span>
                </div>
                <div class="info-item">
                    <strong>操作系统</strong>
                    <span>Linux</span>
                </div>
                <div class="info-item">
                    <strong>服务器时间</strong>
                    <span>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>此页面由 Nginx Manager 自动生成</p>
            <p>部署时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """)

    async def _create_php_page(self, site_root: str, domain: str):
        """创建PHP测试页面"""
        index_path = os.path.join(site_root, 'index.php')
        with open(index_path, 'w') as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {domain}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px auto;
            max-width: 800px;
            padding: 20px;
            text-align: center;
        }}
        h1 {{
            color: #333;
        }}
        .info {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>Welcome to {domain}</h1>
    <div class="info">
        <p>This is a PHP test page.</p>
        <p>Site root: <?php echo "{site_root}"; ?></p>
        <p>Server time: <?php echo date('Y-m-d H:i:s'); ?></p>
        <p>PHP version: <?php echo phpversion(); ?></p>
    </div>
</body>
</html>
            """)

    async def _create_node_page(self, site_root: str, domain: str):
        """创建Node.js测试页面"""
        # 创建package.json
        package_json = {
            "name": domain.replace(".", "-"),
            "version": "1.0.0",
            "description": f"Test site for {domain}",
            "main": "index.js",
            "scripts": {
                "start": "node index.js"
            },
            "dependencies": {
                "express": "^4.17.1"
            }
        }
        
        with open(os.path.join(site_root, 'package.json'), 'w') as f:
            json.dump(package_json, f, indent=2)

        # 创建index.js
        with open(os.path.join(site_root, 'index.js'), 'w') as f:
            f.write(f"""
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {{
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome to {domain}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px auto;
                    max-width: 800px;
                    padding: 20px;
                    text-align: center;
                }}
                h1 {{
                    color: #333;
                }}
                .info {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Welcome to {domain}</h1>
            <div class="info">
                <p>This is a Node.js test page.</p>
                <p>Site root: {site_root}</p>
                <p>Server time: ${{new Date().toLocaleString()}}</p>
                <p>Node.js version: ${{process.version}}</p>
            </div>
        </body>
        </html>
    `);
}});

app.listen(port, () => {{
    console.log(`Server running at http://localhost:${{port}}`);
}});
            """)

        # 安装依赖
        os.system(f"cd {site_root} && npm install")
    
    async def mirror_site(self, request: MirrorRequest):
        """镜像站点"""
        try:
            # 1. 检查源站点是否存在
            source_site = await self.get_site_info(request.domain)
            if not source_site:
                raise ValueError(status_code=404, detail=f"站点 {request.domain} 不存在")
            
            # 2. 检查源站点路径
            source_path = request.path
            if not os.path.exists(source_path):
                raise ValueError(status_code=404, detail=f"站点 {request.domain} 路径 {source_path} 不存在")
            dest_folder = source_path
            # 3. 检查目标站点是否存在 获取目标站点信息 http请求
            target_url = f"http://{request.target_domain}"
            response = requests.get(target_url)
            if response.status_code != 200:
                raise ValueError(status_code=404, detail=f"站点 {request.target_domain} 不存在")
            # 获取目标站点的每一个内容
            response = requests.get(target_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            #替换目标站点tdk
            if request.tdk:
                soup = self._replace_tdk(soup, request.tdk_rules)
            #生成蜘蛛地图
            if request.sitemap:
                self._generate_sitemap(target_url, os.path.join(dest_folder, 'sitemap.xml'))
            # 保存目标站点的HTML内容
            html_filename = os.path.join(dest_folder, 'index.html')
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            # 下载所有资源 包括link script img
            for tag in soup.find_all(['link', 'script', 'img']):
                resource_url = tag.get('href') or tag.get('src')
                if resource_url:
                    full_url = urljoin(target_url, resource_url)
                    await self.download_file(full_url, dest_folder)
            return  MirrorResponse(
                success=True,
                message="站点镜像成功"
            )
        except Exception as e:
            return MirrorResponse(
                success=False,
                message=str(e)
            )
    async def download_file(self, url, output_dir):
        try:
            response = requests.get(url)
            response.raise_for_status()
            parsed_url = urlparse(url)
            path = parsed_url.path.strip("/") or "index.html"
            save_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"Saved: {save_path}")
            return save_path
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    
    def _replace_tdk(self, soup: BeautifulSoup, tdk_rules: Dict[str, str]):
        """替换目标站点的tdk"""
        for key, value in tdk_rules.items():
            soup.replace(key, value)
        return soup
    
    def _generate_sitemap(self, base_url, output_file):    
        visited_urls = set()
        urls_to_visit = {base_url}

        while urls_to_visit:
            current_url = urls_to_visit.pop()
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            new_links = self._get_all_links(current_url, base_url)
            urls_to_visit.update(new_links - visited_urls)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in visited_urls:
                f.write(f'  <url>\n')
                f.write(f'    <loc>{url}</loc>\n')
                f.write(f'  </url>\n')
            f.write('</urlset>\n')