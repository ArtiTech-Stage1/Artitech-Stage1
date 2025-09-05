"""
用户管理 API 路由
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from database.config import get_db_manager
from .service import UserService
from .auth import get_current_user, get_optional_user, extract_user_data_from_clerk, clerk_auth
from .models import (
    User, UserResponse, UserStatsResponse, CreateUserRequest, UpdateUserRequest,
    AddPreferenceRequest, UpdateMoodRequest, CreateChatSessionRequest,
    AddChatMessageRequest, AddRecommendationRequest, ChatSession, ChatMessage,
    RecommendationHistory
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["用户管理"])

# 依赖注入
async def get_user_service() -> UserService:
    """获取用户服务实例"""
    db_manager = get_db_manager()
    return UserService(db_manager)

@router.post("/auth/login", response_model=UserResponse)
async def login_or_register(
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """用户登录或注册"""
    try:
        clerk_user_id = current_user['user_id']
        
        # 从 Clerk 获取完整用户信息
        clerk_user_data = await clerk_auth.get_user_info_from_clerk(clerk_user_id)
        
        # 提取用户数据
        user_data_dict = extract_user_data_from_clerk(clerk_user_data)
        user_data = CreateUserRequest(**user_data_dict)
        
        # 创建或获取用户
        user = await user_service.create_or_get_user(clerk_user_id, user_data)
        
        # 记录活动日志
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await user_service.log_user_activity(
            user.id, 
            "login", 
            {"clerk_user_id": clerk_user_id},
            client_ip,
            user_agent
        )
        
        return UserResponse(
            id=user.id,
            clerk_user_id=user.clerk_user_id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            is_active=user.is_active,
            preferences=user.preferences,
            current_mood=user.current_mood
        )
        
    except Exception as e:
        logger.error(f"用户登录/注册失败: {e}")
        raise HTTPException(status_code=500, detail="登录失败")

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户资料"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse(
        id=user.id,
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        is_active=user.is_active,
        preferences=user.preferences,
        current_mood=user.current_mood
    )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户资料"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    updated_user = await user_service.update_user_profile(user.id, profile_data)
    
    if not updated_user:
        raise HTTPException(status_code=500, detail="更新失败")
    
    return UserResponse(
        id=updated_user.id,
        clerk_user_id=updated_user.clerk_user_id,
        email=updated_user.email,
        username=updated_user.username,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        avatar_url=updated_user.avatar_url,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        last_login=updated_user.last_login,
        is_active=updated_user.is_active,
        preferences=updated_user.preferences,
        current_mood=updated_user.current_mood
    )

@router.post("/preferences")
async def add_user_preference(
    preference: AddPreferenceRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """添加用户偏好"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = await user_service.add_user_preference(user.id, preference)
    
    if not success:
        raise HTTPException(status_code=500, detail="添加偏好失败")
    
    return {"message": "偏好添加成功"}

@router.delete("/preferences/{preference_type}/{preference_value}")
async def remove_user_preference(
    preference_type: str,
    preference_value: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """删除用户偏好"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = await user_service.remove_user_preference(user.id, preference_type, preference_value)
    
    if not success:
        raise HTTPException(status_code=404, detail="偏好不存在")
    
    return {"message": "偏好删除成功"}

@router.post("/mood")
async def update_user_mood(
    mood_data: UpdateMoodRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户情绪"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = await user_service.update_user_mood(user.id, mood_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="更新情绪失败")
    
    return {"message": "情绪更新成功"}

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户统计信息"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    stats = await user_service.get_user_stats(user.id)
    return stats

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: CreateChatSessionRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """创建聊天会话"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    session = await user_service.create_chat_session(user.id, session_data)
    return session

@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户聊天会话"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    sessions = await user_service.get_user_chat_sessions(user.id, limit)
    return sessions

@router.get("/sessions/active", response_model=Optional[ChatSession])
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取活跃聊天会话"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    session = await user_service.get_active_chat_session(user.id)
    return session

@router.post("/messages", response_model=ChatMessage)
async def add_chat_message(
    message_data: AddChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """添加聊天消息"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    message = await user_service.add_chat_message(user.id, message_data)
    return message

@router.post("/sessions/{session_id}/end")
async def end_chat_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """结束聊天会话"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = await user_service.end_chat_session(user.id, session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"message": "会话已结束"}

@router.post("/recommendations", response_model=RecommendationHistory)
async def add_recommendation(
    recommendation_data: AddRecommendationRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """添加推荐记录"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    recommendation = await user_service.add_recommendation(user.id, recommendation_data)
    return recommendation

@router.get("/recommendations", response_model=List[RecommendationHistory])
async def get_user_recommendations(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户推荐历史"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    recommendations = await user_service.get_user_recommendations(user.id, limit)
    return recommendations

@router.put("/recommendations/{recommendation_id}/feedback")
async def update_recommendation_feedback(
    recommendation_id: UUID,
    feedback: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新推荐反馈"""
    user = await user_service.get_user_by_clerk_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if feedback not in ['liked', 'disliked', 'neutral']:
        raise HTTPException(status_code=400, detail="无效的反馈类型")
    
    success = await user_service.update_recommendation_feedback(user.id, recommendation_id, feedback)
    
    if not success:
        raise HTTPException(status_code=404, detail="推荐记录不存在")
    
    return {"message": "反馈更新成功"}
