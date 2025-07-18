#!/usr/bin/env python3
"""
创建数据库表的脚本
运行此脚本来创建/更新数据库表结构
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'asr_system_backend'))

from app.database import engine
from app.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """创建所有数据表"""
    try:
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")
        
        # 打印创建的表
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"已创建的表: {', '.join(tables)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("🎉 数据库初始化完成！")
    else:
        print("❌ 数据库初始化失败")
        sys.exit(1)