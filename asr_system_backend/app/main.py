from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 1. 导入我们所有需要的路由模块
from .routers import transcription, auth, realtime_websocket, chat, simple_hotwords
from .models import Base, engine
from .config import get_settings

# 初始化数据库
Base.metadata.create_all(bind=engine)

app = FastAPI(title="语音识别系统API")
settings = get_settings()

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，用于开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 文件路径: asr_system_backend/app/main.py
# ...
# 包含路由
app.include_router(auth.router, tags=["认证"])
app.include_router(transcription.router, tags=["转写"]) 
# 确保这一行是存在的
app.include_router(realtime_websocket.router, tags=["实时转写"])
app.include_router(chat.router, tags=["AI聊天"]) 
app.include_router(simple_hotwords.router)