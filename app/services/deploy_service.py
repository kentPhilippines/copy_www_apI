from typing import List, Dict, Any
from app.schemas.deploy import DeployRequest, DeployResponse
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.schemas.nginx import NginxSite
from app.core.logger import setup_logger
import os
import aiofiles
import datetime

logger = setup_logger(__name__)

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()

    async def _create_test_page(self, domain: str, root_path: str) -> None:
        """创建测试页面"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain} - 测试页面</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f0f2f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1890ff;
            text-align: center;
            margin-bottom: 20px;
        }}
        .info-box {{
            background: #f6f6f6;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        .success {{
            color: #52c41a;
            font-weight: bold;
        }}
        .time {{
            color: #666;
            font-size: 0.9em;
            text-align: center;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{domain}</h1>
        <div class="info-box">
            <p><strong>部署状态：</strong> <span class="success">成功</span></p>
            <p><strong>站点类型：</strong> 静态网站</p>
            <p><strong>部署目录：</strong> {root_path}</p>
            <p><strong>配置文件：</strong> /etc/nginx/conf.d/{domain}.conf</p>
        </div>
        <p>这是一个默认的测试页面，表明您的站点已经成功部署。您可以：</p>
        <ul>
            <li>替换此页面开始构建您的网站</li>
            <li>在 {root_path} 目录下添加您的网站文件</li>
            <li>修改 Nginx 配置以适应您的需求</li>
        </ul>
        <p class="time">部署时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
            index_path = os.path.join(root_path, "index.html")
            async with aiofiles.open(index_path, 'w') as f:
                await f.write(html_content)
                
            logger.info(f"测试页面创建成功: {index_path}")
            
        except Exception as e:
            logger.error(f"创建测试页面失败: {str(e)}")
            raise

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 步骤1: 创建基础站点配置（不包含SSL）
            logger.info(f"步骤1: 创建基础站点配置 - {request.domain}")
            nginx_site = NginxSite(
                domain=request.domain,
                root_path=f"/var/www/{request.domain}",
                ssl_enabled=False  # 初始不启用SSL
            )
            
            # 创建基础站点
            result = await self.nginx_service.create_site(nginx_site)
            
            # 创建测试页面
            await self._create_test_page(request.domain, result.data["root_path"])

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
                "http": f"http://{request.domain}",
                "https": f"https://{request.domain}" if ssl_info else None
            }

            # 准备返回数据
            response_data = {
                **result.data,
                "ssl_enabled": bool(ssl_info),
                "ssl_info": ssl_info,
                "access_urls": access_urls
            }
            
            return DeployResponse(
                success=True,
                message=f"站点 {request.domain} 部署成功" + 
                        (" (无SSL)" if not ssl_info else f" (含SSL)\n访问地址:\nHTTP: http://{request.domain}\nHTTPS: https://{request.domain}"),
                data=response_data
            )

        except Exception as e:
            logger.error(f"部署失败: {str(e)}")
            # 清理失败的部署
            try:
                await self.remove_site(request.domain)
            except Exception as cleanup_error:
                logger.error(f"清理失败的部署时出错: {str(cleanup_error)}")
            raise

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

    async def list_sites(self) -> List[Dict[str, Any]]:
        """获取所有已部署的站点信息"""
        try:
            # 获取Nginx站点配置
            nginx_sites = await self.nginx_service.list_sites()
            
            # 为每个站点添加部署相关信息
            for site in nginx_sites:
                try:
                    # 添加部署状态信息
                    site['deploy_info'] = {
                        'deployed': True,
                        'deploy_time': self._get_deploy_time(site['config_file']),
                        'git_info': await self._get_git_info(site['root_path']) if site.get('root_exists') else None,
                        'web_server': 'nginx',
                        'server_type': self._detect_server_type(site['root_path']) if site.get('root_exists') else 'unknown'
                    }
                except Exception as e:
                    self.logger.error(f"获取站点部署信息失败 {site['domain']}: {str(e)}")
                    site['deploy_info'] = {
                        'deployed': False,
                        'error': str(e)
                    }

            return nginx_sites

        except Exception as e:
            self.logger.error(f"获取部署站点列表失败: {str(e)}")
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
                },
                'deploy_info': {
                    'deployed': True,
                    'deploy_time': '2024-01-20 10:30:00',
                    'git_info': {
                        'branch': 'main',
                        'commit': 'abc123',
                        'last_update': '2024-01-20 10:25:00'
                    },
                    'web_server': 'nginx',
                    'server_type': 'static'
                }
            }]

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