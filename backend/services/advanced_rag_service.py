from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging
import asyncio
from models.artwork_models import Artwork, ArtworkEmbedding
from models.recommendation_models import RecommendationRequest, RecommendationContext

logger = logging.getLogger(__name__)

class HierarchicalRAG:
    """多级RAG检索架构"""
    
    def __init__(self):
        self.level1_retriever = SemanticRetriever()
        self.level2_retriever = VisualRetriever()
        self.level3_retriever = EmotionRetriever()
        self.level4_retriever = ContextRetriever()
        
        # 初始化embedding模型
        self.embedding_generator = DynamicEmbeddingGenerator()

    async def hierarchical_retrieve(self, query: RecommendationRequest, 
                                  user_context: RecommendationContext) -> List[Dict[str, Any]]:
        """分层检索艺术品"""
        try:
            # Level 1: 基础语义匹配
            logger.info("开始Level 1语义检索...")
            semantic_results = await self.level1_retriever.retrieve(query.query_text)
            
            if not semantic_results:
                logger.warning("语义检索未返回结果")
                return []

            # Level 2: 视觉特征过滤
            if query.preferred_colors or query.preferred_themes:
                logger.info("开始Level 2视觉特征过滤...")
                visual_results = await self.level2_retriever.filter(
                    semantic_results, query.preferred_colors, query.preferred_themes
                )
            else:
                visual_results = semantic_results

            # Level 3: 情感共鸣筛选
            if query.current_mood:
                logger.info("开始Level 3情感共鸣筛选...")
                emotion_results = await self.level3_retriever.rank_by_emotion(
                    visual_results, query.current_mood
                )
            else:
                emotion_results = visual_results

            # Level 4: 个人化上下文调整
            logger.info("开始Level 4个人化调整...")
            final_results = await self.level4_retriever.personalize(
                emotion_results, user_context
            )

            logger.info(f"分层检索完成，返回{len(final_results)}个结果")
            return final_results

        except Exception as e:
            logger.error(f"分层检索失败: {e}")
            return []

class SemanticRetriever:
    """语义检索器"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.artwork_embeddings = {}  # 缓存艺术品embedding

    async def retrieve(self, query_text: str) -> List[Dict[str, Any]]:
        """基于语义相似度的检索"""
        try:
            # 生成查询embedding
            query_embedding = self.model.encode(query_text)
            
            # 计算与所有艺术品的相似度
            similarities = []
            
            # 这里应该从数据库或缓存中获取艺术品数据
            # 为了演示，我们使用模拟数据
            artworks = self._get_sample_artworks()
            
            for artwork in artworks:
                # 获取或生成艺术品embedding
                artwork_embedding = await self._get_artwork_embedding(artwork)
                
                # 计算相似度
                similarity = cosine_similarity(
                    [query_embedding], [artwork_embedding]
                )[0][0]
                
                similarities.append({
                    'artwork': artwork,
                    'similarity': float(similarity),
                    'retrieval_method': 'semantic'
                })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 返回top-k结果
            return similarities[:20]
            
        except Exception as e:
            logger.error(f"语义检索失败: {e}")
            return []

    async def _get_artwork_embedding(self, artwork: Artwork) -> np.ndarray:
        """获取艺术品embedding"""
        artwork_id = artwork.id
        
        if artwork_id in self.artwork_embeddings:
            return self.artwork_embeddings[artwork_id]
        
        # 生成复合文本描述
        text_description = f"{artwork.title} {artwork.artist} {artwork.style} {artwork.description}"
        
        # 生成embedding
        embedding = self.model.encode(text_description)
        
        # 缓存结果
        self.artwork_embeddings[artwork_id] = embedding
        
        return embedding

    def _get_sample_artworks(self) -> List[Artwork]:
        """获取示例艺术品数据"""
        return [
            Artwork(
                id="A001",
                title="星夜",
                artist="梵高",
                style="后印象派",
                colors=["blue", "yellow", "white"],
                themes=["nature", "night", "movement"],
                mood_associations=["calm", "contemplative", "melancholic"],
                description="梵高的经典作品，蓝色和黄色的旋转星空，表达了艺术家内心的激情与宁静"
            ),
            Artwork(
                id="A002",
                title="睡莲",
                artist="莫奈",
                style="印象派",
                colors=["green", "blue", "pink", "white"],
                themes=["nature", "water", "peaceful"],
                mood_associations=["calm", "peaceful", "serene"],
                description="莫奈的睡莲系列作品，展现了水面的光影变化和自然的宁静美"
            ),
            Artwork(
                id="A003",
                title="呐喊",
                artist="蒙克",
                style="表现主义",
                colors=["red", "orange", "blue", "black"],
                themes=["emotion", "anxiety", "expression"],
                mood_associations=["anxious", "distressed", "intense"],
                description="蒙克的代表作，通过扭曲的线条和强烈的色彩表达了内心的焦虑和恐惧"
            )
        ]

class VisualRetriever:
    """视觉特征检索器"""
    
    async def filter(self, semantic_results: List[Dict[str, Any]], 
                    preferred_colors: List[str], preferred_themes: List[str]) -> List[Dict[str, Any]]:
        """基于视觉特征过滤"""
        try:
            filtered_results = []
            
            for result in semantic_results:
                artwork = result['artwork']
                visual_score = self._calculate_visual_score(
                    artwork, preferred_colors, preferred_themes
                )
                
                if visual_score > 0.3:  # 视觉匹配阈值
                    result['visual_score'] = visual_score
                    result['retrieval_method'] = 'semantic + visual'
                    filtered_results.append(result)
            
            # 按视觉分数重新排序
            filtered_results.sort(key=lambda x: x['visual_score'], reverse=True)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"视觉特征过滤失败: {e}")
            return semantic_results

    def _calculate_visual_score(self, artwork: Artwork, 
                               preferred_colors: List[str], 
                               preferred_themes: List[str]) -> float:
        """计算视觉匹配分数"""
        score = 0.0
        
        # 颜色匹配 (权重: 40%)
        if preferred_colors and artwork.colors:
            color_overlap = len(set(preferred_colors) & set(artwork.colors))
            color_score = color_overlap / max(len(preferred_colors), 1)
            score += color_score * 0.4
        
        # 主题匹配 (权重: 35%)
        if preferred_themes and artwork.themes:
            theme_overlap = len(set(preferred_themes) & set(artwork.themes))
            theme_score = theme_overlap / max(len(preferred_themes), 1)
            score += theme_score * 0.35
        
        # 风格匹配 (权重: 25%)
        if hasattr(artwork, 'style') and artwork.style:
            # 这里可以添加更复杂的风格匹配逻辑
            score += 0.25
        
        return score

class EmotionRetriever:
    """情感关联检索器"""
    
    async def rank_by_emotion(self, visual_results: List[Dict[str, Any]], 
                             current_mood: str) -> List[Dict[str, Any]]:
        """基于情感共鸣排序"""
        try:
            for result in visual_results:
                artwork = result['artwork']
                emotion_score = self._calculate_emotion_score(artwork, current_mood)
                result['emotion_score'] = emotion_score
                result['retrieval_method'] = 'semantic + visual + emotion'
            
            # 按情感分数重新排序
            visual_results.sort(key=lambda x: x['emotion_score'], reverse=True)
            
            return visual_results
            
        except Exception as e:
            logger.error(f"情感共鸣排序失败: {e}")
            return visual_results

    def _calculate_emotion_score(self, artwork: Artwork, current_mood: str) -> float:
        """计算情感共鸣分数"""
        if not artwork.mood_associations:
            return 0.5
        
        # 情感匹配度
        mood_match = 0.0
        if current_mood in artwork.mood_associations:
            mood_match = 1.0
        else:
            # 计算情感相似度
            mood_similarity = self._calculate_mood_similarity(current_mood, artwork.mood_associations)
            mood_match = mood_similarity
        
        # 情感强度
        intensity_score = 0.5
        if hasattr(artwork, 'emotional_impact'):
            intensity_mapping = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
            intensity_score = intensity_mapping.get(artwork.emotional_impact, 0.5)
        
        # 综合情感分数
        emotion_score = mood_match * 0.7 + intensity_score * 0.3
        
        return emotion_score

    def _calculate_mood_similarity(self, current_mood: str, artwork_moods: List[str]) -> float:
        """计算情感相似度"""
        # 简化的情感相似度计算
        mood_groups = {
            'positive': ['happy', 'excited', 'content', 'peaceful'],
            'negative': ['sad', 'anxious', 'angry', 'stressed'],
            'neutral': ['calm', 'contemplative', 'melancholic']
        }
        
        current_group = None
        for group, moods in mood_groups.items():
            if current_mood in moods:
                current_group = group
                break
        
        if not current_group:
            return 0.3
        
        # 计算与艺术品情感的相似度
        max_similarity = 0.0
        for artwork_mood in artwork_moods:
            for group, moods in mood_groups.items():
                if artwork_mood in moods:
                    if group == current_group:
                        max_similarity = max(max_similarity, 0.8)
                    elif group == 'neutral':
                        max_similarity = max(max_similarity, 0.5)
                    else:
                        max_similarity = max(max_similarity, 0.2)
                    break
        
        return max_similarity

class ContextRetriever:
    """上下文感知检索器"""
    
    async def personalize(self, emotion_results: List[Dict[str, Any]], 
                         user_context: RecommendationContext) -> List[Dict[str, Any]]:
        """个人化上下文调整"""
        try:
            for result in emotion_results:
                artwork = result['artwork']
                personalization_score = self._calculate_personalization_score(
                    artwork, user_context
                )
                result['personalization_score'] = personalization_score
                result['final_score'] = (
                    result.get('similarity', 0.5) * 0.3 +
                    result.get('visual_score', 0.5) * 0.25 +
                    result.get('emotion_score', 0.5) * 0.25 +
                    personalization_score * 0.2
                )
                result['retrieval_method'] = 'semantic + visual + emotion + personalization'
            
            # 按最终分数排序
            emotion_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            return emotion_results
            
        except Exception as e:
            logger.error(f"个人化调整失败: {e}")
            return emotion_results

    def _calculate_personalization_score(self, artwork: Artwork, 
                                       user_context: RecommendationContext) -> float:
        """计算个人化分数"""
        score = 0.5  # 基础分数
        
        user_profile = user_context.user_profile
        
        # 基于用户偏好的调整
        if user_profile:
            # 颜色偏好
            if 'color_preferences' in user_profile:
                color_score = self._calculate_preference_score(
                    artwork.colors, user_profile['color_preferences']
                )
                score += color_score * 0.2
            
            # 风格偏好
            if 'style_preferences' in user_profile:
                style_score = self._calculate_preference_score(
                    [artwork.style], user_profile['style_preferences']
                )
                score += style_score * 0.2
            
            # 主题偏好
            if 'theme_preferences' in user_profile:
                theme_score = self._calculate_preference_score(
                    artwork.themes, user_profile['theme_preferences']
                )
                score += theme_score * 0.1
        
        # 基于对话历史的调整
        conversation_history = user_context.conversation_history
        if conversation_history:
            # 分析对话中提到的偏好
            mentioned_preferences = self._extract_preferences_from_history(conversation_history)
            
            # 计算与当前艺术品的匹配度
            history_score = self._calculate_history_match_score(artwork, mentioned_preferences)
            score += history_score * 0.1
        
        return min(1.0, max(0.0, score))

    def _calculate_preference_score(self, artwork_features: List[str], 
                                  user_preferences: Dict[str, float]) -> float:
        """计算偏好匹配分数"""
        if not artwork_features or not user_preferences:
            return 0.0
        
        total_score = 0.0
        for feature in artwork_features:
            if feature in user_preferences:
                total_score += user_preferences[feature]
        
        return total_score / len(artwork_features) if artwork_features else 0.0

    def _extract_preferences_from_history(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从对话历史中提取偏好"""
        preferences = {
            'colors': [],
            'themes': [],
            'styles': [],
            'moods': []
        }
        
        for turn in conversation_history:
            if 'extracted_elements' in turn:
                elements = turn['extracted_elements']
                
                if 'colors' in elements:
                    preferences['colors'].extend(elements['colors'])
                if 'themes' in elements:
                    preferences['themes'].extend(elements['themes'])
                if 'styles' in elements:
                    preferences['styles'].extend(elements['styles'])
                if 'mood' in elements:
                    preferences['moods'].append(elements['mood'])
        
        return preferences

    def _calculate_history_match_score(self, artwork: Artwork, 
                                     mentioned_preferences: Dict[str, Any]) -> float:
        """计算与对话历史的匹配分数"""
        score = 0.0
        
        # 颜色匹配
        if mentioned_preferences.get('colors'):
            color_overlap = len(set(artwork.colors) & set(mentioned_preferences['colors']))
            if color_overlap > 0:
                score += 0.3
        
        # 主题匹配
        if mentioned_preferences.get('themes'):
            theme_overlap = len(set(artwork.themes) & set(mentioned_preferences['themes']))
            if theme_overlap > 0:
                score += 0.3
        
        # 风格匹配
        if mentioned_preferences.get('styles') and artwork.style in mentioned_preferences['styles']:
            score += 0.2
        
        # 情感匹配
        if mentioned_preferences.get('moods') and artwork.mood_associations:
            mood_overlap = len(set(artwork.mood_associations) & set(mentioned_preferences['moods']))
            if mood_overlap > 0:
                score += 0.2
        
        return score

