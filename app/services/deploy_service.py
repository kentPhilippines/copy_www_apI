import os
import shutil
from typing import List, Dict
from app.schemas.deploy import DeployRequest, DeployStatus, DeployResponse, SiteInfo
from app.services.nginx_service import NginxService
from app.services.ssl_service import SSLService
from app.utils.shell import run_command
from app.core.logger import setup_logger
from app.schemas.nginx import NginxSite
from app.core.config import settings
import aiofiles
import datetime
from app.utils.nginx import get_nginx_user

logger = setup_logger(__name__)

class DeployService:
    """部署服务实现"""
    
    def __init__(self):
        self.nginx_service = NginxService()
        self.ssl_service = SSLService()

    async def _create_test_page(self, domain: str, root_path: str, deploy_type: str):
        """创建测试页面"""
        try:
            os.makedirs(root_path, exist_ok=True)
            
            # 获取正确的Nginx用户
            nginx_user = await get_nginx_user()
            
            # 设置正确的目录权限
            await run_command(f"chown -R {nginx_user} {root_path}")
            await run_command(f"chmod -R 755 {root_path}")
            
            if deploy_type == "static":
                # 创建静态HTML测试页面
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
            <p><strong>配置文件：</strong> /etc/nginx/sites-available/{domain}.conf</p>
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
                async with aiofiles.open(index_path, "w") as f:
                    await f.write(html_content)
                
                # 设置文件权限
                await run_command(f"chown {nginx_user} {index_path}")
                await run_command(f"chmod 644 {index_path}")
                
            else:  # PHP
                # 创建PHP测试页面
                php_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain} - PHP测试页面</title>
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
        .php-info {{
            margin-top: 20px;
            padding: 15px;
            background: #e6f7ff;
            border-radius: 4px;
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
        <h1><?php echo '{domain}'; ?></h1>
        <div class="info-box">
            <p><strong>部署状态：</strong> <span class="success">成功</span></p>
            <p><strong>站点类型：</strong> PHP网站</p>
            <p><strong>部署目录：</strong> <?php echo '{root_path}'; ?></p>
            <p><strong>PHP版本：</strong> <?php echo phpversion(); ?></p>
        </div>
        <div class="php-info">
            <h3>PHP环境信息：</h3>
            <?php
                echo '<pre>';
                echo 'PHP版本: ' . phpversion() . "\\n";
                echo 'Web服务器: ' . $_SERVER['SERVER_SOFTWARE'] . "\\n";
                echo 'MySQL支持: ' . (extension_loaded('mysql') ? '是' : '否') . "\\n";
                echo 'PDO支持: ' . (extension_loaded('pdo') ? '是' : '否') . "\\n";
                echo 'GD支持: ' . (extension_loaded('gd') ? '是' : '否') . "\\n";
                echo '</pre>';
            ?>
        </div>
        <p class="time">部署时间：<?php echo date('Y-m-d H:i:s'); ?></p>
    </div>
</body>
</html>
"""
                index_path = os.path.join(root_path, "index.php")
                async with aiofiles.open(index_path, "w") as f:
                    await f.write(php_content)
                
                # 设置文件权限
                await run_command(f"chown {nginx_user} {index_path}")
                await run_command(f"chmod 644 {index_path}")
            
            logger.info(f"测试页面创建成功: {index_path}")
            
        except Exception as e:
            logger.error(f"创建测试页面失败: {str(e)}")
            raise

    async def deploy_site(self, request: DeployRequest) -> DeployResponse:
        """部署新站点"""
        try:
            # 准备路径
            root_path = f"/var/www/{request.domain}"
            config_path = f"/etc/nginx/sites-available/{request.domain}.conf"
            enabled_path = f"/etc/nginx/sites-enabled/{request.domain}.conf"
            
            # 创建NginxSite对象
            nginx_site = NginxSite(
                domain=request.domain,
                root_path=root_path,
                php_enabled=request.deploy_type == "php",
                ssl_enabled=request.enable_ssl
            )
            
            # 创建站点
            await self.nginx_service.create_site(nginx_site)
            
            # 创建测试页面
            await self._create_test_page(request.domain, root_path, request.deploy_type)

            # 准备测试URL
            test_urls = {
                "http": f"http://{request.domain}",
                "https": f"https://{request.domain}" if request.enable_ssl else None
            }

            # 如果需要SSL，配置证书
            ssl_info = None
            if request.enable_ssl:
                try:
                    ssl_result = await self.ssl_service.create_certificate(
                        domain=request.domain,
                        email=request.ssl_email
                    )
                    if ssl_result.get("success"):
                        ssl_info = {
                            "cert_path": ssl_result["cert_path"],
                            "key_path": ssl_result["key_path"]
                        }
                        
                        # 更新Nginx配置以使用SSL
                        nginx_site.ssl_enabled = True
                        nginx_site.ssl_certificate = ssl_result["cert_path"]
                        nginx_site.ssl_certificate_key = ssl_result["key_path"]
                        
                        # 重新生成配置并重载Nginx
                        await self.nginx_service.create_site(nginx_site)
                        
                except Exception as e:
                    logger.error(f"SSL证��配置失败: {str(e)}")
                    # 继续部署，但不启用SSL

            # 准备返回信息
            deployment_info = {
                "domain": request.domain,
                "deploy_type": request.deploy_type,
                "paths": {
                    "root_directory": root_path,
                    "nginx_config": config_path,
                    "nginx_enabled": enabled_path
                },
                "urls": test_urls,
                "ssl": ssl_info
            }

            # 在所有操作完成后，确保重启Nginx
            try:
                await self.nginx_service.restart_nginx()
            except Exception as e:
                logger.error(f"Nginx重启失败: {str(e)}")
                # 继续返回结果，但记录错误

            return DeployResponse(
                success=True,
                message=f"站点 {request.domain} 部署成功",
                data=deployment_info
            )

        except Exception as e:
            logger.error(f"部署失败: {str(e)}")
            # 清理失败的部署
            await self._cleanup_failed_deploy(request.domain)
            raise

    async def _cleanup_failed_deploy(self, domain: str):
        """清理失败的部署"""
        try:
            await self.nginx_service.delete_site(domain)
        except Exception as e:
            logger.error(f"清理失败的部署时出错: {str(e)}")

    async def list_sites(self) -> List[SiteInfo]:
        """获取所有已部署的站点"""
        try:
            nginx_sites = await self.nginx_service.list_sites()
            sites = []
            for site in nginx_sites:
                status = await self.get_site_status(site.domain)
                sites.append(SiteInfo(
                    domain=site.domain,
                    deploy_type="php" if site.php_enabled else "static",
                    path=site.root_path,
                    status=status
                ))
            return sites
        except Exception as e:
            logger.error(f"获取站点列表失败: {str(e)}")
            raise

    async def get_site_status(self, domain: str) -> DeployStatus:
        """获取站点状态"""
        try:
            nginx_config_exists = os.path.exists(f"/etc/nginx/sites-enabled/{domain}.conf")
            ssl_exists = os.path.exists(f"/etc/letsencrypt/live/{domain}/fullchain.pem")
            
            # 检查站点是否可访问
            is_accessible = False
            try:
                await run_command(f"curl -sI http://{domain}")
                is_accessible = True
            except:
                pass

            return DeployStatus(
                nginx_configured=nginx_config_exists,
                ssl_configured=ssl_exists,
                is_accessible=is_accessible
            )
        except Exception as e:
            logger.error(f"获取站点状态失败: {str(e)}")
            raise

    async def remove_site(self, domain: str) -> DeployResponse:
        """移除站点"""
        try:
            # 先删除SSL证书（如果存在）
            try:
                await self.ssl_service.delete_certificate(domain)
            except Exception as e:
                logger.warning(f"删除SSL证书失败: {str(e)}")

            # 删除站点配置和文件
            await self.nginx_service.delete_site(domain)
            
            # 确保Nginx重启
            try:
                await self.nginx_service.restart_nginx()
            except Exception as e:
                logger.error(f"Nginx重启失败: {str(e)}")

            return DeployResponse(
                success=True,
                message=f"站点 {domain} 已完全移除"
            )
        except Exception as e:
            logger.error(f"移除站点失败: {str(e)}")
            raise 