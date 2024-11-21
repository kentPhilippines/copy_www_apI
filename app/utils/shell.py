import asyncio
import subprocess
from typing import Optional, Tuple, List, Any
from app.core.logger import setup_logger

logger = setup_logger("shell_utils")

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
        logger.debug(f"Executing command: {command}")
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
            process.kill()
            raise TimeoutError(f"Command timed out after {timeout} seconds: {command}")
            
        if check and process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(f"Command failed with exit code {process.returncode}: {error_msg}")
            
        return stdout.decode().strip()
        
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        raise

async def run_commands(commands: List[str]) -> List[str]:
    """
    异步执行多个shell命令
    
    Args:
        commands: 命令列表
    
    Returns:
        命令输出列表
    """
    results = []
    for cmd in commands:
        result = await run_command(cmd)
        results.append(result)
    return results

def run_command_sync(
    command: str,
    check: bool = True,
    timeout: int = 60
) -> Tuple[int, str, str]:
    """
    同步执行shell命令
    
    Args:
        command: 要执行的命令
        check: 是否检查返回值
        timeout: 超时时间(秒)
    
    Returns:
        (返回码, 标准输出, 标准错误)
    """
    try:
        logger.debug(f"Executing command synchronously: {command}")
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Command failed with exit code {result.returncode}: {result.stderr}"
            )
            
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out after {timeout} seconds: {command}")
    except Exception as e:
        logger.error(f"Synchronous command execution failed: {str(e)}")
        raise 