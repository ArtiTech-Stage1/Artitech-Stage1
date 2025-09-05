from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

class PreferenceType(str, Enum):
    COLOR = "color"
    THEME = "theme"
    STYLE = "style"
    ARTIST = "artist"
    PERIOD = "period"

class MoodType(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    CALM = "calm"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    CONTENT = "content"
    LONELY = "lonely"
    STRESSED = "stressed"
    PEACEFUL = "peaceful"

class UserProfile(BaseModel):
    """用户画像模型"""
    user_id: str
    color_preferences: Dict[str, float] = Field(default_factory=dict)
    style_preferences: Dict[str, float] = Field(default_factory=dict)
    theme_preferences: Dict[str, float] = Field(default_factory=dict)
    current_mood: Optional[str] = None
    mood_history: List[str] = Field(default_factory=list)
    interaction_patterns: Dict[str, Any] = Field(default_factory=dict)
    feedback_weights: Dict[str, float] = Field(default_factory=dict)
    adaptation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserPreference(BaseModel):
    """用户偏好模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    preference_type: PreferenceType
    preference_value: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MoodEntry(BaseModel):
    """情感状态记录模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood: MoodType
    intensity: str  # "low", "medium", "high"
    context: Optional[str] = None
    trigger: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class UserActivityLog(BaseModel):
    """用户活动日志模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    activity_type: str
    activity_data: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

