from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class EmotionIntensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ConversationState(BaseModel):
    """对话状态管理模型"""
    user_engagement_level: float = Field(default=0.5, ge=0.0, le=1.0)
    information_completeness: float = Field(default=0.3, ge=0.0, le=1.0)
    emotional_clarity: float = Field(default=0.4, ge=0.0, le=1.0)
    preference_specificity: float = Field(default=0.3, ge=0.0, le=1.0)
    conversation_depth: int = Field(default=1, ge=1)
    current_phase: str = Field(default="greeting")
    last_updated: datetime = Field(default_factory=datetime.now)

class ConversationTurn(BaseModel):
    """单轮对话数据模型"""
    turn_id: str
    user_input: str
    system_response: str
    extracted_elements: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_ms: Optional[int] = None
    user_satisfaction: Optional[float] = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)

class ConversationQualityMetrics(BaseModel):
    """对话质量评估指标"""
    engagement_score: float = Field(ge=0.0, le=1.0)
    recommendation_accuracy: float = Field(ge=0.0, le=1.0)
    avg_response_time: float
    user_satisfaction: float = Field(ge=0.0, le=5.0)
    conversation_completion_rate: float = Field(ge=0.0, le=1.0)
    error_rate: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationMemory(BaseModel):
    """对话记忆结构"""
    short_term_memory: List[ConversationTurn] = Field(default_factory=list)
    long_term_preferences: Dict[str, Any] = Field(default_factory=dict)
    episodic_memory: List[ConversationTurn] = Field(default_factory=list)
    semantic_associations: Dict[str, List[str]] = Field(default_factory=dict)

