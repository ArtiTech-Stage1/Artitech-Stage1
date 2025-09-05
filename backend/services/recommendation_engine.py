from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging
from collections import defaultdict
from datetime import datetime
import asyncio
from models.recommendation_models import (
    RecommendationRequest, RecommendationResponse, RecommendationContext,
    RecommendationItem, UserFeedback, RecommendationMetrics
)
from models.artwork_models import Artwork
from models.user_models import UserProfile
from services.advanced_rag_service import AdvancedRAGService

logger = logging.getLogger(__name__)

class ArtRecommendationBandit:
    """艺术品推荐多臂老虎机"""
    
    def __init__(self, exploration_rate: float = 0.1):
        self.arm_rewards = defaultdict(list)  # 每个艺术品的历史奖励
        self.exploration_rate = exploration_rate
        self.total_pulls = 0

    def select_recommendations(self, candidate_artworks: List[Artwork], 
                             user_context: Dict[str, Any]) -> List[Artwork]:
        """使用UCB算法选择推荐"""
        try:
            ucb_scores = {}
            
            for artwork in candidate_artworks:
                artwork_id = artwork.id
                rewards = self.arm_rewards[artwork_id]
                
                if not rewards:
                    # 未尝试过的艺术品给予最高优先级
                    ucb_scores[artwork_id] = float('inf')
                else:
                    # 计算UCB分数
                    mean_reward = np.mean(rewards)
                    confidence_interval = np.sqrt(
                        2 * np.log(self.total_pulls) / len(rewards)
                    )
                    ucb_scores[artwork_id] = mean_reward + confidence_interval
            
            # 选择top-k推荐
            sorted_artworks = sorted(
                candidate_artworks,
                key=lambda x: ucb_scores[x.id],
                reverse=True
            )
            
            return sorted_artworks[:5]  # 返回前5个推荐
            
        except Exception as e:
            logger.error(f"多臂老虎机选择失败: {e}")
            return candidate_artworks[:5]

    def update_reward(self, artwork_id: str, user_feedback: UserFeedback):
        """更新奖励信号"""
        try:
            # 将用户反馈转换为奖励分数
            reward_mapping = {
                'loved': 1.0,
                'liked': 0.7,
                'neutral': 0.3,
                'disliked': 0.1,
                'hated': 0.0
            }
            
            # 基于评分计算奖励
            if user_feedback.rating >= 4:
                reward = reward_mapping.get('loved', 1.0)
            elif user_feedback.rating >= 3:
                reward = reward_mapping.get('liked', 0.7)
            elif user_feedback.rating >= 2:
                reward = reward_mapping.get('neutral', 0.3)
            else:
                reward = reward_mapping.get('disliked', 0.1)
            
            self.arm_rewards[artwork_id].append(reward)
            self.total_pulls += 1
            
            logger.info(f"更新艺术品{artwork_id}的奖励: {reward}")
            
        except Exception as e:
            logger.error(f"更新奖励失败: {e}")

