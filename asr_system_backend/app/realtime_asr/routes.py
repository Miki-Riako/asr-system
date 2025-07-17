"""
实时转写路由
处理实时转写相关的 WebSocket 请求
"""

from fastapi import APIRouter, WebSocket, Query
from .realtime_handler import RealtimeTranscriptionHandler

router = APIRouter()
handler = RealtimeTranscriptionHandler()

@router.websocket("/ws/asr/transcribe/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证令牌")
):
    """
    实时转写 WebSocket 端点
    
    Args:
        websocket: WebSocket 连接
        token: 用户认证令牌
    """
    await handler.handle_client(websocket, token) 