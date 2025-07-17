import os
import logging
import asyncio
import websockets
import json
import wave
from typing import List, Dict, Optional
from datetime import datetime
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ASREngine:
    def __init__(self):
        """初始化ASR引擎"""
        self.host = "127.0.0.1"  # FunASR服务地址
        self.port = 10095       # FunASR服务端口
        self.initialized = True  # FunASR服务是独立的Docker容器，不需要初始化
    
    def initialize(self):
        """FunASR服务是独立的Docker容器，不需要初始化"""
        pass
    
    async def _transcribe_with_funasr(self, audio_file_path: str) -> Dict:
        """使用FunASR WebSocket客户端进行转写"""
        try:
            # 读取音频文件
            with wave.open(audio_file_path, 'rb') as wav_file:
                audio_bytes = wav_file.readframes(wav_file.getnframes())
                sample_rate = wav_file.getframerate()
            
            # 连接WebSocket服务器
            uri = f"ws://{self.host}:{self.port}"
            logger.info(f"正在连接FunASR服务: {uri}")
            
            async with websockets.connect(uri, ping_interval=None) as websocket:
                # 发送初始配置
                config = {
                    "mode": "offline",
                    "chunk_size": [5, 10, 5],
                    "chunk_interval": 10,
                    "wav_name": os.path.basename(audio_file_path),
                    "is_speaking": True,
                    "audio_fs": sample_rate,
                    "wav_format": "wav",
                    "hotwords": "",
                    "itn": True
                }
                await websocket.send(json.dumps(config))
                logger.info("已发送配置信息")
                
                # 发送音频数据
                await websocket.send(audio_bytes)
                logger.info("已发送音频数据")
                
                # 发送结束标记
                await websocket.send(json.dumps({"is_speaking": False}))
                logger.info("已发送结束标记")
                
                # 接收转写结果
                while True:
                    try:
                        result = await websocket.recv()
                        logger.info(f"收到结果: {result}")
                        
                        if isinstance(result, str):
                            try:
                                # 尝试解析JSON结果
                                json_result = json.loads(result)
                                if "text" in json_result:
                                    text = json_result["text"]
                                else:
                                    # 如果不是JSON或没有text字段，使用原始文本
                                    text = result.split(": ")[-1].strip()
                                
                                # 构建标准格式的结果
                                formatted_result = {
                                    "text": text,
                                    "language": "zh",
                                    "segments": [{
                                        "segment_id": 0,
                                        "start_time": 0,
                                        "end_time": 0,  # FunASR离线模式不提供时间戳
                                        "text": text,
                                        "confidence": 1.0  # FunASR离线模式不提供置信度
                                    }],
                                    "duration": 0,  # FunASR离线模式不提供时长
                                    "processing_time": datetime.now().isoformat()
                                }
                                return formatted_result
                            except json.JSONDecodeError:
                                continue
                    except websockets.exceptions.ConnectionClosed:
                        break
                
                raise ValueError("未收到有效的转写结果")
                    
        except Exception as e:
            logger.error(f"FunASR转写失败: {str(e)}")
            raise
    
    async def _transcribe_with_funasr(self, audio_stream):
        uri = f"ws://{self.host}:{self.port}"
        async with websockets.connect(uri) as ws:
            # 发送实时音频流
            while True:
                chunk = await audio_stream.read(640)  # 40ms的16kHz 16bit音频
                if not chunk:
                    break
                await ws.send(chunk)
                # 接收转写结果
                result = await ws.recv()
                yield json.loads(result)
    
    def transcribe_audio(self, audio_file_path: str, language: str = "zh") -> Dict:
        """转写音频文件"""
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
            
        # 创建事件循环并运行WebSocket客户端
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._transcribe_with_funasr(audio_file_path))
            return result
        finally:
            loop.close()
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return [".wav"]  # 目前只支持WAV格式
    
    def validate_audio_file(self, file_path: str) -> bool:
        """验证音频文件是否有效"""
        try:
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            if ext not in self.get_supported_formats():
                return False
            
            # 尝试打开WAV文件
            with wave.open(file_path, 'rb') as wav_file:
                return wav_file.getnframes() > 0
                
        except Exception:
            return False

# 全局ASR引擎实例
asr_engine = ASREngine()

def get_asr_engine() -> ASREngine:
    """获取ASR引擎实例"""
    return asr_engine