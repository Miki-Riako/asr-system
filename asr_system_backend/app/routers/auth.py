# File: asr_system_backend/app/routers/auth.py (FINAL & SIMPLEST VERSION)

import json
import os
from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, auth_service  # 确保 schemas 和 auth_service 被导入

# --- 配置 ---
# 我们将把用户信息直接存储在这个JSON文件里
USERS_FILE = "users.json"
router = APIRouter(prefix="/auth", tags=["认证"])

# --- 辅助函数 ---
def load_users():
    """从 users.json 加载用户数据"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users_data):
    """将用户数据保存到 users.json"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4)

# --- API 接口 ---

@router.post("/register")
def register(user_in: schemas.UserCreate):
    """
    【极简版注册】
    - 接收 JSON: { "username": "...", "password": "..." }
    """
    users = load_users()
    if user_in.username in users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    
    # 直接存储明文密码，保持绝对简单
    users[user_in.username] = {"password": user_in.password}
    save_users(users)
    
    # 注册成功后直接返回一个token，让用户能自动登录
    access_token = auth_service.create_access_token(data={"sub": user_in.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=schemas.Token)
def login(user_in: schemas.UserLogin):
    """
    【极简版登录】
    - 接收 JSON: { "username": "...", "password": "..." }
    """
    users = load_users()
    user = users.get(user_in.username)
    
    if not user or user.get("password") != user_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user_in.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- 以下部分保持不变，用于验证Token ---
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    users = load_users()
    if username not in users:
        raise credentials_exception
    return {"username": username}

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user