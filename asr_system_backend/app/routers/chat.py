# 文件: asr_system_backend/app/routers/chat.py

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import dashscope
from ..config import get_settings

# 配置日志和路由
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])
settings = get_settings()

# 定义请求体模型
class ChatRequest(BaseModel):
    prompt: str

# 定义一个异步生成器，用于流式传输数据
async def stream_generator(prompt: str):
    """
    调用DeepSeek API并以流式方式返回结果
    """
    # 从配置中获取API Key
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        logger.error("DashScope API Key 未配置")
        # 直接在流中返回错误信息
        yield "Error: Server's API Key is not configured."
        return

    dashscope.api_key = api_key

    try:
        # 调用DeepSeek模型的流式生成接口
        responses = dashscope.Generation.call(
            model='deepseek-v2-chat',
            prompt=prompt,
            stream=True,
            incremental_output=True # 增量输出，实现打字机效果
        )

        for resp in responses:
            if resp.status_code == 200:
                content = resp.output.choices[0]['message']['content']
                yield content # 将每个增量内容块发送给前端
            else:
                error_msg = f"Error: code: {resp.status_code}, message: {resp.message}"
                logger.error(error_msg)
                yield error_msg
                break
    except Exception as e:
        logger.error(f"调用DashScope API时出错: {e}")
        yield f"Error: An exception occurred while calling the AI service."

# 定义流式API端点
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    接收前端的Prompt，并以流式方式返回DeepSeek模型的响应
    """
    if not request.prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt不能为空"
        )
    
    return StreamingResponse(stream_generator(request.prompt), media_type="text/event-stream")