class DynamicEmbeddingGenerator:
    """动态Embedding生成器"""
    
    def __init__(self):
        self.text_encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384  # all-MiniLM-L6-v2的维度

    def generate_composite_embedding(self, artwork: Artwork) -> np.ndarray:
        """生成复合嵌入向量"""
        try:
            # 文本描述嵌入
            text_description = f"{artwork.title} {artwork.artist} {artwork.style} {artwork.description}"
            text_emb = self.text_encoder.encode(text_description)
            
            # 情感特征嵌入（简化实现）
            emotion_text = " ".join(artwork.mood_associations) if artwork.mood_associations else "neutral"
            emotion_emb = self.text_encoder.encode(emotion_text)
            
            # 视觉特征嵌入（简化实现，使用颜色和主题）
            visual_text = " ".join(artwork.colors + artwork.themes)
            visual_emb = self.text_encoder.encode(visual_text)
            
            # 加权融合
            composite_emb = np.concatenate([
                text_emb * 0.4,
                emotion_emb * 0.35,
                visual_emb * 0.25
            ])
            
            return composite_emb
            
        except Exception as e:
            logger.error(f"生成复合embedding失败: {e}")
            # 返回零向量作为fallback
            return np.zeros(self.embedding_dimension)

class AdvancedRAGService:
    """高级RAG服务主类"""
    
    def __init__(self):
        self.hierarchical_rag = HierarchicalRAG()
        self.embedding_generator = DynamicEmbeddingGenerator()

    async def retrieve_artworks(self, request: RecommendationRequest, 
                              context: RecommendationContext) -> List[Dict[str, Any]]:
        """检索艺术品"""
        try:
            logger.info(f"开始为用户{request.user_id}检索艺术品...")
            
            # 执行分层检索
            results = await self.hierarchical_rag.hierarchical_retrieve(request, context)
            
            # 限制返回结果数量
            max_results = min(request.max_results, len(results))
            final_results = results[:max_results]
            
            logger.info(f"检索完成，返回{len(final_results)}个结果")
            
            return final_results
            
        except Exception as e:
            logger.error(f"艺术品检索失败: {e}")
            return []

    async def generate_artwork_embeddings(self, artworks: List[Artwork]) -> List[ArtworkEmbedding]:
        """为艺术品生成embedding"""
        try:
            embeddings = []
            
            for artwork in artworks:
                composite_emb = self.embedding_generator.generate_composite_embedding(artwork)
                
                embedding = ArtworkEmbedding(
                    artwork_id=artwork.id,
                    text_embedding=composite_emb[:128].tolist(),  # 简化处理
                    emotion_embedding=composite_emb[128:256].tolist(),
                    visual_embedding=composite_emb[256:].tolist(),
                    composite_embedding=composite_emb.tolist(),
                    embedding_dimension=len(composite_emb)
                )
                
                embeddings.append(embedding)
            
            logger.info(f"成功生成{len(embeddings)}个艺术品embedding")
            return embeddings
            
        except Exception as e:
            logger.error(f"生成艺术品embedding失败: {e}")
            return []

