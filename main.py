from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import nginx, ssl, deploy, websocket_manager
from app.core.init_db import initialize_database
from app.core.config import settings
from routers import websocket
from monitor.run import start_monitor_service
import threading
import logging

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
app.include_router(websocket.router)
app.include_router(websocket_manager.router, prefix=f"{settings.API_V1_STR}/ws", tags=["WebSocket"])

@app.on_event("startup")
async def startup_event():
    """启动时执行"""
    try:
        await initialize_database()
        # 在新线程中启动监控服务
        monitor_thread = threading.Thread(
            target=start_monitor_service,
            daemon=True
        )
        monitor_thread.start()
    except Exception as e:
        logging.error(f"启动事件异常: {str(e)}")
        raise

@app.get("/")
async def root():
    return {
        "message": "Nginx Deploy API is running",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 