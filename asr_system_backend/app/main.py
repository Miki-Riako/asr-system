from fastapi import FastAPI
from .routers import auth
from .database import engine, Base

# 开发期自动建表，生产建议用Alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(title="支持热词预测的语音识别系统API")

app.include_router(auth.router) 