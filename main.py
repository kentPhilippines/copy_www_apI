from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import nginx, ssl, deploy
from app.core.init_db import init_db
import asyncio

app = FastAPI(
    title="Nginx Deploy API",
    description="API for managing Nginx deployments and SSL certificates",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(nginx.router, prefix="/api/v1/nginx", tags=["Nginx管理"])
app.include_router(ssl.router, prefix="/api/v1/ssl", tags=["SSL证书管理"])
app.include_router(deploy.router, prefix="/api/v1/deploy", tags=["站点部署"])

@app.on_event("startup")
async def startup_event():
    # 初始化数据库
    await init_db()

@app.get("/")
async def root():
    return {
        "message": "Nginx Deploy API is running",
        "docs_url": "/docs"
    } 