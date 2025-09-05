"""
艺术品检索系统的数据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class Artwork(BaseModel):
    """艺术品模型"""
    id: Optional[UUID] = None
    object_id: str
    title: str
    object_name: Optional[str] = None
    department: Optional[str] = None
    culture: Optional[str] = None
    period: Optional[str] = None
    artist_display_name: Optional[str] = None
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    classification: Optional[str] = None
    object_date: Optional[str] = None
    general_text_description: Optional[str] = None
    url: Optional[str] = None
    
    # 标签字段
    color_tags: List[str] = Field(default_factory=list)
    style_tags: List[str] = Field(default_factory=list)
    theme_tags: List[str] = Field(default_factory=list)
    emotion_tags: List[str] = Field(default_factory=list)
    
    # 评分字段
    popularity_score: float = 0.0
    quality_score: float = 0.0
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ArtworkEmbedding(BaseModel):
    """艺术品嵌入向量模型"""
    id: Optional[UUID] = None
    artwork_id: UUID
    embedding_type: str  # 'title', 'description', 'combined'
    embedding_vector: List[float]
    model_name: str
    created_at: Optional[datetime] = None


class ArtworkUserInteraction(BaseModel):
    """用户与艺术品交互模型"""
    id: Optional[UUID] = None
    user_id: UUID
    artwork_id: UUID
    interaction_type: str  # 'view', 'like', 'dislike', 'save', 'share'
    interaction_score: float = 1.0
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ArtworkSimilarity(BaseModel):
    """艺术品相似度模型"""
    id: Optional[UUID] = None
    artwork_id_1: UUID
    artwork_id_2: UUID
    similarity_score: float
    similarity_type: str  # 'visual', 'semantic', 'style', 'theme'
    created_at: Optional[datetime] = None


class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    user_id: UUID
    query: Optional[str] = None
    mood: Optional[str] = None
    preferred_colors: List[str] = Field(default_factory=list)
    preferred_styles: List[str] = Field(default_factory=list)
    preferred_themes: List[str] = Field(default_factory=list)
    excluded_artwork_ids: List[UUID] = Field(default_factory=list)
    limit: int = 20
    offset: int = 0
    use_cache: bool = True


class RecommendationResponse(BaseModel):
    """推荐响应模型"""
    artworks: List[Artwork]
    scores: List[float]
    total_count: int
    has_more: bool
    recommendation_id: Optional[str] = None
    cache_used: bool = False


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "relevance"  # 'relevance', 'popularity', 'date', 'title'
    sort_order: str = "desc"  # 'asc', 'desc'
    limit: int = 20
    offset: int = 0


class SearchResponse(BaseModel):
    """搜索响应模型"""
    artworks: List[Artwork]
    total_count: int
    has_more: bool
    search_time_ms: float


class ArtworkBatch(BaseModel):
    """艺术品批次模型（用于数据导入）"""
    artworks: List[Artwork]
    batch_size: int
    total_batches: int
    current_batch: int


class RecommendationCache(BaseModel):
    """推荐缓存模型"""
    id: Optional[UUID] = None
    user_id: UUID
    cache_key: str
    artwork_ids: List[UUID]
    scores: List[float]
    query_context: Optional[Dict[str, Any]] = None
    expires_at: datetime
    created_at: Optional[datetime] = None


class ArtworkStats(BaseModel):
    """艺术品统计模型"""
    total_artworks: int
    total_artists: int
    total_cultures: int
    total_departments: int
    popular_styles: List[Dict[str, Any]]
    popular_themes: List[Dict[str, Any]]
    recent_additions: int


class UserRecommendationProfile(BaseModel):
    """用户推荐档案模型"""
    user_id: UUID
    preferred_colors: List[str]
    preferred_styles: List[str]
    preferred_themes: List[str]
    preferred_artists: List[str]
    preferred_cultures: List[str]
    preferred_periods: List[str]
    disliked_styles: List[str]
    interaction_history: List[ArtworkUserInteraction]
    recommendation_feedback: Dict[str, float]


class RetrievalConfig(BaseModel):
    """检索配置模型"""
    # 粗排配置
    coarse_ranking_limit: int = 100
    use_text_search: bool = True
    use_vector_search: bool = True
    text_search_weight: float = 0.3
    vector_search_weight: float = 0.7
    
    # 精排配置
    fine_ranking_limit: int = 20
    user_preference_weight: float = 0.4
    mood_weight: float = 0.3
    popularity_weight: float = 0.2
    diversity_weight: float = 0.1
    
    # 缓存配置
    cache_ttl_hours: int = 24
    enable_cache: bool = True
    
    # 向量搜索配置
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.5
    
    # 多样性配置
    diversity_threshold: float = 0.8
    max_same_artist: int = 2
    max_same_style: int = 3


class BatchProcessingStatus(BaseModel):
    """批处理状态模型"""
    task_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: float  # 0.0 - 1.0
    total_items: int
    processed_items: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
