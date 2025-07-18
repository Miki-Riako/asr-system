#!/usr/bin/env python3
"""
数据库迁移脚本 - 修复表结构
"""
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    db_path = "./asr_system.db"
    
    if not os.path.exists(db_path):
        logger.error("数据库文件不存在")
        return False
    
    # 备份数据库
    backup_path = f"{db_path}.backup"
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"数据库已备份到: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查 transcription_tasks 表是否存在 result 列
        cursor.execute("PRAGMA table_info(transcription_tasks);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"transcription_tasks 表现有列: {column_names}")
        
        # 如果没有 result 列，添加它
        if 'result' not in column_names:
            logger.info("添加 result 列...")
            cursor.execute("ALTER TABLE transcription_tasks ADD COLUMN result TEXT;")
            
        # 检查其他可能缺少的列
        expected_columns = [
            ('result', 'TEXT'),
            ('terminal_output', 'TEXT'),
            ('error_message', 'TEXT'),
            ('completed_at', 'DATETIME')
        ]
        
        for col_name, col_type in expected_columns:
            if col_name not in column_names:
                logger.info(f"添加 {col_name} 列...")
                cursor.execute(f"ALTER TABLE transcription_tasks ADD COLUMN {col_name} {col_type};")
        
        # 检查 transcription_segments 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transcription_segments';")
        if not cursor.fetchone():
            logger.info("创建 transcription_segments 表...")
            cursor.execute("""
                CREATE TABLE transcription_segments (
                    id VARCHAR PRIMARY KEY,
                    task_id VARCHAR NOT NULL,
                    segment_id INTEGER NOT NULL,
                    start_time FLOAT NOT NULL,
                    end_time FLOAT NOT NULL,
                    text TEXT NOT NULL,
                    confidence FLOAT,
                    FOREIGN KEY(task_id) REFERENCES transcription_tasks (id)
                );
            """)
        
        conn.commit()
        logger.info("✅ 数据库迁移完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("🎉 数据库迁移成功！")
    else:
        print("❌ 数据库迁移失败")
        print("可以使用备份文件恢复数据库")