class DeepCollaborativeFiltering:
    """深度协同过滤（简化实现）"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.user_embeddings = {}  # 用户embedding缓存
        self.artwork_embeddings = {}  # 艺术品embedding缓存
        self.emotion_embeddings = {}  # 情感embedding缓存

    def predict_preference(self, user_id: str, artwork_id: str, 
                          emotion_state: str) -> float:
        """预测用户对艺术品的偏好概率"""
        try:
            # 获取或生成embedding
            user_emb = self._get_user_embedding(user_id)
            artwork_emb = self._get_artwork_embedding(artwork_id)
            emotion_emb = self._get_emotion_embedding(emotion_state)
            
            # 简化的相似度计算
            user_artwork_sim = self._cosine_similarity(user_emb, artwork_emb)
            user_emotion_sim = self._cosine_similarity(user_emb, emotion_emb)
            artwork_emotion_sim = self._cosine_similarity(artwork_emb, emotion_emb)
            
            # 综合偏好分数
            preference_score = (
                user_artwork_sim * 0.5 +
                user_emotion_sim * 0.3 +
                artwork_emotion_sim * 0.2
            )
            
            return max(0.0, min(1.0, preference_score))
            
        except Exception as e:
            logger.error(f"偏好预测失败: {e}")
            return 0.5

    def _get_user_embedding(self, user_id: str) -> np.ndarray:
        """获取用户embedding"""
        if user_id not in self.user_embeddings:
            # 生成随机embedding作为示例
            self.user_embeddings[user_id] = np.random.randn(self.embedding_dim)
        return self.user_embeddings[user_id]

    def _get_artwork_embedding(self, artwork_id: str) -> np.ndarray:
        """获取艺术品embedding"""
        if artwork_id not in self.artwork_embeddings:
            # 生成随机embedding作为示例
            self.artwork_embeddings[artwork_id] = np.random.randn(self.embedding_dim)
        return self.artwork_embeddings[artwork_id]

    def _get_emotion_embedding(self, emotion_state: str) -> np.ndarray:
        """获取情感embedding"""
        if emotion_state not in self.emotion_embeddings:
            # 生成随机embedding作为示例
            self.emotion_embeddings[emotion_state] = np.random.randn(self.embedding_dim)
        return self.emotion_embeddings[emotion_state]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

class HybridRecommendationEngine:
    """混合推荐引擎"""
    
    def __init__(self):
        self.rag_service = AdvancedRAGService()
        self.bandit = ArtRecommendationBandit()
        self.collaborative_filter = DeepCollaborativeFiltering()
        self.recommendation_history = defaultdict(list)
        self.user_metrics = defaultdict(lambda: RecommendationMetrics())

    async def generate_recommendations(self, request: RecommendationRequest, 
                                    context: RecommendationContext) -> RecommendationResponse:
        """生成混合推荐"""
        try:
            start_time = datetime.now()
            logger.info(f"开始为用户{request.user_id}生成推荐...")
            
            # 1. 内容过滤 (RAG检索)
            content_results = await self._content_based_filtering(request, context)
            
            # 2. 协同过滤
            collaborative_results = await self._collaborative_filtering(request.user_id, context)
            
            # 3. 情感驱动推荐
            emotion_results = await self._emotion_driven_recommendation(request, context)
            
            # 4. 混合融合
            final_recommendations = self._hybrid_fusion(
                content_results, collaborative_results, emotion_results, request
            )
            
            # 5. 多臂老虎机选择
            selected_recommendations = self.bandit.select_recommendations(
                [r['artwork'] for r in final_recommendations], context.dict()
            )
            
            # 6. 构建推荐响应
            response = self._build_recommendation_response(
                request, selected_recommendations, final_recommendations, start_time
            )
            
            # 7. 更新推荐历史
            self._update_recommendation_history(request.user_id, response)
            
            logger.info(f"推荐生成完成，耗时: {(datetime.now() - start_time).total_seconds():.2f}秒")
            
            return response
            
        except Exception as e:
            logger.error(f"推荐生成失败: {e}")
            return self._create_error_response(request, str(e))

    async def _content_based_filtering(self, request: RecommendationRequest, 
                                     context: RecommendationContext) -> List[Dict[str, Any]]:
        """基于内容的过滤"""
        try:
            # 使用RAG服务检索艺术品
            rag_results = await self.rag_service.retrieve_artworks(request, context)
            
            # 转换为推荐格式
            content_results = []
            for result in rag_results:
                content_results.append({
                    'artwork': result['artwork'],
                    'score': result.get('final_score', result.get('similarity', 0.5)),
                    'method': 'content_based',
                    'reasoning': f"基于语义相似度和视觉特征匹配，分数: {result.get('final_score', 0.5):.3f}"
                })
            
            return content_results
            
        except Exception as e:
            logger.error(f"内容过滤失败: {e}")
            return []

    async def _collaborative_filtering(self, user_id: str, 
                                     context: RecommendationContext) -> List[Dict[str, Any]]:
        """协同过滤推荐"""
        try:
            # 这里应该实现真正的协同过滤算法
            # 为了演示，我们返回一些模拟结果
            
            # 获取示例艺术品
            sample_artworks = self._get_sample_artworks()
            
            collaborative_results = []
            for artwork in sample_artworks:
                # 使用深度协同过滤预测偏好
                preference_score = self.collaborative_filter.predict_preference(
                    user_id, artwork.id, context.user_profile.get('current_mood', 'neutral')
                )
                
                collaborative_results.append({
                    'artwork': artwork,
                    'score': preference_score,
                    'method': 'collaborative',
                    'reasoning': f"基于相似用户的偏好模式，预测分数: {preference_score:.3f}"
                })
            
            # 按分数排序
            collaborative_results.sort(key=lambda x: x['score'], reverse=True)
            
            return collaborative_results[:10]  # 返回前10个
            
        except Exception as e:
            logger.error(f"协同过滤失败: {e}")
            return []

    async def _emotion_driven_recommendation(self, request: RecommendationRequest, 
                                           context: RecommendationContext) -> List[Dict[str, Any]]:
        """情感驱动推荐"""
        try:
            if not request.current_mood:
                return []
            
            # 获取示例艺术品
            sample_artworks = self._get_sample_artworks()
            
            emotion_results = []
            for artwork in sample_artworks:
                # 计算情感匹配度
                emotion_score = self._calculate_emotion_match(
                    request.current_mood, artwork
                )
                
                if emotion_score > 0.5:  # 情感匹配阈值
                    emotion_results.append({
                        'artwork': artwork,
                        'score': emotion_score,
                        'method': 'emotion_driven',
                        'reasoning': f"情感共鸣匹配，当前心情: {request.current_mood}，匹配度: {emotion_score:.3f}"
                    })
            
            # 按情感分数排序
            emotion_results.sort(key=lambda x: x['score'], reverse=True)
            
            return emotion_results[:5]  # 返回前5个
            
        except Exception as e:
            logger.error(f"情感驱动推荐失败: {e}")
            return []

    def _calculate_emotion_match(self, current_mood: str, artwork: Artwork) -> float:
        """计算情感匹配度"""
        if not artwork.mood_associations:
            return 0.0
        
        # 直接匹配
        if current_mood in artwork.mood_associations:
            return 0.9
        
        # 情感组匹配
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
        for artwork_mood in artwork.mood_associations:
            for group, moods in mood_groups.items():
                if artwork_mood in moods:
                    if group == current_group:
                        max_similarity = max(max_similarity, 0.7)
                    elif group == 'neutral':
                        max_similarity = max(max_similarity, 0.4)
                    else:
                        max_similarity = max(max_similarity, 0.2)
                    break
        
        return max_similarity

    def _hybrid_fusion(self, content_results: List[Dict[str, Any]], 
                       collaborative_results: List[Dict[str, Any]], 
                       emotion_results: List[Dict[str, Any]], 
                       request: RecommendationRequest) -> List[Dict[str, Any]]:
        """混合融合推荐结果"""
        try:
            # 创建艺术品ID到结果的映射
            artwork_scores = {}
            
            # 内容过滤权重 (60%)
            for result in content_results:
                artwork_id = result['artwork'].id
                artwork_scores[artwork_id] = {
                    'artwork': result['artwork'],
                    'content_score': result['score'] * 0.6,
                    'collaborative_score': 0.0,
                    'emotion_score': 0.0,
                    'final_score': result['score'] * 0.6,
                    'methods': [result['method']],
                    'reasoning': [result['reasoning']]
                }
            
            # 协同过滤权重 (30%)
            for result in collaborative_results:
                artwork_id = result['artwork'].id
                if artwork_id in artwork_scores:
                    artwork_scores[artwork_id]['collaborative_score'] = result['score'] * 0.3
                    artwork_scores[artwork_id]['final_score'] += result['score'] * 0.3
                    artwork_scores[artwork_id]['methods'].append(result['method'])
                    artwork_scores[artwork_id]['reasoning'].append(result['reasoning'])
                else:
                    artwork_scores[artwork_id] = {
                        'artwork': result['artwork'],
                        'content_score': 0.0,
                        'collaborative_score': result['score'] * 0.3,
                        'emotion_score': 0.0,
                        'final_score': result['score'] * 0.3,
                        'methods': [result['method']],
                        'reasoning': [result['reasoning']]
                    }
            
            # 情感驱动权重 (10%)
            for result in emotion_results:
                artwork_id = result['artwork'].id
                if artwork_id in artwork_scores:
                    artwork_scores[artwork_id]['emotion_score'] = result['score'] * 0.1
                    artwork_scores[artwork_id]['final_score'] += result['score'] * 0.1
                    artwork_scores[artwork_id]['methods'].append(result['method'])
                    artwork_scores[artwork_id]['reasoning'].append(result['reasoning'])
                else:
                    artwork_scores[artwork_id] = {
                        'artwork': result['artwork'],
                        'content_score': 0.0,
                        'collaborative_score': 0.0,
                        'emotion_score': result['score'] * 0.1,
                        'final_score': result['score'] * 0.1,
                        'methods': [result['method']],
                        'reasoning': [result['reasoning']]
                    }
            
            # 转换为列表并排序
            final_results = list(artwork_scores.values())
            final_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            return final_results
            
        except Exception as e:
            logger.error(f"混合融合失败: {e}")
            return content_results  # 返回内容过滤结果作为fallback

    def _build_recommendation_response(self, request: RecommendationRequest, 
                                     selected_artworks: List[Artwork], 
                                     all_results: List[Dict[str, Any]], 
                                     start_time: datetime) -> RecommendationResponse:
        """构建推荐响应"""
        try:
            # 构建推荐项目列表
            recommendations = []
            for artwork in selected_artworks:
                # 查找对应的结果信息
                result_info = next((r for r in all_results if r['artwork'].id == artwork.id), None)
                
                if result_info:
                    recommendation_item = RecommendationItem(
                        artwork_id=artwork.id,
                        title=artwork.title,
                        artist=artwork.artist,
                        match_score=result_info['final_score'],
                        match_reasons=result_info['reasoning'],
                        emotional_fit=result_info.get('emotion_score', 0.5),
                        visual_appeal=result_info.get('content_score', 0.5),
                        novelty_factor=result_info.get('collaborative_score', 0.5),
                        explanation="; ".join(result_info['reasoning'])
                    )
                else:
                    # 如果没有找到结果信息，创建默认推荐项目
                    recommendation_item = RecommendationItem(
                        artwork_id=artwork.id,
                        title=artwork.title,
                        artist=artwork.artist,
                        match_score=0.5,
                        match_reasons=["基于综合推荐算法"],
                        emotional_fit=0.5,
                        visual_appeal=0.5,
                        novelty_factor=0.5,
                        explanation="基于混合推荐算法的艺术品推荐"
                    )
                
                recommendations.append(recommendation_item.dict())
            
            # 构建响应
            response = RecommendationResponse(
                user_id=request.user_id,
                recommendations=recommendations,
                total_count=len(recommendations),
                confidence_score=0.85,  # 基于算法性能的置信度
                reasoning=f"基于内容过滤(60%)、协同过滤(30%)和情感驱动(10%)的混合推荐算法",
                alternative_suggestions=[
                    "尝试不同的艺术风格",
                    "探索新的艺术家作品",
                    "根据心情变化调整偏好"
                ],
                generated_at=datetime.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"构建推荐响应失败: {e}")
            return self._create_error_response(request, str(e))

    def _create_error_response(self, request: RecommendationRequest, error_message: str) -> RecommendationResponse:
        """创建错误响应"""
        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=[],
            total_count=0,
            confidence_score=0.0,
            reasoning=f"推荐生成失败: {error_message}",
            alternative_suggestions=["请稍后重试", "检查网络连接", "联系客服支持"],
            generated_at=datetime.now()
        )

    def _update_recommendation_history(self, user_id: str, response: RecommendationResponse):
        """更新推荐历史"""
        try:
            self.recommendation_history[user_id].append({
                'timestamp': response.generated_at,
                'recommendations': response.recommendations,
                'confidence_score': response.confidence_score
            })
            
            # 限制历史记录数量
            if len(self.recommendation_history[user_id]) > 100:
                self.recommendation_history[user_id] = self.recommendation_history[user_id][-50:]
                
        except Exception as e:
            logger.error(f"更新推荐历史失败: {e}")

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

    def record_user_feedback(self, user_id: str, feedback: UserFeedback):
        """记录用户反馈"""
        try:
            # 更新多臂老虎机
            self.bandit.update_reward(feedback.artwork_id, feedback)
            
            # 更新用户指标
            metrics = self.user_metrics[user_id]
            metrics.total_recommendations += 1
            
            if feedback.rating >= 4:
                metrics.accepted_recommendations += 1
            
            # 更新平均评分
            if metrics.total_recommendations > 0:
                total_rating = metrics.average_rating * (metrics.total_recommendations - 1) + feedback.rating
                metrics.average_rating = total_rating / metrics.total_recommendations
            
            logger.info(f"用户{user_id}的反馈已记录: {feedback.rating}/5")
            
        except Exception as e:
            logger.error(f"记录用户反馈失败: {e}")

    def get_user_recommendation_metrics(self, user_id: str) -> RecommendationMetrics:
        """获取用户推荐指标"""
        return self.user_metrics.get(user_id, RecommendationMetrics())

