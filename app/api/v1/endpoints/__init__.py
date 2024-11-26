from fastapi import APIRouter
from . import nginx, ssl, deploy, websocket_manager  # 添加 websocket_manager

router = APIRouter() 