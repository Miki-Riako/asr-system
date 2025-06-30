from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, services, models
from ..database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = services.AuthService.register_user(db, user_in)
    return schemas.UserOut(user_id=user.id, username=user.username, created_at=user.created_at)

@router.post("/login")
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = services.AuthService.authenticate_user(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    # JWT生成明天再做，暂时返回简单信息
    # return {"message": "登录成功，JWT功能明日上线"} 
    return schemas.UserOut(
        user_id=user.id, 
        username=user.username, 
        created_at=user.created_at
    )