import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """应用配置设置"""
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./asr_system.db")
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "!!!secret_key!!!")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # ASR引擎配置
    ASR_MODEL_SIZE: str = os.getenv("ASR_MODEL_SIZE", "base")  # tiny, base, small, medium, large
    ASR_LANGUAGE: str = os.getenv("ASR_LANGUAGE", "zh")  # 默认语言
    ASR_ENABLE_GPU: bool = os.getenv("ASR_ENABLE_GPU", "true").lower() == "true"
    ASR_MAX_FILE_SIZE_MB: int = int(os.getenv("ASR_MAX_FILE_SIZE_MB", "100"))
    ASR_SUPPORTED_FORMATS: list = [".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"]
    
    # 文件存储配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    MAX_UPLOAD_SIZE: int = ASR_MAX_FILE_SIZE_MB * 1024 * 1024  # 转换为字节
    
    # RAG服务配置
    RAG_MODEL_NAME: str = os.getenv("RAG_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    RAG_VECTOR_DIMENSION: int = 384
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.5"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    # CORS配置
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    
    # 性能配置
    BACKGROUND_TASK_WORKERS: int = int(os.getenv("BACKGROUND_TASK_WORKERS", "2"))
    ASR_PROCESSING_TIMEOUT: int = int(os.getenv("ASR_PROCESSING_TIMEOUT", "300"))  # 5分钟
    
    def __init__(self):
        # 确保上传目录存在
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
    
    @property
    def asr_model_config(self) -> dict:
        """获取ASR模型配置"""
        return {
            "model_size": self.ASR_MODEL_SIZE,
            "language": self.ASR_LANGUAGE,
            "enable_gpu": self.ASR_ENABLE_GPU,
            "max_file_size_mb": self.ASR_MAX_FILE_SIZE_MB,
            "supported_formats": self.ASR_SUPPORTED_FORMATS,
            "processing_timeout": self.ASR_PROCESSING_TIMEOUT
        }
    
    @property
    def rag_config(self) -> dict:
        """获取RAG服务配置"""
        return {
            "model_name": self.RAG_MODEL_NAME,
            "vector_dimension": self.RAG_VECTOR_DIMENSION,
            "similarity_threshold": self.RAG_SIMILARITY_THRESHOLD
        }

# 全局配置实例
settings = Settings()

def get_settings() -> Settings:
    """获取应用配置"""
    return settings 