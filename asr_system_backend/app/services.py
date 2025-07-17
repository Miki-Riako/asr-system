import os
import subprocess
from datetime import datetime
from sqlalchemy.orm import Session
from . import models
from .config import get_settings

settings = get_settings()

class TranscriptionService:
    @staticmethod
    def process_transcription_task(db: Session, task_id: str, file_path: str, hotword_list_id: str = None):
        """处理转写任务"""
        try:
            # 更新任务状态
            task = db.query(models.TranscriptionTask).filter(models.TranscriptionTask.id == task_id).first()
            if not task:
                return
            
            task.status = "processing"
            db.commit()
            
            # 调用本地客户端进行转写
            client_path = os.path.join(os.path.dirname(__file__), "client", "funasr_wss_client.py")
            cmd = ["python", client_path, "--host", "localhost", "--port", "10095", "--mode", "offline", "--audio_in", file_path]
            
            # 执行命令并捕获输出
            process = subprocess.run(cmd, capture_output=True, text=True)
            terminal_output = process.stdout + process.stderr
            
            # 更新任务状态和输出
            task.status = "completed" if process.returncode == 0 else "failed"
            task.terminal_output = terminal_output
            task.completed_at = datetime.utcnow()
            db.commit()
            
            # 清理临时文件
            try:
                os.remove(file_path)
            except:
                pass
                
        except Exception as e:
            # 更新任务状态为失败
            task = db.query(models.TranscriptionTask).filter(models.TranscriptionTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.terminal_output = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
            
            # 清理临时文件
            try:
                os.remove(file_path)
            except:
                pass 