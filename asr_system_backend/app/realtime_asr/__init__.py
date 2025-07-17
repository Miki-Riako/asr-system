"""
实时语音转写模块
提供WebSocket服务，支持实时音频流转写功能
"""

# from .realtime_handler import RealtimeTranscriptionHandler
# 只导入实际用到的内容
from .funasr_client import FunASRRealtimeClient

__all__ = ['FunASRRealtimeClient'] 