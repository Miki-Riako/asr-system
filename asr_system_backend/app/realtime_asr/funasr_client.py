"""
FunASR 实时客户端
负责与 FunASR 服务器建立 WebSocket 连接并进行实时音频转写
"""

import json
import asyncio
import websockets
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FunASRRealtimeClient:
    """FunASR 实时转写客户端"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 10095):
        """
        初始化 FunASR 实时客户端
        
        Args:
            host: FunASR 服务器地址
            port: FunASR 服务器端口
        """
        self.host = host
        self.port = port
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.task_id: Optional[str] = None
        
    async def connect(self) -> bool:
        """
        连接到 FunASR 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            ws_url = f"ws://{self.host}:{self.port}/ws/decode"
            self.ws = await websockets.connect(ws_url)
            self.is_connected = True
            
            # 发送启动命令
            start_command = {
                "mode": "online",
                "chunk_size": 3200,  # 200ms @ 16kHz
                "chunk_interval": 200,  # 每200ms发送一次
                "wav_format": True,  # 使用 WAV 格式
                "audio_fs": 16000,  # 采样率
                "audio_channels": 1,  # 单声道
                "audio_bits": 16,  # 16位
            }
            
            await self.ws.send(json.dumps(start_command))
            response = await self.ws.recv()
            response_data = json.loads(response)
            
            if response_data.get("status") == 0:
                self.task_id = response_data.get("task_id")
                logger.info(f"Connected to FunASR server, task_id: {self.task_id}")
                return True
            else:
                logger.error(f"Failed to start streaming: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to FunASR server: {e}")
            self.is_connected = False
            return False
            
    async def send_audio(self, audio_chunk: bytes) -> Dict[str, Any]:
        """
        发送音频数据到 FunASR 服务器
        
        Args:
            audio_chunk: 音频数据块
            
        Returns:
            Dict[str, Any]: 识别结果
        """
        if not self.is_connected or not self.ws:
            raise ConnectionError("Not connected to FunASR server")
            
        try:
            # 发送音频数据
            await self.ws.send(audio_chunk)
            
            # 接收识别结果
            response = await self.ws.recv()
            result = json.loads(response)
            
            return {
                "text": result.get("text", ""),
                "is_final": result.get("is_final", False),
                "confidence": result.get("confidence", 0.0),
                "segments": result.get("segments", []),
                "status": result.get("status", -1)
            }
            
        except Exception as e:
            logger.error(f"Error while sending audio data: {e}")
            raise
            
    async def stop(self) -> None:
        """停止转写并关闭连接"""
        if self.ws:
            try:
                # 发送结束命令
                end_command = {
                    "end": True,
                    "task_id": self.task_id
                }
                await self.ws.send(json.dumps(end_command))
                
                # 等待最后的结果
                response = await self.ws.recv()
                logger.info(f"Final response: {response}")
                
            except Exception as e:
                logger.error(f"Error while stopping transcription: {e}")
            
            finally:
                await self.ws.close()
                self.ws = None
                self.is_connected = False
                self.task_id = None 