import websockets
import asyncio
import json

async def connect_websocket():
    uri = "ws://localhost:8000/ws/client123"
    async with websockets.connect(uri) as websocket:
        # 发送注册消息
        register_message = {
            "type": "register",
            "client_info": {
                "name": "test_client",
                "version": "1.0"
            }
        }
        await websocket.send(json.dumps(register_message))
        
        # 接收服务器响应
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # 发送心跳
        while True:
            try:
                heartbeat = {
                    "type": "heartbeat"
                }
                await websocket.send(json.dumps(heartbeat))
                response = await websocket.recv()
                print(f"Heartbeat response: {response}")
                await asyncio.sleep(30)  # 30秒发送一次心跳
            except Exception as e:
                print(f"Error: {str(e)}")
                break

asyncio.get_event_loop().run_until_complete(connect_websocket()) 