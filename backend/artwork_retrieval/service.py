"""
艺术品检索服务
"""

import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from database.config import get_db_manager
from .models import (
    Artwork, SearchRequest, SearchResponse, ArtworkStats,
    ArtworkUserInteraction
)

logger = logging.getLogger(__name__)


class ArtworkRetrievalService:
    """艺术品检索服务"""
    
    def __init__(self):
        self.db_manager = None
        
    async def initialize(self):
        """初始化服务"""
        self.db_manager = get_db_manager()
        logger.info("艺术品检索服务初始化完成")
    
    async def search_artworks(self, request: SearchRequest) -> SearchResponse:
        """搜索艺术品"""
        try:
            start_time = datetime.now()
            
            # 构建查询条件
            where_conditions = []
            params = []
            param_count = 0
            
            # 文本搜索
            if request.query:
                param_count += 1
                where_conditions.append(f"""
                    (to_tsvector('english', title || ' ' || COALESCE(general_text_description, '') || ' ' || COALESCE(artist_display_name, '')) 
                     @@ plainto_tsquery('english', ${param_count}))
                """)
                params.append(request.query)
            
            # 过滤条件
            if request.filters:
                if request.filters.get('department'):
                    param_count += 1
                    where_conditions.append(f"department ILIKE ${param_count}")
                    params.append(f"%{request.filters['department']}%")
                
                if request.filters.get('culture'):
                    param_count += 1
                    where_conditions.append(f"culture ILIKE ${param_count}")
                    params.append(f"%{request.filters['culture']}%")
                
                if request.filters.get('artist'):
                    param_count += 1
                    where_conditions.append(f"artist_display_name ILIKE ${param_count}")
                    params.append(f"%{request.filters['artist']}%")
            
            # 构建WHERE子句
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 构建ORDER BY子句
            order_clause = self._build_order_clause(request.sort_by, request.sort_order)
            
            # 添加分页参数
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            params.extend([request.limit, request.offset])
            
            # 执行查询
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                # 获取结果
                query = f"""
                    SELECT * FROM artworks
                    {where_clause}
                    {order_clause}
                    LIMIT ${limit_param} OFFSET ${offset_param}
                """
                
                results = await conn.fetch(query, *params)
                
                # 获取总数
                count_query = f"SELECT COUNT(*) FROM artworks {where_clause}"
                total_count = await conn.fetchval(count_query, *params[:-2])  # 排除limit和offset参数
                
                # 转换为Artwork对象
                artworks = [self._row_to_artwork(row) for row in results]
                
                # 计算搜索时间
                search_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return SearchResponse(
                    artworks=artworks,
                    total_count=total_count or 0,
                    has_more=(request.offset + len(artworks)) < (total_count or 0),
                    search_time_ms=search_time
                )
                
        except Exception as e:
            logger.error(f"搜索艺术品失败: {e}")
            return SearchResponse(
                artworks=[],
                total_count=0,
                has_more=False,
                search_time_ms=0.0
            )
    
    def _build_order_clause(self, sort_by: str, sort_order: str) -> str:
        """构建排序子句"""
        order_mapping = {
            'relevance': 'popularity_score',
            'popularity': 'popularity_score',
            'date': 'created_at',
            'title': 'title',
            'artist': 'artist_display_name'
        }
        
        column = order_mapping.get(sort_by, 'popularity_score')
        direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        return f"ORDER BY {column} {direction}"
    
    async def get_artwork_by_id(self, artwork_id: UUID) -> Optional[Artwork]:
        """根据ID获取艺术品"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                result = await conn.fetchrow(
                    "SELECT * FROM artworks WHERE id = $1",
                    artwork_id
                )
                
                if result:
                    return self._row_to_artwork(result)
                return None
                
        except Exception as e:
            logger.error(f"获取艺术品失败: {e}")
            return None
    
    async def get_similar_artworks(self, artwork_id: UUID, limit: int = 10) -> List[Artwork]:
        """获取相似艺术品"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                # 首先获取目标艺术品的信息
                target_artwork = await conn.fetchrow(
                    "SELECT * FROM artworks WHERE id = $1",
                    artwork_id
                )
                
                if not target_artwork:
                    return []
                
                # 基于标签相似度查找相似艺术品
                similar_results = await conn.fetch("""
                    SELECT a.*, 
                           (CASE WHEN a.color_tags && $2 THEN 1 ELSE 0 END +
                            CASE WHEN a.style_tags && $3 THEN 1 ELSE 0 END +
                            CASE WHEN a.theme_tags && $4 THEN 1 ELSE 0 END +
                            CASE WHEN a.artist_display_name = $5 THEN 2 ELSE 0 END +
                            CASE WHEN a.culture = $6 THEN 1 ELSE 0 END) as similarity_score
                    FROM artworks a
                    WHERE a.id != $1
                    AND (a.color_tags && $2 OR a.style_tags && $3 OR a.theme_tags && $4 
                         OR a.artist_display_name = $5 OR a.culture = $6)
                    ORDER BY similarity_score DESC, a.popularity_score DESC
                    LIMIT $7
                """, 
                    artwork_id,
                    target_artwork['color_tags'] or [],
                    target_artwork['style_tags'] or [],
                    target_artwork['theme_tags'] or [],
                    target_artwork['artist_display_name'],
                    target_artwork['culture'],
                    limit
                )
                
                return [self._row_to_artwork(row) for row in similar_results]
                
        except Exception as e:
            logger.error(f"获取相似艺术品失败: {e}")
            return []
    
    async def get_popular_artworks(self, limit: int = 20) -> List[Artwork]:
        """获取热门艺术品"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                results = await conn.fetch("""
                    SELECT * FROM artworks
                    ORDER BY popularity_score DESC, quality_score DESC
                    LIMIT $1
                """, limit)
                
                return [self._row_to_artwork(row) for row in results]
                
        except Exception as e:
            logger.error(f"获取热门艺术品失败: {e}")
            return []
    
    async def get_recent_artworks(self, limit: int = 20) -> List[Artwork]:
        """获取最新添加的艺术品"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                results = await conn.fetch("""
                    SELECT * FROM artworks
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
                
                return [self._row_to_artwork(row) for row in results]
                
        except Exception as e:
            logger.error(f"获取最新艺术品失败: {e}")
            return []
    
    async def get_artwork_stats(self) -> ArtworkStats:
        """获取艺术品统计信息"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                # 基础统计
                basic_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_artworks,
                        COUNT(DISTINCT artist_display_name) as total_artists,
                        COUNT(DISTINCT culture) as total_cultures,
                        COUNT(DISTINCT department) as total_departments
                    FROM artworks
                    WHERE artist_display_name IS NOT NULL
                """)
                
                # 热门风格统计
                popular_styles = await conn.fetch("""
                    SELECT unnest(style_tags) as style, COUNT(*) as count
                    FROM artworks
                    WHERE style_tags IS NOT NULL AND array_length(style_tags, 1) > 0
                    GROUP BY style
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                # 热门主题统计
                popular_themes = await conn.fetch("""
                    SELECT unnest(theme_tags) as theme, COUNT(*) as count
                    FROM artworks
                    WHERE theme_tags IS NOT NULL AND array_length(theme_tags, 1) > 0
                    GROUP BY theme
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                # 最近添加数量（过去7天）
                recent_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM artworks
                    WHERE created_at >= $1
                """, datetime.now() - timedelta(days=7))
                
                return ArtworkStats(
                    total_artworks=basic_stats['total_artworks'] or 0,
                    total_artists=basic_stats['total_artists'] or 0,
                    total_cultures=basic_stats['total_cultures'] or 0,
                    total_departments=basic_stats['total_departments'] or 0,
                    popular_styles=[
                        {"name": row['style'], "count": row['count']} 
                        for row in popular_styles
                    ],
                    popular_themes=[
                        {"name": row['theme'], "count": row['count']} 
                        for row in popular_themes
                    ],
                    recent_additions=recent_count or 0
                )
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return ArtworkStats(
                total_artworks=0,
                total_artists=0,
                total_cultures=0,
                total_departments=0,
                popular_styles=[],
                popular_themes=[],
                recent_additions=0
            )
    
    async def log_artwork_interaction(self, user_id: UUID, artwork_id: UUID, 
                                    interaction_type: str, interaction_score: float = 1.0,
                                    context: Optional[Dict[str, Any]] = None):
        """记录用户与艺术品的交互"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                await conn.execute("""
                    INSERT INTO artwork_user_interactions 
                    (user_id, artwork_id, interaction_type, interaction_score, context)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, artwork_id, interaction_type)
                    DO UPDATE SET 
                        interaction_score = EXCLUDED.interaction_score,
                        context = EXCLUDED.context,
                        created_at = CURRENT_TIMESTAMP
                """, user_id, artwork_id, interaction_type, interaction_score, 
                    json.dumps(context) if context else None)
                
                # 更新艺术品流行度评分
                await self._update_artwork_popularity(conn, artwork_id, interaction_type, interaction_score)
                
        except Exception as e:
            logger.error(f"记录交互失败: {e}")
    
    async def _update_artwork_popularity(self, conn, artwork_id: UUID, 
                                       interaction_type: str, interaction_score: float):
        """更新艺术品流行度评分"""
        try:
            # 根据交互类型计算权重
            interaction_weights = {
                'view': 0.1,
                'like': 0.5,
                'dislike': -0.3,
                'save': 0.7,
                'share': 0.8,
                'recommendation': 0.05
            }
            
            weight = interaction_weights.get(interaction_type, 0.1)
            score_delta = weight * interaction_score
            
            # 更新流行度评分
            await conn.execute("""
                UPDATE artworks 
                SET popularity_score = GREATEST(0, LEAST(5, popularity_score + $2))
                WHERE id = $1
            """, artwork_id, score_delta)
            
        except Exception as e:
            logger.error(f"更新流行度评分失败: {e}")
    
    def _row_to_artwork(self, row) -> Artwork:
        """将数据库行转换为Artwork对象"""
        return Artwork(
            id=row['id'],
            object_id=row['object_id'],
            title=row['title'],
            object_name=row['object_name'],
            department=row['department'],
            culture=row['culture'],
            period=row['period'],
            artist_display_name=row['artist_display_name'],
            medium=row['medium'],
            dimensions=row['dimensions'],
            classification=row['classification'],
            object_date=row['object_date'],
            general_text_description=row['general_text_description'],
            url=row['url'],
            color_tags=row['color_tags'] or [],
            style_tags=row['style_tags'] or [],
            theme_tags=row['theme_tags'] or [],
            emotion_tags=row['emotion_tags'] or [],
            popularity_score=float(row['popularity_score']) if row['popularity_score'] else 0.0,
            quality_score=float(row['quality_score']) if row['quality_score'] else 0.0,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
