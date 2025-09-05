from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务引用（由main.py设置）
recommendation_engine = None
rag_service = None

class AdvancedRecommendationRequest(BaseModel):
    """高级推荐请求模型"""
    user_id: str
    query_text: str
    current_mood: Optional[str] = None
    preferred_colors: List[str] = []
    preferred_themes: List[str] = []
    preferred_styles: List[str] = []
    max_results: int = 5

@router.post("/recommendations/generate")
async def generate_advanced_recommendations(request: AdvancedRecommendationRequest):
    """生成高级推荐"""
    try:
        if not recommendation_engine:
            raise HTTPException(status_code=500, detail="推荐引擎未初始化")
        
        logger.info(f"为用户{request.user_id}生成高级推荐")
        
        # 构建推荐上下文
        from models.recommendation_models import RecommendationContext
        
        context = RecommendationContext(
            user_profile={'current_mood': request.current_mood},
            conversation_history=[],
            current_session={},
            seasonal_factors={},
            trending_topics=[]
        )
        
        # 生成推荐
        from models.recommendation_models import RecommendationRequest
        rec_request = RecommendationRequest(
            user_id=request.user_id,
            query_text=request.query_text,
            current_mood=request.current_mood,
            preferred_colors=request.preferred_colors,
            preferred_themes=request.preferred_themes,
            preferred_styles=request.preferred_styles,
            max_results=request.max_results
        )
        
        response = await recommendation_engine.generate_recommendations(rec_request, context)
        
        return {
            "user_id": request.user_id,
            "recommendations": response.recommendations,
            "total_count": response.total_count,
            "confidence_score": response.confidence_score,
            "reasoning": response.reasoning,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成高级推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/retrieve")
async def rag_retrieval(request: AdvancedRecommendationRequest):
    """RAG检索端点"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未初始化")
        
        logger.info(f"为用户{request.user_id}执行RAG检索")
        
        # 构建推荐请求和上下文
        from models.recommendation_models import RecommendationRequest, RecommendationContext
        
        rag_request = RecommendationRequest(
            user_id=request.user_id,
            query_text=request.query_text,
            current_mood=request.current_mood,
            preferred_colors=request.preferred_colors,
            preferred_themes=request.preferred_themes,
            preferred_styles=request.preferred_styles,
            max_results=request.max_results
        )
        
        context = RecommendationContext(
            user_profile={'current_mood': request.current_mood},
            conversation_history=[],
            current_session={},
            seasonal_factors={},
            trending_topics=[]
        )
        
        # 执行RAG检索
        results = await rag_service.retrieve_artworks(rag_request, context)
        
        return {
            "user_id": request.user_id,
            "query": request.query_text,
            "results": results,
            "total_count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RAG检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
