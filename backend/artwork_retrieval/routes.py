"""
艺术品检索API路由
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks

from user_management.auth import get_current_user
from .models import (
    RecommendationRequest, RecommendationResponse, SearchRequest, SearchResponse,
    Artwork, ArtworkStats, BatchProcessingStatus
)
from .retrieval_engine import ArtworkRetrievalEngine
from .data_importer import ArtworkDataImporter
from .service import ArtworkRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/artworks", tags=["艺术品检索"])

# 全局服务实例
_retrieval_engine = None
_retrieval_service = None

async def get_retrieval_engine() -> ArtworkRetrievalEngine:
    """获取检索引擎实例"""
    global _retrieval_engine
    if _retrieval_engine is None:
        _retrieval_engine = ArtworkRetrievalEngine()
        await _retrieval_engine.initialize()
    return _retrieval_engine

async def get_retrieval_service() -> ArtworkRetrievalService:
    """获取检索服务实例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = ArtworkRetrievalService()
        await _retrieval_service.initialize()
    return _retrieval_service

@router.post("/recommend", response_model=RecommendationResponse)
async def get_artwork_recommendations(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
    engine: ArtworkRetrievalEngine = Depends(get_retrieval_engine)
):
    """获取艺术品推荐"""
    try:
        # 设置用户ID
        request.user_id = UUID(current_user['user_id'])
        
        logger.info(f"用户 {request.user_id} 请求艺术品推荐")
        
        # 执行推荐
        response = await engine.retrieve_artworks(request)
        
        # 记录用户交互
        if response.artworks:
            await _log_recommendation_interaction(request.user_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"艺术品推荐失败: {e}")
        raise HTTPException(status_code=500, detail="推荐服务暂时不可用")

