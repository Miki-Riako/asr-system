from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def register_user(db: Session, user_in: schemas.UserCreate):
        user = db.query(models.User).filter(models.User.username == user_in.username).first()
        if user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
        hashed_password = AuthService.get_password_hash(user_in.password)
        new_user = models.User(username=user_in.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user 