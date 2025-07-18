#!/usr/bin/env python3
"""
检查现有数据库表结构
"""
import sqlite3
import os

def check_database_structure():
    db_path = "./asr_system.db"
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("数据库中的表:")
        for table in tables:
            table_name = table[0]
            print(f"\n表: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("列信息:")
            for col in columns:
                print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
                
    except Exception as e:
        print(f"检查数据库时出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_structure()