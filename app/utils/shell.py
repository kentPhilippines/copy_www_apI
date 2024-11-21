import asyncio
from typing import Optional

async def run_command(command: str) -> str:
    """执行shell命令"""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"Command failed: {stderr.decode()}")
        
    return stdout.decode() 