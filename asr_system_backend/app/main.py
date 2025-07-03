from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, transcription, hotword
from .database import engine, Base

# 开发期自动建表，生产建议用Alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(title="支持热词预测的语音识别系统API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transcription.router)
app.include_router(hotword.router) 