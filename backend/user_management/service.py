"""
用户管理服务层
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from database.config import DatabaseManager
from .user_repository import UserRepository
from .chat_repository import ChatRepository, RecommendationRepository
from .models import (
    User, UserResponse, UserStatsResponse, CreateUserRequest, UpdateUserRequest,
    AddPreferenceRequest, UpdateMoodRequest, CreateChatSessionRequest,
    AddChatMessageRequest, AddRecommendationRequest, ChatSession, ChatMessage,
    RecommendationHistory, UserActivityLog
)

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.user_repo = UserRepository(db_manager)
        self.chat_repo = ChatRepository(db_manager)
        self.recommendation_repo = RecommendationRepository(db_manager)
        self.db = db_manager
    
    async def create_or_get_user(self, clerk_user_id: str, user_data: CreateUserRequest) -> User:
        """创建或获取用户（用于Clerk登录后的用户初始化）"""
        # 首先尝试获取现有用户
        existing_user = await self.user_repo.get_user_by_clerk_id(clerk_user_id)
        
        if existing_user:
            # 更新最后登录时间
            await self.user_repo.update_last_login(existing_user.id)
            await self.log_user_activity(existing_user.id, "login")
            logger.info(f"用户登录: {existing_user.email}")
            return existing_user
        
        # 创建新用户
        new_user = await self.user_repo.create_user(user_data)
        await self.log_user_activity(new_user.id, "register")
        logger.info(f"新用户注册: {new_user.email}")
        
        return new_user
    
    async def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """根据Clerk用户ID获取用户"""
        return await self.user_repo.get_user_by_clerk_id(clerk_user_id)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据用户ID获取用户"""
        return await self.user_repo.get_user_by_id(user_id)
    
    async def update_user_profile(self, user_id: UUID, user_data: UpdateUserRequest) -> Optional[User]:
        """更新用户资料"""
        updated_user = await self.user_repo.update_user(user_id, user_data)
        if updated_user:
            await self.log_user_activity(user_id, "profile_update", {"updated_fields": user_data.model_dump(exclude_none=True)})
        return updated_user
    
    async def add_user_preference(self, user_id: UUID, preference: AddPreferenceRequest) -> bool:
        """添加用户偏好"""
        success = await self.user_repo.add_user_preference(user_id, preference)
        if success:
            await self.log_user_activity(user_id, "preference_add", {"preference": preference.model_dump()})
        return success
    
    async def remove_user_preference(self, user_id: UUID, preference_type: str, preference_value: str) -> bool:
        """删除用户偏好"""
        success = await self.user_repo.remove_user_preference(user_id, preference_type, preference_value)
        if success:
            await self.log_user_activity(user_id, "preference_remove", {
                "preference_type": preference_type,
                "preference_value": preference_value
            })
        return success
    
    async def update_user_mood(self, user_id: UUID, mood_data: UpdateMoodRequest) -> bool:
        """更新用户情绪"""
        success = await self.user_repo.add_mood_record(user_id, mood_data)
        if success:
            await self.log_user_activity(user_id, "mood_update", {"mood": mood_data.model_dump()})
        return success
    
    async def get_user_stats(self, user_id: UUID) -> UserStatsResponse:
        """获取用户统计信息"""
        # 获取会话统计
        sessions = await self.chat_repo.get_user_sessions(user_id, limit=1000)
        total_sessions = len(sessions)
        
        # 获取消息统计
        messages = await self.chat_repo.get_user_message_history(user_id, limit=1000)
        total_messages = len(messages)
        
        # 获取推荐统计
        recommendations = await self.recommendation_repo.get_user_recommendations(user_id, limit=1000)
        total_recommendations = len(recommendations)
        
        # 分析情绪偏好
        mood_query = """
        SELECT mood, COUNT(*) as count
        FROM user_mood_history 
        WHERE user_id = $1
        GROUP BY mood
        ORDER BY count DESC
        LIMIT 5
        """
        
        # 分析偏好统计
        preference_query = """
        SELECT preference_type, preference_value, weight
        FROM user_preferences 
        WHERE user_id = $1
        ORDER BY preference_type, weight DESC
        """
        
        # 获取最后活动时间
        activity_query = """
        SELECT created_at
        FROM user_activity_logs 
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            # 获取情绪统计
            mood_rows = await conn.fetch(mood_query, user_id)
            favorite_moods = [row['mood'] for row in mood_rows]
            
            # 获取偏好统计
            preference_rows = await conn.fetch(preference_query, user_id)
            top_preferences = {}
            for row in preference_rows:
                pref_type = row['preference_type']
                if pref_type not in top_preferences:
                    top_preferences[pref_type] = []
                if len(top_preferences[pref_type]) < 5:  # 只取前5个
                    top_preferences[pref_type].append(row['preference_value'])
            
            # 获取最后活动时间
            activity_row = await conn.fetchrow(activity_query, user_id)
            last_activity = activity_row['created_at'] if activity_row else None
        
        return UserStatsResponse(
            total_sessions=total_sessions,
            total_messages=total_messages,
            total_recommendations=total_recommendations,
            favorite_moods=favorite_moods,
            top_preferences=top_preferences,
            last_activity=last_activity
        )
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """停用用户"""
        success = await self.user_repo.deactivate_user(user_id)
        if success:
            await self.log_user_activity(user_id, "account_deactivated")
        return success
    
    # 聊天会话管理
    async def create_chat_session(self, user_id: UUID, session_data: CreateChatSessionRequest) -> ChatSession:
        """创建聊天会话"""
        session = await self.chat_repo.create_chat_session(user_id, session_data)
        await self.log_user_activity(user_id, "session_created", {"session_id": str(session.id)})
        return session
    
    async def get_user_chat_sessions(self, user_id: UUID, limit: int = 10) -> List[ChatSession]:
        """获取用户聊天会话"""
        return await self.chat_repo.get_user_sessions(user_id, limit)
    
    async def get_active_chat_session(self, user_id: UUID) -> Optional[ChatSession]:
        """获取活跃聊天会话"""
        return await self.chat_repo.get_active_session(user_id)
    
    async def add_chat_message(self, user_id: UUID, message_data: AddChatMessageRequest) -> ChatMessage:
        """添加聊天消息"""
        message = await self.chat_repo.add_chat_message(user_id, message_data)
        await self.log_user_activity(user_id, "message_sent", {
            "session_id": str(message_data.session_id),
            "message_type": message_data.message_type
        })
        return message
    
    async def end_chat_session(self, user_id: UUID, session_id: UUID) -> bool:
        """结束聊天会话"""
        success = await self.chat_repo.end_chat_session(session_id)
        if success:
            await self.log_user_activity(user_id, "session_ended", {"session_id": str(session_id)})
        return success
    
    # 推荐管理
    async def add_recommendation(self, user_id: UUID, recommendation_data: AddRecommendationRequest) -> RecommendationHistory:
        """添加推荐记录"""
        recommendation = await self.recommendation_repo.add_recommendation(user_id, recommendation_data)
        await self.log_user_activity(user_id, "recommendation_generated", {
            "artwork_count": len(recommendation_data.artwork_ids),
            "session_id": str(recommendation_data.session_id) if recommendation_data.session_id else None
        })
        return recommendation
    
    async def update_recommendation_feedback(self, user_id: UUID, recommendation_id: UUID, feedback: str) -> bool:
        """更新推荐反馈"""
        success = await self.recommendation_repo.update_recommendation_feedback(recommendation_id, feedback)
        if success:
            await self.log_user_activity(user_id, "recommendation_feedback", {
                "recommendation_id": str(recommendation_id),
                "feedback": feedback
            })
        return success
    
    async def get_user_recommendations(self, user_id: UUID, limit: int = 20) -> List[RecommendationHistory]:
        """获取用户推荐历史"""
        return await self.recommendation_repo.get_user_recommendations(user_id, limit)
    
    async def log_user_activity(self, user_id: UUID, activity_type: str, activity_data: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """记录用户活动日志"""
        query = """
        INSERT INTO user_activity_logs (user_id, activity_type, activity_data, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5)
        """
        
        import json
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            await conn.execute(
                query,
                user_id,
                activity_type,
                json.dumps(activity_data) if activity_data else None,
                ip_address,
                user_agent
            )
