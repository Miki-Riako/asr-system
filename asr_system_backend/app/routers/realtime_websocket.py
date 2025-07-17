# 文件路径: asr_system_backend/app/routers/realtime_websocket.py
# 功能: 接收前端通过WebSocket发送的实时音频流，拼接处理后返回转写结果。

import asyncio
import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..auth_service import decode_access_token

# --- 日志和路由配置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

# --- 存储每个连接的音频缓冲区和状态 ---
# 使用字典来管理多个并发连接，key是唯一的client_id
client_buffers: dict[str, bytearray] = {}
client_last_processed_time: dict[str, datetime] = {}
PROCESSING_INTERVAL_SECONDS = 5 # 每隔5秒处理一次累积的音频

# --- WebSocket连接管理器 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # 初始化该连接的缓冲区和时间戳
        client_buffers[client_id] = bytearray()
        client_last_processed_time[client_id] = datetime.now()
        logger.info(f"客户端 {client_id} 已连接，并已创建音频缓冲区。")

    def disconnect(self, client_id: str):
        # 清理资源
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in client_buffers:
            del client_buffers[client_id]
        if client_id in client_last_processed_time:
            del client_last_processed_time[client_id]
        logger.info(f"客户端 {client_id} 已断开，相关资源已清理。")

    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

# --- WebSocket认证 ---
async def get_current_user_from_ws_token(token: str, db: Session):
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username: return None
        return db.query(User).filter(User.username == username).first()
    except Exception:
        return None

# --- 音频处理核心函数 ---
async def process_accumulated_audio(client_id: str):
    """
    处理指定客户端累积的音频数据。
    这个函数会被定时调用或者在接收到新数据时触发检查。
    """
    # 检查缓冲区中是否有数据
    if client_id not in client_buffers or len(client_buffers[client_id]) == 0:
        return

    # 复制缓冲区内容进行处理，并清空原缓冲区
    audio_data_to_process = client_buffers[client_id]
    client_buffers[client_id] = bytearray()
    
    # 更新处理时间戳
    client_last_processed_time[client_id] = datetime.now()
    
    logger.info(f"开始处理客户端 {client_id} 的 {len(audio_data_to_process)} 字节音频数据。")

    # 后续逻辑与之前的实现完全一致：保存、转换、调用脚本、返回结果、清理
    temp_id = str(uuid.uuid4())
    webm_path = f"/tmp/{temp_id}.webm"
    wav_path = f"/tmp/{temp_id}.wav"
    
    try:
        with open(webm_path, "wb") as f:
            f.write(audio_data_to_process)

        command = f"ffmpeg -i {webm_path} -ar 16000 -ac 1 -y {wav_path}"
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = f"FFmpeg转换失败: {stderr.decode()}"
            logger.error(error_message)
            await manager.send_json(client_id, {"type": "error", "message": "音频格式处理失败"})
            return

        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        client_script_path = os.path.join(root_dir, "client", "funasr_wss_client.py")
        
        transcribe_command = ["python", client_script_path, "--host", "127.0.0.1", "--port", "10095", "--mode", "offline", "--audio_in", wav_path]
        
        transcribe_process = await asyncio.create_subprocess_exec(*transcribe_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        transcribe_stdout, _ = await transcribe_process.communicate()
        output = transcribe_stdout.decode()
        
        transcription = ""
        for line in output.split("\n"):
            if "pid0_0: demo:" in line:
                transcription = line.split("pid0_0: demo:")[-1].strip()
                break
        
        logger.info(f"客户端 {client_id} 的转写结果: '{transcription}'")

        if transcription:
            await manager.send_json(client_id, {
                "type": "transcription_result",
                "data": {
                    "text": transcription,
                    "confidence": 0.95,
                    "hotwords_detected": [],
                    "confidence_boost": 1.0,
                    "timestamp": datetime.now().isoformat()
                }
            })

    except Exception as e:
        logger.error(f"处理累积音频时出错: {e}")
        await manager.send_json(client_id, {"type": "error", "message": "服务器处理音频时出错"})
    finally:
        if os.path.exists(webm_path): os.remove(webm_path)
        if os.path.exists(wav_path): os.remove(wav_path)

# --- WebSocket端点定义 ---
@router.websocket("/ws/asr/transcribe/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    处理实时语音转写的WebSocket端点。
    这个版本会累积音频数据，并按固定时间间隔进行处理。
    """
    user = await get_current_user_from_ws_token(token, db)
    if not user:
        await websocket.close(code=1008, reason="认证失败")
        return

    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        await manager.send_json(client_id, {"type": "connection_established", "user_id": user.username})
        await manager.send_json(client_id, {"type": "ready"})
        
        while True:
            # 1. 接收前端发送的一小块音频数据
            audio_data = await websocket.receive_bytes()
            
            # 2. 将接收到的数据追加到该客户端的缓冲区
            if client_id in client_buffers:
                client_buffers[client_id].extend(audio_data)

            # 3. 检查是否达到了处理时间
            now = datetime.now()
            last_processed = client_last_processed_time.get(client_id, now)
            
            if now - last_processed >= timedelta(seconds=PROCESSING_INTERVAL_SECONDS):
                # 如果距离上次处理已超过5秒，则立即处理累积的音频
                # 使用create_task使其在后台运行，不阻塞接收下一块数据
                asyncio.create_task(process_accumulated_audio(client_id))

    except WebSocketDisconnect:
        # 客户端断开连接时，处理最后剩余的音频数据
        logger.info(f"客户端 {client_id} 正在断开连接，处理剩余音频...")
        await process_accumulated_audio(client_id)
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket连接出现意外错误 ({client_id}): {e}")
        manager.disconnect(client_id)