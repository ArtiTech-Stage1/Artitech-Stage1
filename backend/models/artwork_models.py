from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class Artwork(BaseModel):
    """艺术品模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    artist: str
    style: str
    period: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    mood_associations: List[str] = Field(default_factory=list)
    emotional_impact: str = Field(default="medium")  # "low", "medium", "high"
    description: str
    historical_context: Optional[str] = None
    image_url: Optional[str] = None
    visual_elements: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    popularity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)

class ArtworkKnowledgeBase(BaseModel):
    """艺术品知识库模型"""
    artworks: List[Artwork] = Field(default_factory=list)
    total_count: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")

class ArtElementsResponse(BaseModel):
    """艺术元素响应模型"""
    mood: Optional[str] = None
    emotion_intensity: str  # "low", "medium", "high"
    colors: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    direct_response: str
    is_recommendation_query: bool
    needs_guidance: bool
    is_malicious: bool
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    extracted_context: Dict[str, Any] = Field(default_factory=dict)

class VisualElements(BaseModel):
    """视觉元素模型"""
    composition: Optional[str] = None
    brushwork: Optional[str] = None
    lighting: Optional[str] = None
    perspective: Optional[str] = None
    texture: Optional[str] = None
    color_palette: Optional[str] = None

class ArtworkEmbedding(BaseModel):
    """艺术品嵌入向量模型"""
    artwork_id: str
    text_embedding: List[float] = Field(default_factory=list)
    emotion_embedding: List[float] = Field(default_factory=list)
    visual_embedding: List[float] = Field(default_factory=list)
    composite_embedding: List[float] = Field(default_factory=list)
    embedding_dimension: int = Field(default=512)
    created_at: datetime = Field(default_factory=datetime.now)

