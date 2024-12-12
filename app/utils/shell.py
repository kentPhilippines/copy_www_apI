import asyncio
from typing import Optional
from app.core.logger import setup_logger

logger = setup_logger(__name__)

async def run_command(
    command: str,
    check: bool = True,
    timeout: int = 60
) -> str:
    """
    异步执行shell命令
    
    Args:
        command: 要执行的命令
        check: 是否检查返回值
        timeout: 超时时间(秒)
    
    Returns:
        命令输出
    """
    try:
        logger.debug(f"执行命令: {command}")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            if process.returncode is None:
                process.kill()
            raise TimeoutError(f"命令执行超时: {command}")
            
        if check and process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(f"命令执行失败: {error_msg}")
            
        return stdout.decode().strip()
        
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}")
        raise 