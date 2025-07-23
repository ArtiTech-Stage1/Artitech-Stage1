"""
用户管理模块

这个模块提供了完整的用户管理功能，包括：
- Clerk 认证集成
- 用户注册和登录
- 用户资料管理
- 偏好设置
- 情绪跟踪
- 聊天会话管理
- 推荐历史记录
- 用户活动日志
"""

from .models import (
    User, UserPreference, UserMood, ChatSession, ChatMessage,
    RecommendationHistory, UserActivityLog, CreateUserRequest,
    UpdateUserRequest, AddPreferenceRequest, UpdateMoodRequest,
    CreateChatSessionRequest, AddChatMessageRequest, AddRecommendationRequest,
    UserResponse, UserStatsResponse
)

from .repository import UserRepository
from .chat_repository import ChatRepository, RecommendationRepository
from .service import UserService
from .auth import ClerkAuth, get_current_user, get_optional_user, clerk_auth
from .routes import router as user_router

__all__ = [
    # Models
    'User', 'UserPreference', 'UserMood', 'ChatSession', 'ChatMessage',
    'RecommendationHistory', 'UserActivityLog', 'CreateUserRequest',
    'UpdateUserRequest', 'AddPreferenceRequest', 'UpdateMoodRequest',
    'CreateChatSessionRequest', 'AddChatMessageRequest', 'AddRecommendationRequest',
    'UserResponse', 'UserStatsResponse',
    
    # Repositories
    'UserRepository', 'ChatRepository', 'RecommendationRepository',
    
    # Services
    'UserService',
    
    # Auth
    'ClerkAuth', 'get_current_user', 'get_optional_user', 'clerk_auth',
    
    # Routes
    'user_router'
]
