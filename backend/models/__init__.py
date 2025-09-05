"""
简化的模型模块

注意：主要的用户管理模型现在位于 user_management.models 中
这个模块只包含一些通用的模型定义
"""

from .conversation_models import *
from .user_models import *
from .artwork_models import *
from .recommendation_models import *

__all__ = [
    # Conversation models
    "ConversationState",
    "ConversationTurn",
    "ConversationQualityMetrics",
    
    # User models
    "UserProfile",
    "UserPreference",
    "MoodEntry",
    "UserActivityLog",
    
    # Artwork models
    "Artwork",
    "ArtworkKnowledgeBase",
    "ArtElementsResponse",
    
    # Recommendation models
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationContext"
]
