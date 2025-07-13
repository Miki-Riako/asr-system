from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .. import models
from ..database import get_db
from .auth import get_current_user
from ..rag_service import get_rag_service
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/rag",
    tags=["rag"]
)

# Pydantic模型定义
class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(5, ge=1, le=50, description="返回结果数量")
    threshold: float = Field(0.3, ge=0.0, le=1.0, description="相似度阈值")

class VectorSearchResult(BaseModel):
    word: str
    weight: int
    similarity: float
    rank: int

class VectorSearchResponse(BaseModel):
    query: str
    results: List[VectorSearchResult]
    total_found: int
    processing_time_ms: float

class IndexStatsResponse(BaseModel):
    user_id: str
    total_hotwords: int
    index_dimension: int
    is_initialized: bool
    last_updated: Optional[str] = None

class BulkAddRequest(BaseModel):
    words: List[Dict[str, Any]] = Field(..., description="热词列表，格式：[{'word': 'xxx', 'weight': 5}]")

class IndexManagementResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict] = None

@router.get("/health", summary="RAG服务健康检查")
def health_check():
    """RAG服务健康检查"""
    rag_service = get_rag_service()
    return {
        "status": "healthy" if rag_service.initialized else "initializing",
        "service": "RAG Vector Search Engine",
        "version": "1.0.0",
        "initialized": rag_service.initialized
    }

@router.post("/search", response_model=VectorSearchResponse, summary="向量相似度搜索")
def vector_search(
    request: VectorSearchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    基于向量相似度的热词搜索
    
    使用FAISS进行高效的向量检索，支持语义相似度匹配
    """
    import time
    start_time = time.time()
    
    try:
        rag_service = get_rag_service()
        
        # 确保RAG服务已初始化
        if not rag_service.initialized:
            rag_service.initialize()
            
        # 确保用户索引已构建
        if current_user.id not in rag_service.hotword_metadata:
            rag_service.build_user_hotword_index(db, current_user.id)
        
        # 执行向量搜索
        predictions = rag_service.predict_hotwords(
            request.query, 
            current_user.id, 
            top_k=request.top_k, 
            threshold=request.threshold
        )
        
        # 构建响应
        results = [
            VectorSearchResult(
                word=pred["word"],
                weight=pred["weight"],
                similarity=pred["similarity"],
                rank=pred["rank"]
            )
            for pred in predictions
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return VectorSearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )

@router.get("/index/stats", response_model=IndexStatsResponse, summary="获取索引统计信息")
def get_index_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户热词索引的统计信息"""
    try:
        rag_service = get_rag_service()
        
        # 获取用户热词数量
        hotword_count = db.query(models.Hotword).filter(
            models.Hotword.user_id == current_user.id
        ).count()
        
        # 检查索引状态
        has_index = current_user.id in rag_service.hotword_metadata
        
        return IndexStatsResponse(
            user_id=current_user.id,
            total_hotwords=hotword_count,
            index_dimension=rag_service.dimension if rag_service.initialized else 0,
            is_initialized=rag_service.initialized and has_index,
            last_updated=None  # TODO: 可以添加时间戳跟踪
        )
        
    except Exception as e:
        logger.error(f"获取索引统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )

@router.post("/index/rebuild", response_model=IndexManagementResponse, summary="重建用户索引")
def rebuild_index(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重建用户的热词向量索引"""
    try:
        rag_service = get_rag_service()
        
        # 确保RAG服务已初始化
        if not rag_service.initialized:
            rag_service.initialize()
            
        # 重建索引
        success = rag_service.build_user_hotword_index(db, current_user.id)
        
        if success:
            hotword_count = len(rag_service.hotword_metadata.get(current_user.id, {}).get('words', []))
            return IndexManagementResponse(
                success=True,
                message=f"索引重建成功，包含 {hotword_count} 个热词",
                details={
                    "user_id": current_user.id,
                    "hotword_count": hotword_count,
                    "dimension": rag_service.dimension
                }
            )
        else:
            return IndexManagementResponse(
                success=False,
                message="索引重建失败"
            )
            
    except Exception as e:
        logger.error(f"重建索引失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重建索引失败: {str(e)}"
        )

@router.post("/index/bulk-add", response_model=IndexManagementResponse, summary="批量添加热词到索引")
def bulk_add_to_index(
    request: BulkAddRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量添加热词到向量索引
    
    这是一个高级功能，允许直接向索引添加词条而不通过常规的热词管理API
    """
    try:
        rag_service = get_rag_service()
        
        # 确保RAG服务已初始化
        if not rag_service.initialized:
            rag_service.initialize()
            
        added_count = 0
        skipped_count = 0
        
        for word_data in request.words:
            word = word_data.get("word", "").strip()
            weight = word_data.get("weight", 5)
            
            if not word:
                skipped_count += 1
                continue
                
            # 检查是否已存在
            existing = db.query(models.Hotword).filter(
                models.Hotword.user_id == current_user.id,
                models.Hotword.word == word
            ).first()
            
            if existing:
                skipped_count += 1
                continue
                
            # 添加到数据库
            db_hotword = models.Hotword(
                user_id=current_user.id,
                word=word,
                weight=weight
            )
            db.add(db_hotword)
            added_count += 1
            
        # 提交数据库更改
        db.commit()
        
        # 重建索引
        if added_count > 0:
            rag_service.build_user_hotword_index(db, current_user.id)
            
        return IndexManagementResponse(
            success=True,
            message=f"批量添加完成：新增 {added_count} 个，跳过 {skipped_count} 个",
            details={
                "added": added_count,
                "skipped": skipped_count,
                "total_processed": len(request.words)
            }
        )
        
    except Exception as e:
        logger.error(f"批量添加失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量添加失败: {str(e)}"
        )

@router.get("/suggestions", summary="获取热词建议")
def get_suggestions(
    partial_text: str,
    max_suggestions: int = 5,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    根据部分输入文本获取热词建议
    
    结合前缀匹配和语义相似度，提供智能的热词补全建议
    """
    try:
        rag_service = get_rag_service()
        
        # 确保RAG服务已初始化
        if not rag_service.initialized:
            rag_service.initialize()
            
        # 确保用户索引已构建
        if current_user.id not in rag_service.hotword_metadata:
            rag_service.build_user_hotword_index(db, current_user.id)
            
        # 获取建议
        suggestions = rag_service.get_hotword_suggestions(
            partial_text, 
            current_user.id, 
            max_suggestions
        )
        
        return {
            "partial_text": partial_text,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"获取建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}"
        )

@router.get("/model/info", summary="获取模型信息")
def get_model_info():
    """获取当前使用的向量化模型信息"""
    try:
        rag_service = get_rag_service()
        
        if not rag_service.initialized:
            return {
                "status": "not_initialized",
                "message": "RAG服务未初始化"
            }
            
        model_info = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": rag_service.dimension,
            "max_sequence_length": 256,  # 模型的最大序列长度
            "languages": ["zh", "en", "multilingual"],
            "description": "轻量级多语言句子嵌入模型，适合中英文混合场景",
            "performance": {
                "embedding_speed": "~1000 sentences/sec (CPU)",
                "model_size": "~90MB",
                "accuracy": "适中，平衡速度与准确性"
            }
        }
        
        return model_info
        
    except Exception as e:
        logger.error(f"获取模型信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型信息失败: {str(e)}"
        ) 