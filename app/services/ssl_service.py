from typing import Optional, Dict, Any
from app.utils.shell import run_command
from app.core.logger import setup_logger
import os

logger = setup_logger(__name__)

class SSLService:
    """SSL证书服务"""

    async def create_certificate(self, domain: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        申请SSL证书
        
        Args:
            domain: 域名
            email: 邮箱地址（可选）
        """
        try:
            # 确保验证目录存在
            webroot_path = f"/var/www/{domain}"
            os.makedirs(f"{webroot_path}/.well-known/acme-challenge", exist_ok=True)
            
            # 设置正确的权限
            await run_command(f"chmod -R 755 {webroot_path}/.well-known")
            await run_command(f"chown -R nginx:nginx {webroot_path}/.well-known")

            # 准备certbot命令
            cmd_parts = [
                "certbot certonly",
                "--webroot",
                f"-w {webroot_path}",  # 使用站点自己的目录
                f"-d {domain}",
                "--non-interactive",
                "--agree-tos",
                "--preferred-challenges http-01"
            ]

            # 添加邮箱或使用--register-unsafely-without-email
            if email:
                cmd_parts.append(f"--email {email}")
            else:
                cmd_parts.append("--register-unsafely-without-email")

            # 执行命令
            cmd = " ".join(cmd_parts)
            logger.info(f"执行certbot命令: {cmd}")
            
            await run_command(cmd)

            # 验证证书文件是否存在
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
            
            if not (os.path.exists(cert_path) and os.path.exists(key_path)):
                raise Exception("证书文件未创建")

            return {
                "success": True,
                "domain": domain,
                "cert_path": cert_path,
                "key_path": key_path
            }
            
        except Exception as e:
            logger.error(f"SSL证书申请失败: {str(e)}")
            raise

    async def delete_certificate(self, domain: str) -> Dict[str, Any]:
        """删除SSL证书"""
        try:
            await run_command(f"certbot delete --cert-name {domain} -n")
            return {
                "success": True,
                "message": f"证书 {domain} 已删除"
            }
        except Exception as e:
            logger.error(f"SSL证书删除失败: {str(e)}")
            raise

    async def verify_domain(self, domain: str) -> bool:
         
        """验证域名DNS是否已解析"""
        try:
            result = await run_command(f"dig +short {domain}")
            return bool(result.strip())
        except:
            return False