@router.get("/search", response_model=SearchResponse)
async def search_artworks(
    query: str = Query(..., description="搜索查询"),
    department: Optional[str] = Query(None, description="部门过滤"),
    culture: Optional[str] = Query(None, description="文化过滤"),
    artist: Optional[str] = Query(None, description="艺术家过滤"),
    sort_by: str = Query("relevance", description="排序方式"),
    sort_order: str = Query("desc", description="排序顺序"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """搜索艺术品"""
    try:
        # 构建搜索请求
        search_request = SearchRequest(
            query=query,
            filters={
                "department": department,
                "culture": culture,
                "artist": artist
            },
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # 执行搜索
        response = await service.search_artworks(search_request)
        
        return response
        
    except Exception as e:
        logger.error(f"艺术品搜索失败: {e}")
        raise HTTPException(status_code=500, detail="搜索服务暂时不可用")

@router.get("/artwork/{artwork_id}", response_model=Artwork)
async def get_artwork_detail(
    artwork_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """获取艺术品详情"""
    try:
        artwork = await service.get_artwork_by_id(artwork_id)
        
        if not artwork:
            raise HTTPException(status_code=404, detail="艺术品不存在")
        
        # 记录查看行为
        await _log_artwork_interaction(
            UUID(current_user['user_id']), 
            artwork_id, 
            "view"
        )
        
        return artwork
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取艺术品详情失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用")

@router.post("/artwork/{artwork_id}/interaction")
async def record_artwork_interaction(
    artwork_id: UUID,
    interaction_type: str,
    interaction_score: float = 1.0,
    current_user: dict = Depends(get_current_user),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """记录用户与艺术品的交互"""
    try:
        valid_interactions = ['view', 'like', 'dislike', 'save', 'share']
        if interaction_type not in valid_interactions:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的交互类型，支持: {', '.join(valid_interactions)}"
            )
        
        await _log_artwork_interaction(
            UUID(current_user['user_id']),
            artwork_id,
            interaction_type,
            interaction_score
        )
        
        return {"message": "交互记录成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录交互失败: {e}")
        raise HTTPException(status_code=500, detail="记录交互失败")

@router.get("/similar/{artwork_id}", response_model=List[Artwork])
async def get_similar_artworks(
    artwork_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """获取相似艺术品"""
    try:
        similar_artworks = await service.get_similar_artworks(artwork_id, limit)
        return similar_artworks
        
    except Exception as e:
        logger.error(f"获取相似艺术品失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用")

@router.get("/stats", response_model=ArtworkStats)
async def get_artwork_stats(
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """获取艺术品统计信息"""
    try:
        stats = await service.get_artwork_stats()
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用")

@router.post("/import/csv")
async def import_artworks_from_csv(
    csv_file_path: str,
    batch_size: int = 100,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user)
):
    """从CSV文件导入艺术品数据"""
    try:
        # 检查用户权限（这里简化处理，实际应该检查管理员权限）
        logger.info(f"用户 {current_user['user_id']} 请求导入CSV数据: {csv_file_path}")
        
        # 创建导入器
        importer = ArtworkDataImporter()
        
        # 在后台任务中执行导入
        background_tasks.add_task(
            _background_import_task,
            importer,
            csv_file_path,
            batch_size
        )
        
        return {
            "message": "导入任务已启动",
            "csv_file": csv_file_path,
            "batch_size": batch_size
        }
        
    except Exception as e:
        logger.error(f"启动导入任务失败: {e}")
        raise HTTPException(status_code=500, detail="导入任务启动失败")

@router.get("/import/stats")
async def get_import_stats():
    """获取导入统计信息"""
    try:
        importer = ArtworkDataImporter()
        await importer.initialize()
        
        stats = await importer.get_import_stats()
        return stats
        
    except Exception as e:
        logger.error(f"获取导入统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@router.get("/popular", response_model=List[Artwork])
async def get_popular_artworks(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """获取热门艺术品"""
    try:
        popular_artworks = await service.get_popular_artworks(limit)
        return popular_artworks
        
    except Exception as e:
        logger.error(f"获取热门艺术品失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用")

@router.get("/recent", response_model=List[Artwork])
async def get_recent_artworks(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    service: ArtworkRetrievalService = Depends(get_retrieval_service)
):
    """获取最新添加的艺术品"""
    try:
        recent_artworks = await service.get_recent_artworks(limit)
        return recent_artworks
        
    except Exception as e:
        logger.error(f"获取最新艺术品失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用")

# 辅助函数

async def _log_recommendation_interaction(user_id: UUID, response: RecommendationResponse):
    """记录推荐交互"""
    try:
        service = await get_retrieval_service()
        
        for artwork in response.artworks[:3]:  # 只记录前3个推荐
            await service.log_artwork_interaction(
                user_id=user_id,
                artwork_id=artwork.id,
                interaction_type="recommendation",
                interaction_score=0.5,
                context={"recommendation_id": response.recommendation_id}
            )
            
    except Exception as e:
        logger.error(f"记录推荐交互失败: {e}")

async def _log_artwork_interaction(user_id: UUID, artwork_id: UUID, 
                                 interaction_type: str, interaction_score: float = 1.0):
    """记录艺术品交互"""
    try:
        service = await get_retrieval_service()
        
        await service.log_artwork_interaction(
            user_id=user_id,
            artwork_id=artwork_id,
            interaction_type=interaction_type,
            interaction_score=interaction_score
        )
        
    except Exception as e:
        logger.error(f"记录艺术品交互失败: {e}")

async def _background_import_task(importer: ArtworkDataImporter, 
                                csv_file_path: str, batch_size: int):
    """后台导入任务"""
    try:
        logger.info(f"开始后台导入任务: {csv_file_path}")
        
        await importer.initialize()
        status = await importer.import_from_csv(csv_file_path, batch_size)
        
        logger.info(f"导入任务完成: {status.status}, 处理了 {status.processed_items} 条记录")
        
    except Exception as e:
        logger.error(f"后台导入任务失败: {e}")
