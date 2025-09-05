"""
聊天会话和消息管理数据访问层
"""

import json
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from database.config import DatabaseManager
from .models import (
    ChatSession, ChatMessage, RecommendationHistory,
    CreateChatSessionRequest, AddChatMessageRequest, AddRecommendationRequest
)

logger = logging.getLogger(__name__)

class ChatRepository:
    """聊天数据访问类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_chat_session(self, user_id: UUID, session_data: CreateChatSessionRequest) -> ChatSession:
        """创建新的聊天会话"""
        query = """
        INSERT INTO chat_sessions (user_id, session_name)
        VALUES ($1, $2)
        RETURNING id, user_id, session_name, started_at, ended_at, is_active, total_messages
        """
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:
            row = await conn.fetchrow(query, user_id, session_data.session_name)
            
            if row:
                logger.info(f"创建聊天会话成功: {row['id']}")
                return ChatSession(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_name=row['session_name'],
                    started_at=row['started_at'],
                    ended_at=row['ended_at'],
                    is_active=row['is_active'],
                    total_messages=row['total_messages']
                )
            else:
                raise Exception("创建聊天会话失败")
    
    async def get_chat_session(self, session_id: UUID) -> Optional[ChatSession]:
        """获取聊天会话"""
        query = """
        SELECT id, user_id, session_name, started_at, ended_at, is_active, total_messages
        FROM chat_sessions 
        WHERE id = $1
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:
            row = await conn.fetchrow(query, session_id)
            
            if row:
                session = ChatSession(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_name=row['session_name'],
                    started_at=row['started_at'],
                    ended_at=row['ended_at'],
                    is_active=row['is_active'],
                    total_messages=row['total_messages']
                )
                
                # 加载会话消息
                session.messages = await self.get_session_messages(session_id)
                
                return session
            
            return None
    
    async def get_user_sessions(self, user_id: UUID, limit: int = 10) -> List[ChatSession]:
        """获取用户的聊天会话列表"""
        query = """
        SELECT id, user_id, session_name, started_at, ended_at, is_active, total_messages
        FROM chat_sessions 
        WHERE user_id = $1
        ORDER BY started_at DESC
        LIMIT $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            rows = await conn.fetch(query, user_id, limit)
            
            sessions = []
            for row in rows:
                sessions.append(ChatSession(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_name=row['session_name'],
                    started_at=row['started_at'],
                    ended_at=row['ended_at'],
                    is_active=row['is_active'],
                    total_messages=row['total_messages']
                ))
            
            return sessions
    
    async def get_active_session(self, user_id: UUID) -> Optional[ChatSession]:
        """获取用户当前活跃的会话"""
        query = """
        SELECT id, user_id, session_name, started_at, ended_at, is_active, total_messages
        FROM chat_sessions 
        WHERE user_id = $1 AND is_active = TRUE
        ORDER BY started_at DESC
        LIMIT 1
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(query, user_id)
            
            if row:
                return ChatSession(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_name=row['session_name'],
                    started_at=row['started_at'],
                    ended_at=row['ended_at'],
                    is_active=row['is_active'],
                    total_messages=row['total_messages']
                )
            
            return None
    
    async def end_chat_session(self, session_id: UUID) -> bool:
        """结束聊天会话"""
        query = """
        UPDATE chat_sessions 
        SET ended_at = $1, is_active = FALSE
        WHERE id = $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(query, datetime.now(), session_id)
            return result == "UPDATE 1"
    
    async def add_chat_message(self, user_id: UUID, message_data: AddChatMessageRequest) -> ChatMessage:
        """添加聊天消息"""
        # 首先更新会话的消息计数
        update_session_query = """
        UPDATE chat_sessions 
        SET total_messages = total_messages + 1
        WHERE id = $1
        """
        
        # 插入消息
        insert_message_query = """
        INSERT INTO chat_messages (session_id, user_id, message_type, content, extracted_elements, recommendation_triggered)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, session_id, user_id, message_type, content, extracted_elements, recommendation_triggered, created_at
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            async with conn.transaction():
                # 更新会话计数
                await conn.execute(update_session_query, message_data.session_id)
                
                # 插入消息
                row = await conn.fetchrow(
                    insert_message_query,
                    message_data.session_id,
                    user_id,
                    message_data.message_type,
                    message_data.content,
                    json.dumps(message_data.extracted_elements) if message_data.extracted_elements else None,
                    message_data.recommendation_triggered
                )
                
                if row:
                    logger.info(f"添加聊天消息成功: {row['id']}")
                    return ChatMessage(
                        id=row['id'],
                        session_id=row['session_id'],
                        message_type=row['message_type'],
                        content=row['content'],
                        extracted_elements=json.loads(row['extracted_elements']) if row['extracted_elements'] else None,
                        recommendation_triggered=row['recommendation_triggered'],
                        created_at=row['created_at']
                    )
                else:
                    raise Exception("添加聊天消息失败")
    
    async def get_session_messages(self, session_id: UUID, limit: int = 50) -> List[ChatMessage]:
        """获取会话消息"""
        query = """
        SELECT id, session_id, user_id, message_type, content, extracted_elements, recommendation_triggered, created_at
        FROM chat_messages 
        WHERE session_id = $1
        ORDER BY created_at ASC
        LIMIT $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            rows = await conn.fetch(query, session_id, limit)
            
            messages = []
            for row in rows:
                messages.append(ChatMessage(
                    id=row['id'],
                    session_id=row['session_id'],
                    message_type=row['message_type'],
                    content=row['content'],
                    extracted_elements=json.loads(row['extracted_elements']) if row['extracted_elements'] else None,
                    recommendation_triggered=row['recommendation_triggered'],
                    created_at=row['created_at']
                ))
            
            return messages
    
    async def get_user_message_history(self, user_id: UUID, limit: int = 100) -> List[ChatMessage]:
        """获取用户的消息历史"""
        query = """
        SELECT cm.id, cm.session_id, cm.user_id, cm.message_type, cm.content, 
               cm.extracted_elements, cm.recommendation_triggered, cm.created_at
        FROM chat_messages cm
        JOIN chat_sessions cs ON cm.session_id = cs.id
        WHERE cm.user_id = $1
        ORDER BY cm.created_at DESC
        LIMIT $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            rows = await conn.fetch(query, user_id, limit)
            
            messages = []
            for row in rows:
                messages.append(ChatMessage(
                    id=row['id'],
                    session_id=row['session_id'],
                    message_type=row['message_type'],
                    content=row['content'],
                    extracted_elements=json.loads(row['extracted_elements']) if row['extracted_elements'] else None,
                    recommendation_triggered=row['recommendation_triggered'],
                    created_at=row['created_at']
                ))
            
            return messages

