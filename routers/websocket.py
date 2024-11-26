from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.websocket_service import WebSocketManager
import json

router = APIRouter()
manager = WebSocketManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await manager.connect(client_id, websocket)
        
        # 发送连接成功消息
        await manager.send_message(client_id, {
            "type": "connection_established",
            "client_id": client_id
        })
        
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                if message.get("type") == "register":
                    # 处理注册消息
                    await handle_register(client_id, message)
                elif message.get("type") == "heartbeat":
                    # 处理心跳消息
                    await handle_heartbeat(client_id)
                else:
                    # 处理其他类型消息
                    await handle_message(client_id, message)
                    
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        await manager.disconnect(client_id)
        raise e

async def handle_register(client_id: str, message: dict):
    """处理注册消息"""
    # 这里可以添加注册逻辑，比如存储客户端信息到数据库
    await manager.send_message(client_id, {
        "type": "register_response",
        "status": "success",
        "message": "Registration successful"
    })

async def handle_heartbeat(client_id: str):
    """处理心跳消息"""
    await manager.send_message(client_id, {
        "type": "heartbeat_response",
        "status": "alive"
    })

async def handle_message(client_id: str, message: dict):
    """处理其他消息"""
    # 根据需要处理其他类型的消息
    await manager.send_message(client_id, {
        "type": "message_received",
        "message": message
    }) 