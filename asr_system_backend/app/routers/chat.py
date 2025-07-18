import logging
import json
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import dashscope
from dashscope import Generation

# 移除所有与数据库和认证相关的导入，实现完全解耦
# from ..database import get_db
# from .auth import get_current_user
# from .. import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# =========================================================================
#  救命方案核心：将API Key硬编码在这里
# =========================================================================
DASHSCOPE_API_KEY = "sk-adda7d0fd3b7488e92750d1c27bffcd2"

class ChatRequest(BaseModel):
    prompt: str

async def stream_generator(prompt: str):
    """
    使用硬编码的API Key调用阿里云通义千问，并生成流式聊天响应。
    """
    if not DASHSCOPE_API_KEY:
        error_message = "服务端API Key未硬编码！"
        logger.error(error_message)
        yield f"data: {json.dumps({'error': error_message})}\n\n"
        return

    # 每次调用都设置一次，确保使用的是我们硬编码的Key
    dashscope.api_key = DASHSCOPE_API_KEY
    logger.info(f"正在使用API Key: {DASHSCOPE_API_KEY[:10]}... 调用通义千问模型。")

    try:
        messages = [
            {"role": "system", "content": "你是一个智能助手，能够准确理解用户的语音转写内容并给出有帮助的回复。请用简洁明了的语言回答问题。"},
            {"role": "user", "content": prompt}
        ]
        
        responses = Generation.call(
            model='qwen-plus',
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
        )
        
        full_response_content = "" # 用于在日志中记录完整响应
        for resp in responses:
            if resp.status_code == 200:
                content = resp.output.choices[0]['message']['content']
                if content:
                    full_response_content += content
                    # 按照 Server-Sent Events (SSE) 格式发送数据
                    yield f"data: {json.dumps({'content': content})}\n\n"
            else:
                error_msg = f"通义千问API错误: {resp.code} - {resp.message}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                return # 发生错误，立即停止

        logger.info(f"通义千问完整响应: {full_response_content}")

    except Exception as e:
        error_msg = f"调用AI服务时发生未知异常: {str(e)}"
        logger.error(error_msg, exc_info=True) # 打印完整的错误堆栈
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
    finally:
        # 发送一个结束信号，告诉前端数据流已结束
        yield f"data: {json.dumps({'done': True})}\n\n"
        logger.info("流式响应结束。")


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    【救命版】流式聊天接口，已移除用户认证依赖。
    现在任何人都可以调用这个接口进行测试。
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt不能为空")
    
    logger.info(f"收到匿名聊天请求: '{request.prompt[:100]}...'")
    
    return StreamingResponse(
        stream_generator(request.prompt),
        media_type="text/event-stream"
    )