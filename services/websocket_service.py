from fastapi import WebSocket
from typing import Dict, List
import logging
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        # 存储所有连接的客户端
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger("websocket_manager")

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message: {str(e)}") 