class RecommendationRepository:
    """推荐历史数据访问类"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def add_recommendation(self, user_id: UUID, recommendation_data: AddRecommendationRequest) -> RecommendationHistory:
        """添加推荐记录"""
        query = """
        INSERT INTO recommendation_history (user_id, session_id, message_id, artwork_ids, recommendation_context)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, user_id, session_id, message_id, artwork_ids, recommendation_context, user_feedback, created_at
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(
                query,
                user_id,
                recommendation_data.session_id,
                recommendation_data.message_id,
                json.dumps(recommendation_data.artwork_ids),
                json.dumps(recommendation_data.recommendation_context)
            )

            if row:
                logger.info(f"添加推荐记录成功: {row['id']}")
                return RecommendationHistory(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    message_id=row['message_id'],
                    artwork_ids=json.loads(row['artwork_ids']),
                    recommendation_context=json.loads(row['recommendation_context']),
                    user_feedback=row['user_feedback'],
                    created_at=row['created_at']
                )
            else:
                raise Exception("添加推荐记录失败")

    async def update_recommendation_feedback(self, recommendation_id: UUID, feedback: str) -> bool:
        """更新推荐反馈"""
        query = """
        UPDATE recommendation_history
        SET user_feedback = $1
        WHERE id = $2
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(query, feedback, recommendation_id)
            return result == "UPDATE 1"

    async def get_user_recommendations(self, user_id: UUID, limit: int = 20) -> List[RecommendationHistory]:
        """获取用户推荐历史"""
        query = """
        SELECT id, user_id, session_id, message_id, artwork_ids, recommendation_context, user_feedback, created_at
        FROM recommendation_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            rows = await conn.fetch(query, user_id, limit)

            recommendations = []
            for row in rows:
                recommendations.append(RecommendationHistory(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    message_id=row['message_id'],
                    artwork_ids=json.loads(row['artwork_ids']),
                    recommendation_context=json.loads(row['recommendation_context']),
                    user_feedback=row['user_feedback'],
                    created_at=row['created_at']
                ))

            return recommendations
