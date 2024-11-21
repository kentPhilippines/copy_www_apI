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
            # 首先检查域名是否已经有证书
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            if os.path.exists(cert_path):
                logger.info(f"域名 {domain} 已存在证书，尝试续期")
                return await self.renew_certificate(domain)

            # 准备certbot命令
            cmd_parts = [
                "certbot certonly",
                "--webroot",  # 使用webroot方式验证
                "-w /var/www/" + domain,  # 指定网站根目录
                "-d " + domain,  # 指定域名
                "--non-interactive",  # 非交互模式
                "--agree-tos",  # 同意服务条款
                "--preferred-challenges http-01",  # 使用HTTP验证
            ]

            # 添加邮箱或使用--register-unsafely-without-email
            if email:
                cmd_parts.append(f"--email {email}")
            else:
                cmd_parts.append("--register-unsafely-without-email")

            # 在测试环境中使用staging服务器
            if os.getenv("ENVIRONMENT") == "development":
                cmd_parts.append("--test-cert")

            # 执行命令
            cmd = " ".join(cmd_parts)
            logger.info(f"执行certbot命令: {cmd}")
            
            try:
                await run_command(cmd)
            except Exception as e:
                # 如果失败，尝试使用staging环境
                if "--test-cert" not in cmd:
                    logger.warning("正式环境申请失败，尝试使用测试证书")
                    cmd_parts.append("--test-cert")
                    cmd = " ".join(cmd_parts)
                    await run_command(cmd)

            # 验证证书文件是否存在
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
            
            if not (os.path.exists(cert_path) and os.path.exists(key_path)):
                raise Exception("证书文件未创建")

            # 获取证书信息
            cert_info = await run_command(f"openssl x509 -in {cert_path} -text -noout")
            
            return {
                "success": True,
                "domain": domain,
                "cert_path": cert_path,
                "key_path": key_path,
                "cert_info": cert_info
            }
            
        except Exception as e:
            logger.error(f"SSL证书申请失败: {str(e)}")
            # 返回错误信息而不是抛出异常，让部署继续进行
            return {
                "success": False,
                "domain": domain,
                "error": str(e)
            }

    async def verify_domain(self, domain: str) -> bool:
        """验证域名DNS是否已解析"""
        try:
            result = await run_command(f"dig +short {domain}")
            return bool(result.strip())
        except:
            return False

    async def check_cert_status(self, domain: str) -> Dict[str, Any]:
        """检查证书状态"""
        try:
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            if not os.path.exists(cert_path):
                return {"exists": False}

            # 获取证书信息
            cert_info = await run_command(f"openssl x509 -in {cert_path} -text -noout")
            expiry = await run_command(f"openssl x509 -in {cert_path} -enddate -noout")
            
            return {
                "exists": True,
                "cert_info": cert_info,
                "expiry": expiry
            }
        except Exception as e:
            logger.error(f"检查证书状态失败: {str(e)}")
            return {"exists": False, "error": str(e)}

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
            return {
                "success": False,
                "error": str(e)
            }

    async def renew_certificate(self, domain: str) -> Dict[str, Any]:
        """续期SSL证书"""
        try:
            await run_command(f"certbot renew --cert-name {domain} --force-renewal -n")
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
            
            return {
                "success": True,
                "domain": domain,
                "cert_path": cert_path,
                "key_path": key_path,
                "message": f"证书 {domain} 已续期"
            }
        except Exception as e:
            logger.error(f"SSL证书续期失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }