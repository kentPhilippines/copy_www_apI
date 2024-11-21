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
            cmd = ["certbot", "certonly", "--nginx"]
            
            # 添加域名
            cmd.extend(["-d", domain])
            
            # 添加邮箱（如果提供）
            if email:
                cmd.extend(["--email", email])
            else:
                cmd.append("--register-unsafely-without-email")
            
            # 自动同意服务条款
            cmd.append("--agree-tos")
            
            # 非交互模式
            cmd.append("-n")
            
            # 执行命令
            await run_command(" ".join(cmd))
            
            # 检查证书是否成功创建
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

    async def renew_certificate(self, domain: str) -> Dict[str, Any]:
        """续期SSL证书"""
        try:
            await run_command(f"certbot renew --cert-name {domain} --force-renewal -n")
            return {
                "success": True,
                "message": f"证书 {domain} 已续期"
            }
        except Exception as e:
            logger.error(f"SSL证书续期失败: {str(e)}")
            raise 