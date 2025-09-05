"""
嵌入向量服务
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入向量服务"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.embedding_cache = {}
        
    async def initialize(self):
        """初始化模型"""
        try:
            logger.info(f"正在加载嵌入模型: {self.model_name}")
            
            # 在线程池中加载模型，避免阻塞
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor, 
                self._load_model
            )
            
            logger.info("嵌入模型加载完成")
            
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {e}")
            raise
    
    def _load_model(self) -> SentenceTransformer:
        """加载SentenceTransformer模型"""
        return SentenceTransformer(self.model_name)
    
    async def encode_text(self, text: str) -> List[float]:
        """将文本编码为向量"""
        if not text or not text.strip():
            return [0.0] * 384  # 返回零向量
        
        # 检查缓存
        cache_key = hash(text.strip())
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            # 在线程池中执行编码
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._encode_single_text,
                text.strip()
            )
            
            # 缓存结果
            self.embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            return [0.0] * 384  # 返回零向量
    
    def _encode_single_text(self, text: str) -> List[float]:
        """编码单个文本"""
        if not self.model:
            raise RuntimeError("模型未初始化")
        
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        if not texts:
            return []
        
        try:
            # 在线程池中执行批量编码
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._encode_batch_texts,
                texts
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"批量编码失败: {e}")
            return [[0.0] * 384] * len(texts)
    
    def _encode_batch_texts(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        if not self.model:
            raise RuntimeError("模型未初始化")
        
        # 过滤空文本
        valid_texts = [text.strip() if text else "" for text in texts]
        
        embeddings = self.model.encode(valid_texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def calculate_batch_similarity(self, query_embedding: List[float], 
                                 candidate_embeddings: List[List[float]]) -> List[float]:
        """计算查询向量与候选向量列表的相似度"""
        try:
            query_vec = np.array(query_embedding)
            candidate_vecs = np.array(candidate_embeddings)
            
            # 批量计算余弦相似度
            dot_products = np.dot(candidate_vecs, query_vec)
            query_norm = np.linalg.norm(query_vec)
            candidate_norms = np.linalg.norm(candidate_vecs, axis=1)
            
            # 避免除零
            valid_mask = (candidate_norms != 0) & (query_norm != 0)
            similarities = np.zeros(len(candidate_embeddings))
            
            if query_norm != 0:
                similarities[valid_mask] = dot_products[valid_mask] / (
                    query_norm * candidate_norms[valid_mask]
                )
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"批量相似度计算失败: {e}")
            return [0.0] * len(candidate_embeddings)
    
    async def find_similar_embeddings(self, query_embedding: List[float], 
                                    candidate_embeddings: List[Dict[str, Any]], 
                                    top_k: int = 10, 
                                    threshold: float = 0.5) -> List[Dict[str, Any]]:
        """找到最相似的嵌入向量"""
        try:
            if not candidate_embeddings:
                return []
            
            # 提取候选向量
            vectors = [item['embedding'] for item in candidate_embeddings]
            
            # 计算相似度
            similarities = self.calculate_batch_similarity(query_embedding, vectors)
            
            # 组合结果
            results = []
            for i, (item, similarity) in enumerate(zip(candidate_embeddings, similarities)):
                if similarity >= threshold:
                    result = item.copy()
                    result['similarity'] = similarity
                    results.append(result)
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"相似向量查找失败: {e}")
            return []
    
    def create_weighted_embedding(self, embeddings: List[List[float]], 
                                weights: List[float]) -> List[float]:
        """创建加权嵌入向量"""
        try:
            if not embeddings or not weights or len(embeddings) != len(weights):
                return [0.0] * 384
            
            embeddings_array = np.array(embeddings)
            weights_array = np.array(weights)
            
            # 归一化权重
            weights_sum = np.sum(weights_array)
            if weights_sum > 0:
                weights_array = weights_array / weights_sum
            
            # 计算加权平均
            weighted_embedding = np.average(embeddings_array, axis=0, weights=weights_array)
            
            return weighted_embedding.tolist()
            
        except Exception as e:
            logger.error(f"加权嵌入创建失败: {e}")
            return [0.0] * 384
    
    def embedding_to_json(self, embedding: List[float]) -> str:
        """将嵌入向量转换为JSON字符串"""
        return json.dumps(embedding)
    
    def json_to_embedding(self, json_str: str) -> List[float]:
        """将JSON字符串转换为嵌入向量"""
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"JSON转换失败: {e}")
            return [0.0] * 384
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return 384  # all-MiniLM-L6-v2的维度
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
            
            # 清理缓存
            self.embedding_cache.clear()
            
            logger.info("嵌入服务资源清理完成")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")


# 全局嵌入服务实例
_embedding_service = None

async def get_embedding_service() -> EmbeddingService:
    """获取全局嵌入服务实例"""
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        await _embedding_service.initialize()
    
    return _embedding_service

async def cleanup_embedding_service():
    """清理全局嵌入服务"""
    global _embedding_service
    
    if _embedding_service:
        await _embedding_service.cleanup()
        _embedding_service = None
