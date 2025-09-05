"""
艺术品检索模块

这个模块提供了完整的艺术品检索和推荐功能，包括：
- 数据导入和预处理
- 基于向量和标签的检索
- 粗排和精排算法
- 个性化推荐
- 用户交互记录
"""

from .models import (
    Artwork,
    ArtworkEmbedding,
    ArtworkUserInteraction,
    RecommendationRequest,
    RecommendationResponse,
    SearchRequest,
    SearchResponse,
    ArtworkStats,
    RetrievalConfig
)

from .retrieval_engine import ArtworkRetrievalEngine
from .service import ArtworkRetrievalService
from .data_importer import ArtworkDataImporter, import_artworks_from_csv
from .embedding_service import EmbeddingService, get_embedding_service
from .tag_extractor import TagExtractor

__version__ = "1.0.0"

__all__ = [
    # Models
    "Artwork",
    "ArtworkEmbedding", 
    "ArtworkUserInteraction",
    "RecommendationRequest",
    "RecommendationResponse",
    "SearchRequest",
    "SearchResponse",
    "ArtworkStats",
    "RetrievalConfig",
    
    # Services
    "ArtworkRetrievalEngine",
    "ArtworkRetrievalService",
    "ArtworkDataImporter",
    "EmbeddingService",
    "TagExtractor",
    
    # Functions
    "import_artworks_from_csv",
    "get_embedding_service"
]
