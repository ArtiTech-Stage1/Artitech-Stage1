"""
艺术品检索引擎 - 粗排+精排
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import numpy as np
from datetime import datetime, timedelta

from database.config import get_db_manager
from .models import (
    Artwork, RecommendationRequest, RecommendationResponse, 
    RetrievalConfig, UserRecommendationProfile
)
from .embedding_service import get_embedding_service
from .tag_extractor import TagExtractor

logger = logging.getLogger(__name__)


class ArtworkRetrievalEngine:
    """艺术品检索引擎"""
    
    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        self.db_manager = None
        self.embedding_service = None
        self.tag_extractor = TagExtractor()
        
    async def initialize(self):
        """初始化检索引擎"""
        self.db_manager = get_db_manager()
        self.embedding_service = await get_embedding_service()
        logger.info("艺术品检索引擎初始化完成")
    
    async def retrieve_artworks(self, request: RecommendationRequest) -> RecommendationResponse:
        """检索艺术品 - 主入口"""
        try:
            logger.info(f"开始检索艺术品，用户ID: {request.user_id}")
            
            # 1. 检查缓存
            if request.use_cache and self.config.enable_cache:
                cached_result = await self._get_cached_recommendation(request)
                if cached_result:
                    logger.info("使用缓存结果")
                    return cached_result
            
            # 2. 获取用户推荐档案
            user_profile = await self._get_user_recommendation_profile(request.user_id)
            
            # 3. 粗排 - 获取候选艺术品
            coarse_candidates = await self._coarse_ranking(request, user_profile)
            
            if not coarse_candidates:
                logger.warning("粗排未找到候选艺术品")
                return RecommendationResponse(
                    artworks=[],
                    scores=[],
                    total_count=0,
                    has_more=False
                )
            
            # 4. 精排 - 重新排序和评分
            fine_ranked_results = await self._fine_ranking(
                coarse_candidates, request, user_profile
            )
            
            # 5. 分页和多样性处理
            final_results = await self._apply_pagination_and_diversity(
                fine_ranked_results, request
            )
            
            # 6. 构建响应
            response = await self._build_response(final_results, request)
            
            # 7. 缓存结果
            if self.config.enable_cache:
                await self._cache_recommendation(request, response)
            
            logger.info(f"检索完成，返回 {len(response.artworks)} 个结果")
            return response
            
        except Exception as e:
            logger.error(f"艺术品检索失败: {e}")
            return RecommendationResponse(
                artworks=[],
                scores=[],
                total_count=0,
                has_more=False
            )
    
    async def _coarse_ranking(self, request: RecommendationRequest, 
                            user_profile: UserRecommendationProfile) -> List[Dict[str, Any]]:
        """粗排 - 基于基础匹配和向量相似度"""
        try:
            candidates = []
            
            # 1. 文本搜索候选
            if self.config.use_text_search and request.query:
                text_candidates = await self._text_search(request.query, self.config.coarse_ranking_limit)
                candidates.extend(text_candidates)
            
            # 2. 向量搜索候选
            if self.config.use_vector_search:
                vector_candidates = await self._vector_search(request, user_profile, self.config.coarse_ranking_limit)
                candidates.extend(vector_candidates)
            
            # 3. 标签匹配候选
            tag_candidates = await self._tag_based_search(request, user_profile, self.config.coarse_ranking_limit)
            candidates.extend(tag_candidates)
            
            # 4. 去重和合并
            unique_candidates = self._deduplicate_candidates(candidates)
            
            # 5. 基础评分
            scored_candidates = await self._apply_coarse_scoring(unique_candidates, request, user_profile)
            
            # 6. 排序并限制数量
            scored_candidates.sort(key=lambda x: x['coarse_score'], reverse=True)
            
            return scored_candidates[:self.config.coarse_ranking_limit]
            
        except Exception as e:
            logger.error(f"粗排失败: {e}")
            return []
    
    async def _text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """基于文本的搜索"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                results = await conn.fetch("""
                    SELECT a.*, 
                           ts_rank(to_tsvector('english', a.title || ' ' || COALESCE(a.general_text_description, '')), 
                                  plainto_tsquery('english', $1)) as text_score
                    FROM artworks a
                    WHERE to_tsvector('english', a.title || ' ' || COALESCE(a.general_text_description, '')) 
                          @@ plainto_tsquery('english', $1)
                    ORDER BY text_score DESC
                    LIMIT $2
                """, query, limit)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            return []
    
    async def _vector_search(self, request: RecommendationRequest, 
                           user_profile: UserRecommendationProfile, limit: int) -> List[Dict[str, Any]]:
        """基于向量的搜索"""
        try:
            # 构建查询向量
            query_embedding = await self._build_query_embedding(request, user_profile)
            
            if not query_embedding:
                return []
            
            # 获取所有艺术品的嵌入向量
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                embeddings = await conn.fetch("""
                    SELECT a.*, ae.embedding_vector
                    FROM artworks a
                    JOIN artwork_embeddings ae ON a.id = ae.artwork_id
                    WHERE ae.embedding_type = 'combined'
                    ORDER BY a.popularity_score DESC
                    LIMIT $1
                """, limit * 3)  # 获取更多候选以提高质量
                
                # 计算相似度
                candidates = []
                for row in embeddings:
                    try:
                        embedding = json.loads(row['embedding_vector'])
                        similarity = self.embedding_service.calculate_similarity(
                            query_embedding, embedding
                        )
                        
                        if similarity >= self.config.similarity_threshold:
                            candidate = dict(row)
                            candidate['vector_score'] = similarity
                            candidates.append(candidate)
                            
                    except Exception as e:
                        logger.error(f"向量相似度计算失败: {e}")
                        continue
                
                # 按相似度排序
                candidates.sort(key=lambda x: x['vector_score'], reverse=True)
                return candidates[:limit]
                
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def _tag_based_search(self, request: RecommendationRequest, 
                              user_profile: UserRecommendationProfile, limit: int) -> List[Dict[str, Any]]:
        """基于标签的搜索"""
        try:
            # 构建标签查询条件
            tag_conditions = []
            params = []
            param_count = 0
            
            # 用户偏好标签
            if user_profile.preferred_colors:
                param_count += 1
                tag_conditions.append(f"color_tags && ${param_count}")
                params.append(user_profile.preferred_colors)
            
            if user_profile.preferred_styles:
                param_count += 1
                tag_conditions.append(f"style_tags && ${param_count}")
                params.append(user_profile.preferred_styles)
            
            if user_profile.preferred_themes:
                param_count += 1
                tag_conditions.append(f"theme_tags && ${param_count}")
                params.append(user_profile.preferred_themes)
            
            # 请求中的偏好
            if request.preferred_colors:
                param_count += 1
                tag_conditions.append(f"color_tags && ${param_count}")
                params.append(request.preferred_colors)
            
            if request.preferred_styles:
                param_count += 1
                tag_conditions.append(f"style_tags && ${param_count}")
                params.append(request.preferred_styles)
            
            if request.preferred_themes:
                param_count += 1
                tag_conditions.append(f"theme_tags && ${param_count}")
                params.append(request.preferred_themes)
            
            if not tag_conditions:
                return []
            
            # 构建查询
            where_clause = " OR ".join(tag_conditions)
            param_count += 1
            params.append(limit)
            
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                query = f"""
                    SELECT *, 
                           (CASE 
                            WHEN color_tags && $1 THEN 1 ELSE 0 END +
                            CASE WHEN style_tags && $2 THEN 1 ELSE 0 END +
                            CASE WHEN theme_tags && $3 THEN 1 ELSE 0 END) as tag_score
                    FROM artworks
                    WHERE {where_clause}
                    ORDER BY tag_score DESC, popularity_score DESC
                    LIMIT ${param_count}
                """
                
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"标签搜索失败: {e}")
            return []
    
    async def _fine_ranking(self, candidates: List[Dict[str, Any]], 
                          request: RecommendationRequest, 
                          user_profile: UserRecommendationProfile) -> List[Dict[str, Any]]:
        """精排 - 基于用户偏好和情感状态的深度排序"""
        try:
            scored_candidates = []
            
            for candidate in candidates:
                # 计算综合评分
                final_score = await self._calculate_fine_score(candidate, request, user_profile)
                
                candidate['fine_score'] = final_score
                scored_candidates.append(candidate)
            
            # 按精排评分排序
            scored_candidates.sort(key=lambda x: x['fine_score'], reverse=True)
            
            return scored_candidates[:self.config.fine_ranking_limit]
            
        except Exception as e:
            logger.error(f"精排失败: {e}")
            return candidates  # 返回原始候选
    
    async def _calculate_fine_score(self, candidate: Dict[str, Any], 
                                  request: RecommendationRequest, 
                                  user_profile: UserRecommendationProfile) -> float:
        """计算精排评分"""
        try:
            score = 0.0
            
            # 1. 用户偏好匹配评分
            preference_score = self._calculate_preference_score(candidate, user_profile)
            score += preference_score * self.config.user_preference_weight
            
            # 2. 情绪匹配评分
            mood_score = self._calculate_mood_score(candidate, request.mood)
            score += mood_score * self.config.mood_weight
            
            # 3. 流行度评分
            popularity_score = candidate.get('popularity_score', 0.0) / 5.0  # 归一化到0-1
            score += popularity_score * self.config.popularity_weight
            
            # 4. 质量评分
            quality_score = candidate.get('quality_score', 0.0) / 5.0  # 归一化到0-1
            score += quality_score * 0.1  # 质量权重
            
            # 5. 向量相似度评分
            vector_score = candidate.get('vector_score', 0.0)
            score += vector_score * 0.2  # 向量权重
            
            # 6. 文本相似度评分
            text_score = candidate.get('text_score', 0.0)
            if text_score > 0:
                score += min(text_score, 1.0) * 0.1  # 文本权重
            
            return score
            
        except Exception as e:
            logger.error(f"精排评分计算失败: {e}")
            return 0.0
    
    def _calculate_preference_score(self, candidate: Dict[str, Any], 
                                  user_profile: UserRecommendationProfile) -> float:
        """计算用户偏好匹配评分"""
        try:
            score = 0.0
            total_weight = 0.0
            
            # 颜色偏好匹配
            if user_profile.preferred_colors:
                color_tags = candidate.get('color_tags', [])
                color_match = len(set(color_tags) & set(user_profile.preferred_colors))
                if color_match > 0:
                    score += color_match / len(user_profile.preferred_colors)
                    total_weight += 1.0
            
            # 风格偏好匹配
            if user_profile.preferred_styles:
                style_tags = candidate.get('style_tags', [])
                style_match = len(set(style_tags) & set(user_profile.preferred_styles))
                if style_match > 0:
                    score += style_match / len(user_profile.preferred_styles)
                    total_weight += 1.0
            
            # 主题偏好匹配
            if user_profile.preferred_themes:
                theme_tags = candidate.get('theme_tags', [])
                theme_match = len(set(theme_tags) & set(user_profile.preferred_themes))
                if theme_match > 0:
                    score += theme_match / len(user_profile.preferred_themes)
                    total_weight += 1.0
            
            # 艺术家偏好匹配
            if user_profile.preferred_artists:
                artist = candidate.get('artist_display_name', '').lower()
                if any(pref_artist.lower() in artist for pref_artist in user_profile.preferred_artists):
                    score += 1.0
                    total_weight += 1.0
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"偏好评分计算失败: {e}")
            return 0.0
    
    def _calculate_mood_score(self, candidate: Dict[str, Any], mood: Optional[str]) -> float:
        """计算情绪匹配评分"""
        try:
            if not mood:
                return 0.5  # 中性评分
            
            emotion_tags = candidate.get('emotion_tags', [])
            
            # 情绪映射
            mood_emotion_mapping = {
                'happy': ['joyful', 'energetic', 'peaceful'],
                'sad': ['melancholic', 'contemplative', 'nostalgic'],
                'excited': ['energetic', 'dramatic', 'joyful'],
                'calm': ['peaceful', 'contemplative', 'serene'],
                'anxious': ['dramatic', 'mysterious', 'intense'],
                'angry': ['dramatic', 'intense', 'powerful'],
                'content': ['peaceful', 'joyful', 'serene'],
                'lonely': ['melancholic', 'contemplative', 'nostalgic']
            }
            
            target_emotions = mood_emotion_mapping.get(mood.lower(), [])
            if not target_emotions:
                return 0.5
            
            # 计算匹配度
            matches = len(set(emotion_tags) & set(target_emotions))
            return matches / len(target_emotions) if target_emotions else 0.0
            
        except Exception as e:
            logger.error(f"情绪评分计算失败: {e}")
            return 0.0

    async def _build_query_embedding(self, request: RecommendationRequest,
                                   user_profile: UserRecommendationProfile) -> Optional[List[float]]:
        """构建查询嵌入向量"""
        try:
            query_texts = []

            # 添加查询文本
            if request.query:
                query_texts.append(request.query)

            # 添加用户偏好
            if user_profile.preferred_styles:
                query_texts.append(" ".join(user_profile.preferred_styles))

            if user_profile.preferred_themes:
                query_texts.append(" ".join(user_profile.preferred_themes))

            if request.mood:
                query_texts.append(request.mood)

            if not query_texts:
                return None

            # 组合查询文本
            combined_query = " ".join(query_texts)

            # 生成嵌入向量
            return await self.embedding_service.encode_text(combined_query)

        except Exception as e:
            logger.error(f"查询嵌入构建失败: {e}")
            return None

    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重候选艺术品"""
        seen_ids = set()
        unique_candidates = []

        for candidate in candidates:
            artwork_id = candidate.get('id')
            if artwork_id and artwork_id not in seen_ids:
                seen_ids.add(artwork_id)
                unique_candidates.append(candidate)

        return unique_candidates

    async def _apply_coarse_scoring(self, candidates: List[Dict[str, Any]],
                                  request: RecommendationRequest,
                                  user_profile: UserRecommendationProfile) -> List[Dict[str, Any]]:
        """应用粗排评分"""
        for candidate in candidates:
            score = 0.0

            # 文本匹配评分
            text_score = candidate.get('text_score', 0.0)
            if text_score > 0:
                score += text_score * self.config.text_search_weight

            # 向量匹配评分
            vector_score = candidate.get('vector_score', 0.0)
            score += vector_score * self.config.vector_search_weight

            # 标签匹配评分
            tag_score = candidate.get('tag_score', 0.0)
            score += tag_score * 0.3

            # 流行度评分
            popularity_score = candidate.get('popularity_score', 0.0) / 5.0
            score += popularity_score * 0.2

            candidate['coarse_score'] = score

        return candidates

    async def _apply_pagination_and_diversity(self, candidates: List[Dict[str, Any]],
                                            request: RecommendationRequest) -> List[Dict[str, Any]]:
        """应用分页和多样性处理"""
        try:
            # 应用多样性过滤
            diverse_candidates = self._apply_diversity_filter(candidates)

            # 分页
            start_idx = request.offset
            end_idx = start_idx + request.limit

            return diverse_candidates[start_idx:end_idx]

        except Exception as e:
            logger.error(f"分页和多样性处理失败: {e}")
            return candidates[:request.limit]

    def _apply_diversity_filter(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用多样性过滤"""
        try:
            diverse_results = []
            artist_count = {}
            style_count = {}

            for candidate in candidates:
                artist = candidate.get('artist_display_name', 'Unknown')
                styles = candidate.get('style_tags', [])

                # 检查艺术家多样性
                if artist_count.get(artist, 0) >= self.config.max_same_artist:
                    continue

                # 检查风格多样性
                style_conflict = False
                for style in styles:
                    if style_count.get(style, 0) >= self.config.max_same_style:
                        style_conflict = True
                        break

                if style_conflict:
                    continue

                # 添加到结果
                diverse_results.append(candidate)

                # 更新计数
                artist_count[artist] = artist_count.get(artist, 0) + 1
                for style in styles:
                    style_count[style] = style_count.get(style, 0) + 1

            return diverse_results

        except Exception as e:
            logger.error(f"多样性过滤失败: {e}")
            return candidates

    async def _build_response(self, candidates: List[Dict[str, Any]],
                            request: RecommendationRequest) -> RecommendationResponse:
        """构建响应"""
        try:
            artworks = []
            scores = []

            for candidate in candidates:
                # 转换为Artwork对象
                artwork = Artwork(
                    id=candidate.get('id'),
                    object_id=candidate.get('object_id'),
                    title=candidate.get('title'),
                    object_name=candidate.get('object_name'),
                    department=candidate.get('department'),
                    culture=candidate.get('culture'),
                    period=candidate.get('period'),
                    artist_display_name=candidate.get('artist_display_name'),
                    medium=candidate.get('medium'),
                    dimensions=candidate.get('dimensions'),
                    classification=candidate.get('classification'),
                    object_date=candidate.get('object_date'),
                    general_text_description=candidate.get('general_text_description'),
                    url=candidate.get('url'),
                    color_tags=candidate.get('color_tags', []),
                    style_tags=candidate.get('style_tags', []),
                    theme_tags=candidate.get('theme_tags', []),
                    emotion_tags=candidate.get('emotion_tags', []),
                    popularity_score=candidate.get('popularity_score', 0.0),
                    quality_score=candidate.get('quality_score', 0.0),
                    created_at=candidate.get('created_at'),
                    updated_at=candidate.get('updated_at')
                )

                artworks.append(artwork)
                scores.append(candidate.get('fine_score', 0.0))

            # 计算总数和是否有更多
            total_count = await self._get_total_count(request)
            has_more = (request.offset + len(artworks)) < total_count

            return RecommendationResponse(
                artworks=artworks,
                scores=scores,
                total_count=total_count,
                has_more=has_more
            )

        except Exception as e:
            logger.error(f"响应构建失败: {e}")
            return RecommendationResponse(
                artworks=[],
                scores=[],
                total_count=0,
                has_more=False
            )

    async def _get_total_count(self, request: RecommendationRequest) -> int:
        """获取总数量"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM artworks")
                return result or 0

        except Exception as e:
            logger.error(f"获取总数失败: {e}")
            return 0

    async def _get_user_recommendation_profile(self, user_id: UUID) -> UserRecommendationProfile:
        """获取用户推荐档案"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                # 获取用户偏好
                preferences = await conn.fetch("""
                    SELECT preference_type, preference_value, weight
                    FROM user_preferences
                    WHERE user_id = $1
                """, user_id)

                # 分类偏好
                preferred_colors = []
                preferred_styles = []
                preferred_themes = []

                for pref in preferences:
                    pref_type = pref['preference_type']
                    pref_value = pref['preference_value']

                    if pref_type == 'color':
                        preferred_colors.append(pref_value)
                    elif pref_type == 'style':
                        preferred_styles.append(pref_value)
                    elif pref_type == 'theme':
                        preferred_themes.append(pref_value)

                # 获取交互历史（简化版）
                interactions = await conn.fetch("""
                    SELECT artwork_id, interaction_type, interaction_score
                    FROM artwork_user_interactions
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 100
                """, user_id)

                # 分析偏好艺术家（基于交互历史）
                preferred_artists = []
                if interactions:
                    artist_scores = {}
                    for interaction in interactions:
                        if interaction['interaction_type'] in ['like', 'save']:
                            # 获取艺术品的艺术家
                            artwork = await conn.fetchrow("""
                                SELECT artist_display_name
                                FROM artworks
                                WHERE id = $1
                            """, interaction['artwork_id'])

                            if artwork and artwork['artist_display_name']:
                                artist = artwork['artist_display_name']
                                artist_scores[artist] = artist_scores.get(artist, 0) + interaction['interaction_score']

                    # 选择评分最高的艺术家
                    preferred_artists = sorted(artist_scores.keys(),
                                             key=lambda x: artist_scores[x],
                                             reverse=True)[:5]

                return UserRecommendationProfile(
                    user_id=user_id,
                    preferred_colors=preferred_colors,
                    preferred_styles=preferred_styles,
                    preferred_themes=preferred_themes,
                    preferred_artists=preferred_artists,
                    preferred_cultures=[],
                    preferred_periods=[],
                    disliked_styles=[],
                    interaction_history=[],
                    recommendation_feedback={}
                )

        except Exception as e:
            logger.error(f"获取用户推荐档案失败: {e}")
            return UserRecommendationProfile(
                user_id=user_id,
                preferred_colors=[],
                preferred_styles=[],
                preferred_themes=[],
                preferred_artists=[],
                preferred_cultures=[],
                preferred_periods=[],
                disliked_styles=[],
                interaction_history=[],
                recommendation_feedback={}
            )

    async def _get_cached_recommendation(self, request: RecommendationRequest) -> Optional[RecommendationResponse]:
        """获取缓存的推荐结果"""
        try:
            cache_key = self._generate_cache_key(request)

            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                cached = await conn.fetchrow("""
                    SELECT artwork_ids, scores, query_context
                    FROM artwork_recommendation_cache
                    WHERE user_id = $1 AND cache_key = $2 AND expires_at > $3
                """, request.user_id, cache_key, datetime.utcnow())

                if not cached:
                    return None

                # 获取艺术品详情
                artwork_ids = json.loads(cached['artwork_ids'])
                scores = json.loads(cached['scores'])

                artworks = []
                for artwork_id in artwork_ids:
                    artwork_data = await conn.fetchrow("""
                        SELECT * FROM artworks WHERE id = $1
                    """, artwork_id)

                    if artwork_data:
                        artwork = Artwork(**dict(artwork_data))
                        artworks.append(artwork)

                return RecommendationResponse(
                    artworks=artworks,
                    scores=scores,
                    total_count=len(artworks),
                    has_more=False,
                    cache_used=True
                )

        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None

    async def _cache_recommendation(self, request: RecommendationRequest,
                                  response: RecommendationResponse):
        """缓存推荐结果"""
        try:
            cache_key = self._generate_cache_key(request)
            artwork_ids = [str(artwork.id) for artwork in response.artworks]
            expires_at = datetime.utcnow() + timedelta(hours=self.config.cache_ttl_hours)

            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                await conn.execute("""
                    INSERT INTO artwork_recommendation_cache
                    (user_id, cache_key, artwork_ids, scores, query_context, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (user_id, cache_key)
                    DO UPDATE SET
                        artwork_ids = EXCLUDED.artwork_ids,
                        scores = EXCLUDED.scores,
                        query_context = EXCLUDED.query_context,
                        expires_at = EXCLUDED.expires_at
                """,
                    request.user_id,
                    cache_key,
                    json.dumps(artwork_ids),
                    json.dumps(response.scores),
                    json.dumps(request.dict()),
                    expires_at
                )

        except Exception as e:
            logger.error(f"缓存推荐失败: {e}")

    def _generate_cache_key(self, request: RecommendationRequest) -> str:
        """生成缓存键"""
        key_parts = [
            request.query or "",
            request.mood or "",
            ",".join(sorted(request.preferred_colors)),
            ",".join(sorted(request.preferred_styles)),
            ",".join(sorted(request.preferred_themes)),
            str(request.limit),
            str(request.offset)
        ]

        return hash("|".join(key_parts)).__str__()
