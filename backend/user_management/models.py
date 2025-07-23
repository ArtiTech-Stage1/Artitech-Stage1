"""
用户管理相关的数据模型
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import uuid

class UserPreference(BaseModel):
    """用户偏好模型"""
    type: str = Field(..., description="偏好类型: color, theme, style, artist")
    value: str = Field(..., description="偏好值")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="偏好权重")

class UserMood(BaseModel):
    """用户情绪模型"""
    mood: str = Field(..., description="情绪类型")
    intensity: str = Field(..., description="情绪强度: low, medium, high")
    context: Optional[str] = Field(None, description="情绪上下文")
    created_at: datetime = Field(default_factory=datetime.now)

class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: Optional[UUID] = Field(default_factory=uuid.uuid4)
    session_id: UUID
    message_type: str = Field(..., description="消息类型: user, assistant")
    content: str = Field(..., description="消息内容")
    extracted_elements: Optional[Dict[str, Any]] = Field(None, description="提取的元素")
    recommendation_triggered: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

class ChatSession(BaseModel):
    """聊天会话模型"""
    id: Optional[UUID] = Field(default_factory=uuid.uuid4)
    user_id: UUID
    session_name: Optional[str] = Field(None)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = Field(None)
    is_active: bool = Field(default=True)
    total_messages: int = Field(default=0)
    messages: List[ChatMessage] = Field(default_factory=list)

class RecommendationHistory(BaseModel):
    """推荐历史模型"""
    id: Optional[UUID] = Field(default_factory=uuid.uuid4)
    user_id: UUID
    session_id: Optional[UUID] = Field(None)
    message_id: Optional[UUID] = Field(None)
    artwork_ids: List[str] = Field(..., description="推荐的艺术品ID列表")
    recommendation_context: Dict[str, Any] = Field(..., description="推荐上下文")
    user_feedback: Optional[str] = Field(None, description="用户反馈: liked, disliked, neutral")
    created_at: datetime = Field(default_factory=datetime.now)

class UserActivityLog(BaseModel):
    """用户活动日志模型"""
    id: Optional[UUID] = Field(default_factory=uuid.uuid4)
    user_id: UUID
    activity_type: str = Field(..., description="活动类型")
    activity_data: Optional[Dict[str, Any]] = Field(None)
    ip_address: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.now)

class User(BaseModel):
    """用户模型"""
    id: Optional[UUID] = Field(default_factory=uuid.uuid4)
    clerk_user_id: str = Field(..., description="Clerk用户ID")
    email: EmailStr = Field(..., description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    first_name: Optional[str] = Field(None, description="名")
    last_name: Optional[str] = Field(None, description="姓")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(None)
    is_active: bool = Field(default=True)
    
    # 关联数据
    preferences: List[UserPreference] = Field(default_factory=list)
    current_mood: Optional[UserMood] = Field(None)
    active_sessions: List[ChatSession] = Field(default_factory=list)

# 请求和响应模型
class CreateUserRequest(BaseModel):
    """创建用户请求"""
    clerk_user_id: str
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None

class AddPreferenceRequest(BaseModel):
    """添加偏好请求"""
    type: str
    value: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)

class UpdateMoodRequest(BaseModel):
    """更新情绪请求"""
    mood: str
    intensity: str = Field(..., pattern="^(low|medium|high)$")
    context: Optional[str] = None

class CreateChatSessionRequest(BaseModel):
    """创建聊天会话请求"""
    session_name: Optional[str] = None

class AddChatMessageRequest(BaseModel):
    """添加聊天消息请求"""
    session_id: UUID
    message_type: str = Field(..., pattern="^(user|assistant)$")
    content: str
    extracted_elements: Optional[Dict[str, Any]] = None
    recommendation_triggered: bool = False

class AddRecommendationRequest(BaseModel):
    """添加推荐记录请求"""
    session_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    artwork_ids: List[str]
    recommendation_context: Dict[str, Any]

class UserResponse(BaseModel):
    """用户响应模型"""
    id: UUID
    clerk_user_id: str
    email: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    preferences: List[UserPreference]
    current_mood: Optional[UserMood]

class UserStatsResponse(BaseModel):
    """用户统计响应"""
    total_sessions: int
    total_messages: int
    total_recommendations: int
    favorite_moods: List[str]
    top_preferences: Dict[str, List[str]]
    last_activity: Optional[datetime]
