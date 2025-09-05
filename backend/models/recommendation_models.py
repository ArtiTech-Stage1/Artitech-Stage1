from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    user_id: str
    query_text: str
    current_mood: Optional[str] = None
    preferred_colors: List[str] = Field(default_factory=list)
    preferred_themes: List[str] = Field(default_factory=list)
    preferred_styles: List[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=1, le=20)
    include_explanations: bool = Field(default=True)
    context: Dict[str, Any] = Field(default_factory=dict)

class RecommendationResponse(BaseModel):
    """推荐响应模型"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = Field(default=0)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    reasoning: str
    alternative_suggestions: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)

class RecommendationContext(BaseModel):
    """推荐上下文模型"""
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_session: Dict[str, Any] = Field(default_factory=dict)
    seasonal_factors: Dict[str, Any] = Field(default_factory=dict)
    trending_topics: List[str] = Field(default_factory=list)

class RecommendationItem(BaseModel):
    """推荐项目模型"""
    artwork_id: str
    title: str
    artist: str
    match_score: float = Field(ge=0.0, le=1.0)
    match_reasons: List[str] = Field(default_factory=list)
    emotional_fit: float = Field(ge=0.0, le=1.0)
    visual_appeal: float = Field(ge=0.0, le=1.0)
    novelty_factor: float = Field(ge=0.0, le=1.0)
    explanation: str

class UserFeedback(BaseModel):
    """用户反馈模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recommendation_id: str
    artwork_id: str
    rating: int = Field(ge=1, le=5)
    feedback_type: str  # "liked", "disliked", "neutral", "loved", "hated"
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class RecommendationMetrics(BaseModel):
    """推荐指标模型"""
    total_recommendations: int = Field(default=0)
    accepted_recommendations: int = Field(default=0)
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    click_through_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    user_satisfaction: float = Field(default=0.0, ge=0.0, le=1.0)
    diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

