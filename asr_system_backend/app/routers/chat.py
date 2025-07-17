import logging
import json
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import dashscope
from dashscope import Generation

from ..config import get_settings
from ..database import get_db
from .auth import get_current_user
from .. import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])
settings = get_settings()

class ChatRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant" or "system"
    content: str

async def stream_generator(prompt: str, temperature: float = 0.7, max_tokens: int = 2000):
    """使用阿里云通义千问生成流式聊天响应"""
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        logger.error("DashScope API Key 未配置")
        yield "data: " + json.dumps({"error": "服务端未配置API Key"}) + "\n\n"
        return

    dashscope.api_key = api_key

    try:
        # 使用通义千问模型
        responses = Generation.call(
            model='qwen-plus',  # 使用稳定的通义千问Plus模型
            messages=[
                {"role": "system", "content": "你是一个智能助手，能够准确理解用户的语音转写内容并给出有帮助的回复。请用简洁明了的语言回答问题。"},
                {"role": "user", "content": prompt}
            ],
            result_format='message',
            stream=True,
            incremental_output=True,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.8,
        )
        
        for resp in responses:
            if resp.status_code == 200:
                # 处理通义千问的响应格式
                if hasattr(resp.output, 'choices') and len(resp.output.choices) > 0:
                    choice = resp.output.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content
                        if content:  # 确保内容不为空
                            yield f"data: {json.dumps({'content': content, 'model': 'qwen-plus'})}\n\n"
                # 兼容其他响应格式
                elif hasattr(resp.output, 'text') and resp.output.text:
                    content = resp.output.text
                    yield f"data: {json.dumps({'content': content, 'model': 'qwen-plus'})}\n\n"
            else:
                error_msg = f"通义千问 API Error: {resp.code} - {resp.message}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                break
                
        # 发送结束标记
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        logger.error(f"调用通义千问 API时出错: {e}")
        yield f"data: {json.dumps({'error': f'调用AI服务时发生异常: {str(e)}'})}\n\n"

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_user)
):
    """流式聊天接口"""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt不能为空")
    
    logger.info(f"用户 {current_user.username} 发起聊天: {request.prompt[:50]}...")
    
    return StreamingResponse(
        stream_generator(request.prompt, request.temperature, request.max_tokens),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.get("/models")
async def get_available_models():
    """获取可用的聊天模型"""
    return {
        "models": [
            {
                "name": "qwen-plus", 
                "description": "通义千问Plus - 平衡性能与成本",
                "provider": "Alibaba DashScope"
            },
            {
                "name": "qwen-turbo", 
                "description": "通义千问Turbo - 快速响应",
                "provider": "Alibaba DashScope"
            },
            {
                "name": "qwen-max", 
                "description": "通义千问Max - 最强性能",
                "provider": "Alibaba DashScope"
            }
        ],
        "current": "qwen-plus",
        "provider": "Alibaba DashScope"
    }

@router.get("/health")
async def chat_health_check():
    """聊天服务健康检查"""
    api_key = settings.DASHSCOPE_API_KEY
    
    # 测试API连接
    if api_key:
        try:
            dashscope.api_key = api_key
            # 发送一个简单的测试请求
            test_response = Generation.call(
                model='qwen-turbo',
                prompt='测试',
                max_tokens=10
            )
            api_working = test_response.status_code == 200
        except Exception as e:
            logger.error(f"API测试失败: {e}")
            api_working = False
    else:
        api_working = False
    
    return {
        "status": "healthy" if api_working else "api_error",
        "model": "qwen-plus",
        "api_configured": bool(api_key),
        "api_working": api_working
    }

# 非流式聊天接口（可选）
@router.post("/simple")
async def simple_chat(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_user)
):
    """非流式聊天接口"""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt不能为空")
    
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key未配置")
    
    dashscope.api_key = api_key
    
    try:
        response = Generation.call(
            model='qwen-plus',
            messages=[
                {"role": "system", "content": "你是一个智能助手，能够准确理解用户的语音转写内容并给出有帮助的回复。"},
                {"role": "user", "content": request.prompt}
            ],
            result_format='message',
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        if response.status_code == 200:
            if hasattr(response.output, 'choices') and len(response.output.choices) > 0:
                content = response.output.choices[0].message.content
            else:
                content = response.output.text
                
            return {
                "response": content,
                "model": "qwen-plus",
                "usage": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            }
        else:
            raise HTTPException(status_code=500, detail=f"API调用失败: {response.message}")
            
    except Exception as e:
        logger.error(f"聊天API调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI服务调用失败: {str(e)}")