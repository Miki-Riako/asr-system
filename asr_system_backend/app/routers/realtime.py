import asyncio
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..asr_engine import get_asr_engine
from ..rag_service import get_rag_service
from ..auth_service import decode_access_token
import numpy as np
import wave
import io
import tempfile
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# 存储活动的WebSocket连接
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        logger.info(f"用户 {user_id} 建立WebSocket连接 {connection_id}")
        
    def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            del self.active_connections[connection_id]
            
            # 移除用户连接映射
            for user_id, conn_id in list(self.user_connections.items()):
                if conn_id == connection_id:
                    del self.user_connections[user_id]
                    break
                    
            logger.info(f"WebSocket连接 {connection_id} 已断开")
            
    async def send_message(self, connection_id: str, message: dict):
        """发送消息到指定连接"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                self.disconnect(connection_id)

manager = ConnectionManager()

async def get_current_user_ws(token: str, db: Session = Depends(get_db)):
    """WebSocket认证中间件"""
    try:
        # 解码JWT token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的token")
            
        # 从数据库获取用户信息
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
            
        return user
    except Exception as e:
        logger.error(f"WebSocket认证失败: {str(e)}")
        raise HTTPException(status_code=401, detail="认证失败")

@router.websocket("/ws/asr/transcribe/realtime")
async def websocket_realtime_transcribe(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """实时语音转写WebSocket端点"""
    connection_id = f"conn_{hash(websocket)}"
    
    try:
        # 认证用户
        user = await get_current_user_ws(token, db)
        
        # 建立连接
        await manager.connect(websocket, user.id, connection_id)
        
        # 发送连接成功消息
        await manager.send_message(connection_id, {
            "type": "connection_established",
            "message": "WebSocket连接已建立",
            "user_id": user.id
        })
        
        # 初始化ASR引擎
        asr_engine = get_asr_engine()
        if not asr_engine.initialized:
            asr_engine.initialize()
            
        # 初始化RAG服务
        rag_service = get_rag_service()
        if not rag_service.initialized:
            rag_service.initialize()
            
        # 为用户构建热词索引
        rag_service.build_user_hotword_index(db, user.id)
        
        # 音频数据缓冲区
        audio_buffer = bytearray()
        sample_rate = 16000  # 默认采样率
        chunk_duration = 2.0  # 2秒一个处理块
        chunk_size = int(sample_rate * chunk_duration * 2)  # 16-bit PCM
        
        await manager.send_message(connection_id, {
            "type": "ready",
            "message": "实时转写服务已准备就绪",
            "config": {
                "sample_rate": sample_rate,
                "chunk_duration": chunk_duration,
                "supported_formats": ["PCM", "WAV"]
            }
        })
        
        while True:
            # 接收音频数据
            data = await websocket.receive()
            
            if data["type"] == "websocket.receive":
                if "bytes" in data:
                    # 处理二进制音频数据
                    audio_data = data["bytes"]
                    audio_buffer.extend(audio_data)
                    
                    # 当缓冲区积累足够数据时进行转写
                    if len(audio_buffer) >= chunk_size:
                        # 提取音频块
                        chunk_data = bytes(audio_buffer[:chunk_size])
                        audio_buffer = audio_buffer[chunk_size:]
                        
                        # 异步处理音频转写
                        asyncio.create_task(
                            process_audio_chunk(
                                chunk_data,
                                connection_id,
                                user.id,
                                asr_engine,
                                rag_service,
                                db,
                                sample_rate
                            )
                        )
                        
                elif "text" in data:
                    # 处理文本命令
                    try:
                        command = json.loads(data["text"])
                        await handle_command(command, connection_id, user.id, db)
                    except json.JSONDecodeError:
                        await manager.send_message(connection_id, {
                            "type": "error",
                            "message": "无效的JSON格式"
                        })
                        
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接 {connection_id} 主动断开")
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        await manager.send_message(connection_id, {
            "type": "error",
            "message": f"服务器内部错误: {str(e)}"
        })
        manager.disconnect(connection_id)

async def process_audio_chunk(
    audio_data: bytes,
    connection_id: str,
    user_id: str,
    asr_engine,
    rag_service,
    db: Session,
    sample_rate: int
):
    """处理音频块的异步任务"""
    try:
        # 将音频数据写入临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # 创建WAV文件头
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            # 写入临时文件
            temp_file.write(wav_buffer.getvalue())
            temp_file_path = temp_file.name
            
        try:
            # 使用ASR引擎转写音频
            transcription_result = asr_engine.transcribe_audio(temp_file_path)
            
            # 提取转写文本
            transcription_text = transcription_result.get("text", "").strip()
            
            if transcription_text:
                # 使用RAG服务增强转写结果
                enhanced_result = rag_service.enhance_transcription_with_hotwords(
                    transcription_text, user_id
                )
                
                # 发送转写结果
                await manager.send_message(connection_id, {
                    "type": "transcription_result",
                    "data": {
                        "text": enhanced_result["enhanced_text"],
                        "original_text": transcription_text,
                        "confidence_boost": enhanced_result["confidence_boost"],
                        "hotwords_detected": enhanced_result["hotwords_detected"],
                        "predicted_hotwords": enhanced_result.get("predicted_hotwords", []),
                        "segments": transcription_result.get("segments", []),
                        "timestamp": transcription_result.get("processing_time")
                    }
                })
            else:
                # 发送静音检测结果
                await manager.send_message(connection_id, {
                    "type": "silence_detected",
                    "message": "检测到静音"
                })
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"音频处理失败: {str(e)}")
        await manager.send_message(connection_id, {
            "type": "error",
            "message": f"音频处理失败: {str(e)}"
        })

async def handle_command(command: dict, connection_id: str, user_id: str, db: Session):
    """处理WebSocket命令"""
    try:
        command_type = command.get("type")
        
        if command_type == "ping":
            await manager.send_message(connection_id, {
                "type": "pong",
                "timestamp": command.get("timestamp")
            })
            
        elif command_type == "get_hotwords":
            # 获取用户热词列表
            hotwords = db.query(models.Hotword).filter(
                models.Hotword.user_id == user_id
            ).all()
            
            await manager.send_message(connection_id, {
                "type": "hotwords_list",
                "data": [
                    {
                        "id": hw.id,
                        "word": hw.word,
                        "weight": hw.weight
                    }
                    for hw in hotwords
                ]
            })
            
        elif command_type == "update_config":
            # 更新实时转写配置
            config = command.get("config", {})
            await manager.send_message(connection_id, {
                "type": "config_updated",
                "message": "配置已更新",
                "config": config
            })
            
        else:
            await manager.send_message(connection_id, {
                "type": "error",
                "message": f"未知命令类型: {command_type}"
            })
            
    except Exception as e:
        logger.error(f"命令处理失败: {str(e)}")
        await manager.send_message(connection_id, {
            "type": "error",
            "message": f"命令处理失败: {str(e)}"
        }) 