from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, transcription, hotword, realtime
from .database import engine, Base
from .config import get_settings

# 获取配置
settings = get_settings()

# 开发期自动建表，生产建议用Alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(title="支持热词预测的语音识别系统API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router) 
app.include_router(transcription.router)
app.include_router(hotword.router)
app.include_router(realtime.router) 