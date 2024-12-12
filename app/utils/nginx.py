from typing import Optional
import os
from app.core.config import settings
from app.core.logger import setup_logger
from app.core.exceptions import NginxError
from app.utils.shell import run_command

logger = setup_logger(__name__)

async def verify_nginx_config() -> bool:
    """验证Nginx配置"""
    try:
        await run_command("nginx -t")
        return True
    except Exception as e:
        logger.error(f"Nginx配置验证失败: {str(e)}")
        return False

async def get_nginx_user() -> str:
    """获取Nginx运行用户"""
    try:
        result = await run_command("ps aux | grep 'nginx: master' | grep -v grep | awk '{print $1}' | head -n1")
        if result:
            return result.strip()
        return 'nginx'
    except:
        return 'nginx'

def ensure_nginx_dirs():
    """确保Nginx必要目录存在"""
    os.makedirs(settings.NGINX_CONF_DIR, exist_ok=True)
    os.makedirs(settings.WWW_ROOT, exist_ok=True) 