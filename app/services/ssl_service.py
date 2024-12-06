from typing import Optional, Dict, Any
from app.utils.shell import run_command
from app.core.logger import setup_logger
import os
import asyncio
import aiohttp
import socket

logger = setup_logger(__name__)

class SSLService:
    """SSL证书服务"""

    def __init__(self):
        self.logger = setup_logger(__name__)

    async def create_certificate(self, domain: str, email: str) -> Dict[str, Any]:
        """申请SSL证书"""
        try:
            # 检查域名DNS解析
            if not await self._check_dns(domain):
                return {
                    "success": False,
                    "message": f"域名 {domain} DNS未解析到当前服务器"
                }

            # 确保目录存在
            cert_dir = f"/etc/letsencrypt/live/{domain}"
            os.makedirs(cert_dir, exist_ok=True)

            # 构建certbot命令
            cmd = (
                f"certbot certonly --standalone "
                f"--non-interactive "
                f"--agree-tos "
                f"--email {email} "
                f"--domain {domain} "
                f"--preferred-challenges http "
                f"--http-01-port 80 "
                "--force-renewal "
                "--debug-challenges"
            )

            # 临时停止Nginx
            await run_command("systemctl stop nginx")
            self.logger.info("Nginx服务已停止，准备申请证书")

            try:
                # 执行certbot命令
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                # 记录详细日志
                if stdout:
                    self.logger.info(f"Certbot输出: {stdout.decode()}")
                if stderr:
                    self.logger.warning(f"Certbot错误: {stderr.decode()}")

                if process.returncode != 0:
                    raise Exception(f"Certbot命令执行失败: {stderr.decode()}")

                # 检查证书文件是否存在
                cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"

                if not (os.path.exists(cert_path) and os.path.exists(key_path)):
                    raise Exception("证书文件未生成")

                return {
                    "success": True,
                    "message": "SSL证书申请成功",
                    "cert_path": cert_path,
                    "key_path": key_path
                }

            finally:
                # 重���启动Nginx
                try:
                    await run_command("systemctl start nginx")
                    self.logger.info("Nginx服务已重新启动")
                except Exception as e:
                    self.logger.error(f"重启Nginx失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"SSL证书申请失败: {str(e)}")
            return {
                "success": False,
                "message": f"SSL证书申请失败: {str(e)}"
            }

    async def _check_dns(self, domain: str) -> bool:
        """检查域名DNS解析"""
        try:
            # 获取当前服务器IP
            server_ip = await self._get_server_ip()
            if not server_ip:
                self.logger.error("无法获取服务器IP")
                return False

            # 获取域名解析IP
            domain_ip = await self._get_domain_ip(domain)
            if not domain_ip:
                self.logger.error(f"无法获取域名 {domain} 的解析IP")
                return False

            # 比较IP
            return server_ip == domain_ip

        except Exception as e:
            self.logger.error(f"检查DNS解析失败: {str(e)}")
            return False

    async def _get_server_ip(self) -> Optional[str]:
        """获取服��器公网IP"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org') as response:
                    return await response.text()
        except Exception as e:
            self.logger.error(f"获取服务器IP失败: {str(e)}")
            return None

    async def _get_domain_ip(self, domain: str) -> Optional[str]:
        """获取域名解析IP"""
        try:
            return socket.gethostbyname(domain)
        except Exception as e:
            self.logger.error(f"获取域名IP失败: {str(e)}")
            return None

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