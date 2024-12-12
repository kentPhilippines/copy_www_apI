import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import deploy, ssl
from app.core.config import settings
from app.utils.shell import run_command
from app.core.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Nginx Deploy API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(
    deploy.router, 
    prefix=f"{settings.API_V1_STR}/deploy", 
    tags=["站点部署"]
)
app.include_router(
    ssl.router, 
    prefix=f"{settings.API_V1_STR}/ssl", 
    tags=["SSL证书"]
)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 确保必要目录存在
    os.makedirs(settings.NGINX_CONF_DIR, exist_ok=True)
    os.makedirs(settings.WWW_ROOT, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Nginx Deploy API is running",
        "docs_url": "/docs"
    }

async def auto_update():
    """自动更新代码"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 先获取远程更新信息
        await run_command(f"cd {current_dir} && git fetch")
        # 检查是否有更新
        result = await run_command(f"cd {current_dir} && git status -uno")
        if "Your branch is behind" in result:
            # 有更新时执行拉取
            await run_command(f"cd {current_dir} && git pull")
            logger.info("代码已更新到最新版本")
            # 重启服务
            await run_command("systemctl restart nginx-deploy")
        else:
            logger.info("当前代码已是最新版本")
    except Exception as e:
        logger.error(f"代码更新失败: {str(e)}")

# 定时执行自动更新
async def schedule_updates():
    """定时执行更新检查"""
    while True:
        await auto_update()
        await asyncio.sleep(300)  # 每5分钟检查一次

if __name__ == "__main__":
    import uvicorn
    # 启动自动更新任务
    asyncio.create_task(schedule_updates())
    # 启动API服务
    uvicorn.run(app, host="0.0.0.0", port=8000) 

 



#这里需要一个自动更新代码的脚本
async def auto_update():
    # 1. 拉取最新代码 在当前项目的根目录执行 git pull
    # 获取当前项目的根目录  
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 执行 git pull
    await run_command(f"cd {current_dir} && git pull")
    # 打印日志
    logger.info("已拉取最新代码")
    pass