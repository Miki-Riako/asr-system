import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from . import models
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.model = None
        self.index = None
        self.hotword_embeddings = {}
        self.hotword_metadata = {}
        self.dimension = 384  # sentence-transformers/all-MiniLM-L6-v2 的维度
        self.initialized = False
        
    def initialize(self):
        """初始化RAG服务，加载预训练模型"""
        try:
            # 加载轻量级的多语言模型
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # 创建FAISS索引 (使用余弦相似度)
            self.index = faiss.IndexFlatIP(self.dimension)
            
            self.initialized = True
            logger.info("RAG服务初始化成功")
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {str(e)}")
            self.initialized = False
    
    def build_user_hotword_index(self, db: Session, user_id: str) -> bool:
        """为特定用户构建热词索引"""
        if not self.initialized:
            self.initialize()
            
        if not self.initialized:
            return False
            
        try:
            # 获取用户的所有热词
            hotwords = db.query(models.Hotword).filter(
                models.Hotword.user_id == user_id
            ).all()
            
            if not hotwords:
                logger.info(f"用户 {user_id} 没有热词，跳过索引构建")
                return True
            
            # 提取热词文本和权重
            hotword_texts = [hw.word for hw in hotwords]
            hotword_weights = [hw.weight for hw in hotwords]
            
            # 生成嵌入向量
            embeddings = self.model.encode(hotword_texts, normalize_embeddings=True)
            
            # 清空并重建索引
            self.index.reset()
            self.hotword_embeddings[user_id] = embeddings
            self.hotword_metadata[user_id] = {
                'words': hotword_texts,
                'weights': hotword_weights,
                'ids': [hw.id for hw in hotwords]
            }
            
            # 添加到FAISS索引
            self.index.add(embeddings)
            
            logger.info(f"为用户 {user_id} 构建了包含 {len(hotwords)} 个热词的索引")
            return True
            
        except Exception as e:
            logger.error(f"构建用户热词索引失败: {str(e)}")
            return False
    
    def predict_hotwords(self, text: str, user_id: str, top_k: int = 5, threshold: float = 0.5) -> List[Dict]:
        """根据输入文本预测相关热词"""
        if not self.initialized:
            logger.warning("RAG服务未初始化")
            return []
            
        if user_id not in self.hotword_metadata:
            logger.warning(f"用户 {user_id} 的热词索引不存在")
            return []
            
        try:
            # 对输入文本进行编码
            query_embedding = self.model.encode([text], normalize_embeddings=True)
            
            # 在FAISS索引中搜索
            similarities, indices = self.index.search(query_embedding, min(top_k, len(self.hotword_metadata[user_id]['words'])))
            
            # 构建结果
            predictions = []
            metadata = self.hotword_metadata[user_id]
            
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= threshold:  # 只返回相似度超过阈值的结果
                    predictions.append({
                        'word': metadata['words'][idx],
                        'weight': metadata['weights'][idx],
                        'similarity': float(similarity),
                        'rank': i + 1
                    })
            
            # 按权重和相似度排序
            predictions.sort(key=lambda x: (x['weight'] * x['similarity']), reverse=True)
            
            return predictions[:top_k]
            
        except Exception as e:
            logger.error(f"热词预测失败: {str(e)}")
            return []
    
    def enhance_transcription_with_hotwords(self, transcription_text: str, user_id: str) -> Dict:
        """使用热词增强转写结果"""
        if not transcription_text:
            return {
                'enhanced_text': transcription_text,
                'hotwords_detected': [],
                'confidence_boost': 1.0
            }
        
        try:
            # 预测相关热词
            predicted_hotwords = self.predict_hotwords(transcription_text, user_id, top_k=10, threshold=0.3)
            
            enhanced_text = transcription_text
            detected_hotwords = []
            confidence_boost = 1.0
            
            # 检查是否有热词在转写文本中
            for hotword_info in predicted_hotwords:
                word = hotword_info['word']
                if word.lower() in transcription_text.lower():
                    detected_hotwords.append(hotword_info)
                    # 根据热词权重提升置信度
                    confidence_boost += (hotword_info['weight'] / 10) * 0.1
            
            # 应用简单的热词替换增强（在实际应用中可能更复杂）
            for hotword_info in detected_hotwords:
                word = hotword_info['word']
                # 确保正确的大小写
                enhanced_text = enhanced_text.replace(word.lower(), word)
                enhanced_text = enhanced_text.replace(word.upper(), word)
            
            return {
                'enhanced_text': enhanced_text,
                'hotwords_detected': detected_hotwords,
                'confidence_boost': min(confidence_boost, 2.0),  # 最大提升2倍
                'predicted_hotwords': predicted_hotwords[:5]  # 返回前5个预测热词
            }
            
        except Exception as e:
            logger.error(f"转写增强失败: {str(e)}")
            return {
                'enhanced_text': transcription_text,
                'hotwords_detected': [],
                'confidence_boost': 1.0
            }
    
    def get_hotword_suggestions(self, partial_text: str, user_id: str, max_suggestions: int = 5) -> List[str]:
        """根据部分输入文本获取热词建议"""
        if not partial_text or len(partial_text) < 2:
            return []
            
        if user_id not in self.hotword_metadata:
            return []
            
        try:
            # 预测相关热词
            predictions = self.predict_hotwords(partial_text, user_id, top_k=max_suggestions * 2, threshold=0.2)
            
            # 过滤出以部分文本开头的热词或相似的热词
            suggestions = []
            metadata = self.hotword_metadata[user_id]
            
            # 首先添加前缀匹配的热词
            for word in metadata['words']:
                if word.lower().startswith(partial_text.lower()) and len(suggestions) < max_suggestions:
                    suggestions.append(word)
            
            # 然后添加语义相似的热词
            for pred in predictions:
                if pred['word'] not in suggestions and len(suggestions) < max_suggestions:
                    suggestions.append(pred['word'])
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"获取热词建议失败: {str(e)}")
            return []

# 全局RAG服务实例
rag_service = RAGService()

def get_rag_service() -> RAGService:
    """获取RAG服务实例"""
    return rag_service 