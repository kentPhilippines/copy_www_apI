from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import logging
import json
from datetime import datetime

router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger("websocket")

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                self.logger.error(f"Error sending message to {client_id}: {str(e)}")
                await self.disconnect(client_id)

manager = WebSocketManager()

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
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理接收到的消息
                await manager.send_message(client_id, {
                    "type": "message_received",
                    "data": message,
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