from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 将变量名改为DATABASE_URL
DATABASE_URL = "sqlite:///./asr_system.db"

engine = create_engine(
    DATABASE_URL,  # 使用新变量名
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()