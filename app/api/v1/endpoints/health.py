from fastapi import APIRouter
from app.schemas.health import HealthCheck
from app.utils.shell import run_command
import psutil

router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """系统健康检查"""
    try:
        # 检查Nginx状态
        nginx_status = await run_command("systemctl is-active nginx")
        nginx_running = nginx_status.strip() == "active"
        
        # 获取系统信息
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return HealthCheck(
            status="healthy",
            nginx_running=nginx_running,
            system_info={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        )
    except Exception as e:
        return HealthCheck(
            status="unhealthy",
            error=str(e)
        ) 