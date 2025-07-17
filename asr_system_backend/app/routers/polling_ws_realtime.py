# 文件路径: asr_system_backend/app/routers/polling_ws_realtime.py
# 功能: 为新的“轮询式WebSocket”实时转写功能提供后端服务。

import asyncio
import logging
import os
import subprocess
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..auth_service import decode_access_token

# --- 日志和路由配置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 创建一个全新的路由器实例
router = APIRouter()

# --- 新的、独立的连接管理器 ---
class PollingConnectionManager:
    """为新功能创建一个独立的连接管理器，避免与现有功能混淆。"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"[Polling WS] 客户端 {client_id} 已连接。")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"[Polling WS] 客户端 {client_id} 已断开。")

    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

polling_manager = PollingConnectionManager()


# --- WebSocket认证 (可复用，但为清晰起见，我们放在这里) ---
async def get_current_user_from_polling_ws(token: str = Query(...), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username: return None
        user = db.query(User).filter(User.username == username).first()
        return user
    except Exception:
        return None


# --- 音频处理核心函数 (与上次提供的逻辑相同) ---
async def process_polling_chunk(client_id: str, audio_data: bytes):
    temp_id = str(uuid.uuid4())
    webm_path = f"/tmp/{temp_id}.webm"
    wav_path = f"/tmp/{temp_id}.wav"
    
    try:
        with open(webm_path, "wb") as f:
            f.write(audio_data)

        command = f"ffmpeg -i {webm_path} -ar 16000 -ac 1 -y {wav_path}"
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"[Polling WS] FFmpeg转换失败: {stderr.decode()}")
            await polling_manager.send_json(client_id, {"type": "error", "message": "音频格式处理失败"})
            return

        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        client_script_path = os.path.join(root_dir, "client", "funasr_wss_client.py")
        
        transcribe_command = ["python", client_script_path, "--host", "127.0.0.1", "--port", "10095", "--mode", "offline", "--audio_in", wav_path]
        
        transcribe_process = await asyncio.create_subprocess_exec(*transcribe_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        transcribe_stdout, transcribe_stderr = await transcribe_process.communicate()
        output = transcribe_stdout.decode() + transcribe_stderr.decode()
        
        transcription = ""
        for line in output.split("\n"):
            if "pid0_0: demo:" in line:
                transcription = line.split("pid0_0: demo:")[-1].strip()
                break
        
        logger.info(f"[Polling WS] 客户端 {client_id} 的转写结果: '{transcription}'")

        if transcription:
            await polling_manager.send_json(client_id, {
                "type": "polling_transcription_result", # 使用新的类型以区分
                "text": transcription
            })

    except Exception as e:
        logger.error(f"[Polling WS] 处理音频块时出错: {e}")
        await polling_manager.send_json(client_id, {"type": "error", "message": "服务器处理音频时出错"})
    finally:
        if os.path.exists(webm_path): os.remove(webm_path)
        if os.path.exists(wav_path): os.remove(wav_path)


# --- 新的WebSocket端点定义 ---
@router.websocket("/ws/asr/transcribe/polling_realtime") # <--- 注意，这是全新的URL
async def websocket_polling_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    user = await get_current_user_from_polling_ws(token, db)
    if not user:
        await websocket.close(code=1008, reason="认证失败")
        return

    client_id = str(uuid.uuid4())
    await polling_manager.connect(websocket, client_id)
    
    try:
        await polling_manager.send_json(client_id, {"type": "polling_connection_established"})
        
        while True:
            audio_data = await websocket.receive_bytes()
            asyncio.create_task(process_polling_chunk(client_id, audio_data))

    except WebSocketDisconnect:
        polling_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"[Polling WS] 连接 ({client_id}) 出现意外错误: {e}")
        polling_manager.disconnect(client_id)