import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from . import models
import logging
import pickle
from datetime import datetime
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RAGService:
    def __init__(self):
        self.model = None
        self.index = None
        self.hotword_embeddings = {}
        self.hotword_metadata = {}
        self.dimension = 384  # sentence-transformers/all-MiniLM-L6-v2 的维度
        self.initialized = False
        self.index_dir = os.path.join(settings.TEMP_DIR, "rag_indices")
        
        # 确保索引目录存在
        os.makedirs(self.index_dir, exist_ok=True)
        
    def initialize(self):
        """初始化RAG服务，加载预训练模型"""
        try:
            # 加载轻量级的多语言模型
            logger.info("正在加载句子嵌入模型...")
            self.model = SentenceTransformer(settings.RAG_MODEL_NAME)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # 创建FAISS索引 (使用余弦相似度)
            self.index = faiss.IndexFlatIP(self.dimension)
            
            self.initialized = True
            logger.info(f"RAG服务初始化成功 (模型: {settings.RAG_MODEL_NAME}, 维度: {self.dimension})")
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {str(e)}")
            self.initialized = False
    
    def save_user_index(self, user_id: str) -> bool:
        """保存用户索引到文件"""
        try:
            if user_id not in self.hotword_metadata:
                logger.warning(f"用户 {user_id} 的索引不存在，无法保存")
                return False
                
            index_file = os.path.join(self.index_dir, f"user_{user_id}.index")
            metadata_file = os.path.join(self.index_dir, f"user_{user_id}.metadata")
            
            # 保存FAISS索引
            user_embeddings = self.hotword_embeddings.get(user_id)
            if user_embeddings is not None:
                # 创建临时索引只包含该用户的向量
                temp_index = faiss.IndexFlatIP(self.dimension)
                temp_index.add(user_embeddings)
                faiss.write_index(temp_index, index_file)
                
            # 保存元数据
            metadata = self.hotword_metadata[user_id].copy()
            metadata['last_updated'] = datetime.now().isoformat()
            metadata['dimension'] = self.dimension
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            logger.info(f"用户 {user_id} 的索引已保存到文件")
            return True
            
        except Exception as e:
            logger.error(f"保存用户索引失败: {str(e)}")
            return False
    
    def load_user_index(self, user_id: str) -> bool:
        """从文件加载用户索引"""
        try:
            index_file = os.path.join(self.index_dir, f"user_{user_id}.index")
            metadata_file = os.path.join(self.index_dir, f"user_{user_id}.metadata")
            
            # 检查文件是否存在
            if not os.path.exists(index_file) or not os.path.exists(metadata_file):
                logger.info(f"用户 {user_id} 的索引文件不存在")
                return False
                
            # 加载元数据
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 验证维度兼容性
            if metadata.get('dimension', 0) != self.dimension:
                logger.warning(f"用户 {user_id} 的索引维度不匹配，需要重建")
                return False
                
            # 加载FAISS索引
            temp_index = faiss.read_index(index_file)
            embeddings = np.zeros((temp_index.ntotal, self.dimension), dtype=np.float32)
            temp_index.reconstruct_n(0, temp_index.ntotal, embeddings)
            
            # 恢复到服务中
            self.hotword_embeddings[user_id] = embeddings
            self.hotword_metadata[user_id] = metadata
            
            # 重建全局索引
            self._rebuild_global_index()
            
            logger.info(f"用户 {user_id} 的索引已从文件加载，包含 {len(metadata.get('words', []))} 个热词")
            return True
            
        except Exception as e:
            logger.error(f"加载用户索引失败: {str(e)}")
            return False
    
    def _rebuild_global_index(self):
        """重建全局FAISS索引"""
        try:
            self.index.reset()
            
            for user_id, embeddings in self.hotword_embeddings.items():
                if embeddings is not None and len(embeddings) > 0:
                    self.index.add(embeddings)
                    
            logger.debug("全局索引重建完成")
            
        except Exception as e:
            logger.error(f"重建全局索引失败: {str(e)}")
    
    def build_user_hotword_index(self, db: Session, user_id: str) -> bool:
        """为特定用户构建热词索引"""
        if not self.initialized:
            self.initialize()
            
        if not self.initialized:
            return False
            
        try:
            # 尝试从文件加载现有索引
            if self.load_user_index(user_id):
                # 检查数据库中的热词是否有更新
                db_hotwords = db.query(models.Hotword).filter(
                    models.Hotword.user_id == user_id
                ).all()
                
                db_words = {hw.word: hw.weight for hw in db_hotwords}
                cached_words = {word: weight for word, weight in zip(
                    self.hotword_metadata[user_id]['words'],
                    self.hotword_metadata[user_id]['weights']
                )}
                
                # 如果数据一致，直接使用缓存的索引
                if db_words == cached_words:
                    logger.info(f"用户 {user_id} 的索引已是最新，无需重建")
                    return True
            
            # 获取用户的所有热词
            hotwords = db.query(models.Hotword).filter(
                models.Hotword.user_id == user_id
            ).all()
            
            if not hotwords:
                logger.info(f"用户 {user_id} 没有热词，跳过索引构建")
                # 清理可能存在的旧索引
                if user_id in self.hotword_embeddings:
                    del self.hotword_embeddings[user_id]
                if user_id in self.hotword_metadata:
                    del self.hotword_metadata[user_id]
                return True
            
            # 提取热词文本和权重
            hotword_texts = [hw.word for hw in hotwords]
            hotword_weights = [hw.weight for hw in hotwords]
            
            # 生成嵌入向量
            logger.info(f"正在为用户 {user_id} 生成 {len(hotword_texts)} 个热词的向量嵌入...")
            embeddings = self.model.encode(hotword_texts, normalize_embeddings=True)
            
            # 更新内存中的数据
            self.hotword_embeddings[user_id] = embeddings
            self.hotword_metadata[user_id] = {
                'words': hotword_texts,
                'weights': hotword_weights,
                'ids': [hw.id for hw in hotwords]
            }
            
            # 重建全局索引
            self._rebuild_global_index()
            
            # 保存到文件
            self.save_user_index(user_id)
            
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
    
    def clear_user_index(self, user_id: str) -> bool:
        """清除用户索引"""
        try:
            # 从内存中删除
            if user_id in self.hotword_embeddings:
                del self.hotword_embeddings[user_id]
            if user_id in self.hotword_metadata:
                del self.hotword_metadata[user_id]
                
            # 删除文件
            index_file = os.path.join(self.index_dir, f"user_{user_id}.index")
            metadata_file = os.path.join(self.index_dir, f"user_{user_id}.metadata")
            
            for file_path in [index_file, metadata_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            # 重建全局索引
            self._rebuild_global_index()
            
            logger.info(f"用户 {user_id} 的索引已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除用户索引失败: {str(e)}")
            return False
    
    def get_service_stats(self) -> Dict:
        """获取RAG服务统计信息"""
        try:
            total_users = len(self.hotword_metadata)
            total_hotwords = sum(len(meta.get('words', [])) for meta in self.hotword_metadata.values())
            
            return {
                'initialized': self.initialized,
                'model_name': settings.RAG_MODEL_NAME if self.initialized else None,
                'dimension': self.dimension if self.initialized else 0,
                'total_users_indexed': total_users,
                'total_hotwords': total_hotwords,
                'index_dir': self.index_dir,
                'memory_usage_mb': self._estimate_memory_usage()
            }
            
        except Exception as e:
            logger.error(f"获取服务统计失败: {str(e)}")
            return {'error': str(e)}
    
    def _estimate_memory_usage(self) -> float:
        """估算内存使用量（MB）"""
        try:
            total_size = 0
            
            # 估算嵌入向量的大小
            for embeddings in self.hotword_embeddings.values():
                if embeddings is not None:
                    total_size += embeddings.nbytes
                    
            # 估算元数据的大小
            for metadata in self.hotword_metadata.values():
                total_size += len(str(metadata).encode('utf-8'))
                
            return total_size / (1024 * 1024)  # 转换为MB
            
        except Exception as e:
            logger.error(f"估算内存使用量失败: {str(e)}")
            return 0.0

# 全局RAG服务实例
rag_service = RAGService()

def get_rag_service() -> RAGService:
    """获取RAG服务实例"""
    return rag_service 