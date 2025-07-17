from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import transcription, auth, realtime_websocket
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

# 包含路由
app.include_router(auth.router, tags=["认证"])
app.include_router(transcription.router, tags=["转写"]) 
app.include_router(realtime_websocket.router, tags=["实时转写"]) 