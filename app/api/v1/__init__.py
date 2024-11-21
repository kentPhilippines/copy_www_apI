from fastapi import APIRouter
from app.api.v1.endpoints import member, crawler, addon, system

api_router = APIRouter()

# 注册路由
api_router.include_router(member.router, prefix="/members", tags=["会员管理"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["采集管理"])
api_router.include_router(addon.router, prefix="/addons", tags=["插件管理"])
api_router.include_router(system.router, prefix="/system", tags=["系统管理"]) 