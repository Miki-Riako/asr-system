#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表结构和初始数据
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Base, engine, SessionLocal
from app.models import User, Hotword, TranscriptionTask, TranscriptionSegment
from app.config import get_settings
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """创建所有数据表"""
    try:
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        return False

def create_sample_data():
    """创建示例数据（可选）"""
    try:
        db = SessionLocal()
        
        # 检查是否已有数据
        user_count = db.query(User).count()
        if user_count > 0:
            logger.info("数据库中已有用户数据，跳过示例数据创建")
            return True
        
        logger.info("创建示例数据...")
        
        # 这里可以添加示例数据创建逻辑
        # 但为了安全，我们暂时不创建任何示例数据
        
        logger.info("✅ 示例数据创建完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 示例数据创建失败: {e}")
        return False
    finally:
        db.close()

def verify_database():
    """验证数据库连接和表结构"""
    try:
        db = SessionLocal()
        
        # 测试每个表
        tables = [User, Hotword, TranscriptionTask, TranscriptionSegment]
        for table in tables:
            count = db.query(table).count()
            logger.info(f"表 {table.__tablename__}: {count} 条记录")
        
        logger.info("✅ 数据库验证成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库验证失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("ASR系统数据库初始化")
    logger.info("=" * 50)
    
    settings = get_settings()
    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    
    # 创建必要的目录
    upload_dir = Path(settings.UPLOAD_DIR)
    temp_dir = Path(settings.TEMP_DIR)
    
    upload_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    
    logger.info(f"上传目录: {upload_dir.absolute()}")
    logger.info(f"临时目录: {temp_dir.absolute()}")
    
    # 初始化数据库
    success = True
    success &= create_tables()
    success &= create_sample_data()
    success &= verify_database()
    
    if success:
        logger.info("🎉 数据库初始化完成！")
        logger.info("现在可以启动应用程序了:")
        logger.info("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        logger.error("❌ 数据库初始化失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 