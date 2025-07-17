from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List
import asyncio
import wave
import numpy as np
from ..realtime_asr.realtime_handler import RealtimeASRHandler
from ..auth_service import decode_access_token
from ..models import User
from ..database import get_db

router = APIRouter()

# 存储所有活跃的WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

async def get_current_user(token: str):
    """从令牌中获取当前用户"""
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.websocket("/ws/asr/transcribe/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str
):
    # 验证用户
    try:
        user = await get_current_user(token)
    except Exception as e:
        await websocket.close(code=4001, reason="认证失败")
        return

    await manager.connect(websocket)
    asr_handler = RealtimeASRHandler()
    
    # 发送连接成功消息
    await websocket.send_json({
        "type": "connection_established",
        "user_id": str(user.id)
    })
    
    # 发送准备就绪消息
    await websocket.send_json({
        "type": "ready"
    })
    
    try:
        while True:
            # 接收二进制音频数据
            audio_data = await websocket.receive_bytes()
            
            try:
                # 处理音频数据
                result = await asr_handler.process_audio(audio_data)
                
                if result:
                    # 发送识别结果回客户端
                    await websocket.send_json({
                        "type": "transcription_result",
                        "data": {
                            "text": result,
                            "segments": [{
                                "confidence": 0.9  # 示例置信度
                            }],
                            "confidence_boost": 1.0,
                            "hotwords_detected": []  # 可以在这里添加热词检测逻辑
                        }
                    })
            except Exception as e:
                # 发送错误消息给客户端
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await asr_handler.cleanup() 