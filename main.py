import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import nginx, ssl, deploy ,sites
from app.core.init_db import initialize_database
from app.core.config import settings
from app.utils.shell import run_command

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
app.include_router(nginx.router, prefix=f"{settings.API_V1_STR}/nginx", tags=["Nginx管理"])
app.include_router(ssl.router, prefix=f"{settings.API_V1_STR}/ssl", tags=["SSL证书管理"])
app.include_router(deploy.router, prefix=f"{settings.API_V1_STR}/deploy", tags=["站点部署"])
app.include_router(sites.router, prefix=f"{settings.API_V1_STR}/sites", tags=["站点管理"])

@app.on_event("startup")
async def startup_event():
    """启动时执行"""
    await initialize_database()

@app.get("/")
async def root():
    return {
        "message": "Nginx Deploy API is running",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # 定时执行更新代码 定时配置 2秒执行一次
    async def auto_update():
        while True:
            await asyncio.sleep(2)
            await auto_update()
    uvicorn.run(app, host="0.0.0.0", port=9999) 

 



#这里需要一个自动更新代码的脚本
async def auto_update():
    # 1. 拉取最新代码 在当前项目的根目录执行 git pull
    # 获取当前项目的根目录  
    current_dir = os.path.dirname(os.path.abspath(__file__))
    await run_command(f"cd {current_dir} && git pull")
    pass