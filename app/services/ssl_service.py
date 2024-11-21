import os
from datetime import datetime
from typing import List
from app.schemas.ssl import SSLCertRequest, SSLCertInfo, SSLResponse
from app.utils.shell import run_command

class SSLService:
    CERTBOT_PATH = "/etc/letsencrypt/live"

    async def create_certificate(self, request: SSLCertRequest) -> SSLResponse:
        """申请SSL证书"""
        try:
            # 使用certbot申请证书
            cmd = f"certbot --nginx -d {request.domain}"
            if request.email:
                cmd += f" --email {request.email}"
            if request.staging:
                cmd += " --staging"
            if request.force_renewal:
                cmd += " --force-renewal"
            
            await run_command(cmd)
            
            return SSLResponse(
                success=True,
                message=f"SSL certificate for {request.domain} created successfully"
            )
        except Exception as e:
            raise Exception(f"Failed to create SSL certificate: {str(e)}")

    async def list_certificates(self) -> List[SSLCertInfo]:
        """获取所有证书信息"""
        certs = []
        try:
            # 获取所有证书目录
            for domain in os.listdir(self.CERTBOT_PATH):
                cert_path = os.path.join(self.CERTBOT_PATH, domain)
                if os.path.isdir(cert_path):
                    # 获取证书信息
                    cert_info = await self._get_cert_info(domain)
                    if cert_info:
                        certs.append(cert_info)
            return certs
        except Exception as e:
            raise Exception(f"Failed to list certificates: {str(e)}")

    async def delete_certificate(self, domain: str) -> SSLResponse:
        """删除证书"""
        try:
            await run_command(f"certbot delete --cert-name {domain}")
            return SSLResponse(
                success=True,
                message=f"SSL certificate for {domain} deleted successfully"
            )
        except Exception as e:
            raise Exception(f"Failed to delete certificate: {str(e)}")

    async def renew_certificate(self, domain: str) -> SSLResponse:
        """续期证书"""
        try:
            await run_command(f"certbot renew --cert-name {domain} --force-renewal")
            return SSLResponse(
                success=True,
                message=f"SSL certificate for {domain} renewed successfully"
            )
        except Exception as e:
            raise Exception(f"Failed to renew certificate: {str(e)}")

    async def _get_cert_info(self, domain: str) -> SSLCertInfo:
        """获取证书详细信息"""
        try:
            cert_path = os.path.join(self.CERTBOT_PATH, domain, "cert.pem")
            if not os.path.exists(cert_path):
                return None

            # 使用OpenSSL获取证书信息
            cmd = f"openssl x509 -in {cert_path} -noout -text"
            cert_text = await run_command(cmd)

            # 解析证书信息
            # 这里需要实现证书信息解析逻辑
            return SSLCertInfo(
                domain=domain,
                issuer="Let's Encrypt",
                valid_from=datetime.now(),  # 需要从证书中解析
                valid_to=datetime.now(),    # 需要从证书中解析
                is_valid=True
            )
        except Exception:
            return None 