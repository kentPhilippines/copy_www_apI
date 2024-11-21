from typing import List
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
            # 创建基础的Nginx站点
            nginx_site = NginxSite(
                domain=request.domain,
                root_path=f"/var/www/{request.domain}",
                ssl_enabled=request.enable_ssl
            )
            
            # 创建站点
            result = await self.nginx_service.create_site(nginx_site)
            
            # 创建测试页面
            await self._create_test_page(request.domain, result.data["root_path"])

            # 如果需要SSL，配置证书
            ssl_info = None
            if request.enable_ssl:
                try:
                    # 先检查域名DNS解析
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
                            # 更新Nginx配置以使用SSL
                            nginx_site.ssl_certificate = ssl_result["cert_path"]
                            nginx_site.ssl_certificate_key = ssl_result["key_path"]
                            
                            # 重新生成配置并重载Nginx
                            await self.nginx_service.create_site(nginx_site)
                    else:
                        logger.warning(f"域名 {request.domain} DNS未解析，跳过SSL配置")
                except Exception as e:
                    logger.error(f"SSL证书配置失败: {str(e)}")

            # 准备返回数据
            response_data = {
                **result.data,
                "ssl_enabled": request.enable_ssl,
                "ssl_info": ssl_info
            }
            
            return DeployResponse(
                success=True,
                message=f"站点 {request.domain} 部署成功",
                data=response_data
            )

        except Exception as e:
            logger.error(f"部署失败: {str(e)}")
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
            result = await self.nginx_service.delete_site(domain)
            
            return DeployResponse(
                success=True,
                message=f"站点 {domain} 已移除"
            )
        except Exception as e:
            logger.error(f"移除站点失败: {str(e)}")
            raise 