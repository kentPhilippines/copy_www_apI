from fastapi import APIRouter, HTTPException, Depends, WebSocket, Query, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from app.services.nginx_service import NginxService
from app.schemas.nginx import (
    NginxSite,
    NginxStatus,
    NginxResponse
)
from websockets.exceptions import ConnectionClosed

router = APIRouter()
nginx_service = NginxService()

@router.get("/status", response_model=NginxStatus)
async def get_nginx_status():
    """获取Nginx状态"""
    status = await nginx_service.get_status()
    return NginxStatus(**status)

@router.post("/sites", response_model=NginxResponse)
async def create_site(site: NginxSite):
    """创建新的网站配置"""
    try:
        return await nginx_service.create_site(site)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{domain}", response_model=NginxResponse)
async def delete_site(domain: str):
    """删除网站配置"""
    try:
        return await nginx_service.delete_site(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites", response_model=List[Dict[str, Any]])
async def list_sites():
    """获取所有网站配置"""
    return await nginx_service.list_sites()

@router.get("/reload", response_model=NginxResponse)
async def reload_nginx():
    """重新加载Nginx配置"""
    try:
        return await nginx_service.reload()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/restart", response_model=NginxResponse)
async def restart_nginx():
    """重启Nginx"""
    try:
        return await nginx_service.restart()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.websocket("/logs/ws/{log_type}")
async def websocket_logs(
    websocket: WebSocket,
    log_type: str,
    domain: Optional[str] = None
):
    """实时日志WebSocket接口"""
    try:
        await websocket.accept()
        
        # 验证日志类型
        if log_type not in ['access', 'error']:
            await websocket.send_text("无效的日志类型")
            await websocket.close()
            return

        await nginx_service.tail_log(websocket, log_type, domain)
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except ConnectionClosed:
        logger.info("WebSocket连接关闭")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        try:
            await websocket.send_text(f"错误: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.get("/logs/{log_type}", response_model=List[str])
async def get_logs(
    log_type: str,
    lines: int = Query(default=100, ge=1, le=10000),
    domain: Optional[str] = None
):
    """获取日志内容"""
    return await nginx_service.get_log_content(log_type, lines, domain)


@router.websocket("/nginx/ws")
async def websocket_nginx(websocket: WebSocket):
    """Nginx状态WebSocket接口"""
    try:
        await nginx_service.tail_nginx_status(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except ConnectionClosed:
        logger.info("WebSocket连接关闭")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        try:
            await websocket.send_text(f"错误: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
