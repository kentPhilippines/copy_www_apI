from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging
import json
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # 存储所有连接的客户端 {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储客户端信息 {client_id: client_info}
        self.client_info: Dict[str, dict] = {}
        self.logger = logging.getLogger("websocket_manager")

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            if client_id in self.client_info:
                del self.client_info[client_id]
            self.logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                self.logger.error(f"Error sending message to {client_id}: {str(e)}")
                await self.disconnect(client_id)

    async def broadcast(self, message: dict, exclude: str = None):
        for client_id in list(self.active_connections.keys()):
            if client_id != exclude:
                await self.send_message(client_id, message)

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await manager.connect(client_id, websocket)
        
        # 发送连接成功消息
        await manager.send_message(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                message_type = message.get("type", "")
                
                if message_type == "register":
                    # 存储客户端信息
                    manager.client_info[client_id] = message.get("client_info", {})
                    await manager.send_message(client_id, {
                        "type": "register_response",
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message_type == "heartbeat":
                    # 处理心跳消息
                    await manager.send_message(client_id, {
                        "type": "heartbeat_response",
                        "status": "alive",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message_type == "metrics":
                    # 处理监控数据
                    # 这里可以添加数据存储逻辑
                    await manager.send_message(client_id, {
                        "type": "metrics_received",
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    })
                
                else:
                    # 处理其他类型消息
                    await manager.send_message(client_id, {
                        "type": "message_received",
                        "status": "success",
                        "original_type": message_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logging.error(f"WebSocket error for client {client_id}: {str(e)}")
        await manager.disconnect(client_id) 