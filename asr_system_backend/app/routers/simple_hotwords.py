# File: asr_system_backend/app/routers/simple_hotwords.py

import os
from fastapi import APIRouter, HTTPException, status, Body
from typing import List, Dict, Any

router = APIRouter(
    prefix="/simple-hotwords",
    tags=["Simple Hotwords"]
)

# 定义热词文件的路径（项目根目录）
# 后端服务运行在 asr_system_backend/ 目录，所以需要向上返回一级
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOTWORDS_FILE_PATH = os.path.join(PROJECT_ROOT, "hotwords.txt")


@router.get("", response_model=List[Dict[str, Any]])
def get_hotwords_from_file():
    """从 hotwords.txt 文件读取所有热词并返回"""
    if not os.path.exists(HOTWORDS_FILE_PATH):
        # 如果文件不存在，创建一个空文件
        open(HOTWORDS_FILE_PATH, 'a').close()
        return []

    try:
        hotwords = []
        with open(HOTWORDS_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    word = parts[0]
                    weight_str = parts[-1]
                    try:
                        weight = int(weight_str)
                        hotwords.append({"word": word, "weight": weight})
                    except ValueError:
                        # 忽略格式错误的行
                        continue
        return hotwords
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取热词文件失败: {str(e)}"
        )


@router.post("")
def save_hotwords_to_file(hotwords: List[Dict[str, Any]] = Body(...)):
    """接收前端发来的完整热词列表，并覆盖写入 hotwords.txt"""
    try:
        lines_to_write = []
        for item in hotwords:
            word = item.get("word", "").strip()
            weight = item.get("weight", 5)
            if word:
                lines_to_write.append(f"{word} {weight}")

        with open(HOTWORDS_FILE_PATH, "w", encoding="utf-8") as f:
            if lines_to_write:
                f.write("\n".join(lines_to_write) + "\n")
            else:
                f.write("") # 如果列表为空，则写入空文件
        
        return {"message": "热词保存成功", "count": len(lines_to_write)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入热词文件失败: {str(e)}"
        )