"""
用户管理数据访问层
"""

import json
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from database.config import DatabaseManager
from .models import (
    User, UserPreference, UserMood, ChatSession, ChatMessage,
    RecommendationHistory, UserActivityLog, CreateUserRequest,
    UpdateUserRequest, AddPreferenceRequest, UpdateMoodRequest
)

logger = logging.getLogger(__name__)

class UserRepository:
    """用户数据访问类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_user(self, user_data: CreateUserRequest) -> User:
        """创建新用户"""
        query = """
        INSERT INTO users (clerk_user_id, email, username, first_name, last_name, avatar_url)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, clerk_user_id, email, username, first_name, last_name, 
                  avatar_url, created_at, updated_at, last_login, is_active
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(
                query,
                user_data.clerk_user_id,
                user_data.email,
                user_data.username,
                user_data.first_name,
                user_data.last_name,
                user_data.avatar_url
            )
            
            if row:
                logger.info(f"创建用户成功: {user_data.email}")
                return User(
                    id=row['id'],
                    clerk_user_id=row['clerk_user_id'],
                    email=row['email'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    avatar_url=row['avatar_url'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login=row['last_login'],
                    is_active=row['is_active']
                )
            else:
                raise Exception("创建用户失败")
    
    async def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """根据Clerk用户ID获取用户"""
        query = """
        SELECT id, clerk_user_id, email, username, first_name, last_name,
               avatar_url, created_at, updated_at, last_login, is_active
        FROM users 
        WHERE clerk_user_id = $1 AND is_active = TRUE
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(query, clerk_user_id)
            
            if row:
                user = User(
                    id=row['id'],
                    clerk_user_id=row['clerk_user_id'],
                    email=row['email'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    avatar_url=row['avatar_url'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login=row['last_login'],
                    is_active=row['is_active']
                )
                
                # 加载用户偏好
                user.preferences = await self.get_user_preferences(user.id)
                
                # 加载当前情绪
                user.current_mood = await self.get_current_mood(user.id)
                
                return user
            
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据用户ID获取用户"""
        query = """
        SELECT id, clerk_user_id, email, username, first_name, last_name,
               avatar_url, created_at, updated_at, last_login, is_active
        FROM users 
        WHERE id = $1 AND is_active = TRUE
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(query, user_id)
            
            if row:
                user = User(
                    id=row['id'],
                    clerk_user_id=row['clerk_user_id'],
                    email=row['email'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    avatar_url=row['avatar_url'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login=row['last_login'],
                    is_active=row['is_active']
                )
                
                # 加载用户偏好
                user.preferences = await self.get_user_preferences(user.id)
                
                # 加载当前情绪
                user.current_mood = await self.get_current_mood(user.id)
                
                return user
            
            return None
    
    async def update_user(self, user_id: UUID, user_data: UpdateUserRequest) -> Optional[User]:
        """更新用户信息"""
        # 构建动态更新查询
        update_fields = []
        values = []
        param_count = 1
        
        if user_data.username is not None:
            update_fields.append(f"username = ${param_count}")
            values.append(user_data.username)
            param_count += 1
            
        if user_data.first_name is not None:
            update_fields.append(f"first_name = ${param_count}")
            values.append(user_data.first_name)
            param_count += 1
            
        if user_data.last_name is not None:
            update_fields.append(f"last_name = ${param_count}")
            values.append(user_data.last_name)
            param_count += 1
            
        if user_data.avatar_url is not None:
            update_fields.append(f"avatar_url = ${param_count}")
            values.append(user_data.avatar_url)
            param_count += 1
        
        if not update_fields:
            # 没有字段需要更新
            return await self.get_user_by_id(user_id)
        
        update_fields.append(f"updated_at = ${param_count}")
        values.append(datetime.now())
        param_count += 1
        
        values.append(user_id)
        
        query = f"""
        UPDATE users 
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
        RETURNING id, clerk_user_id, email, username, first_name, last_name,
                  avatar_url, created_at, updated_at, last_login, is_active
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(query, *values)
            
            if row:
                logger.info(f"更新用户成功: {user_id}")
                return User(
                    id=row['id'],
                    clerk_user_id=row['clerk_user_id'],
                    email=row['email'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    avatar_url=row['avatar_url'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_login=row['last_login'],
                    is_active=row['is_active']
                )
            
            return None
    
    async def update_last_login(self, user_id: UUID) -> bool:
        """更新用户最后登录时间"""
        query = """
        UPDATE users 
        SET last_login = $1, updated_at = $1
        WHERE id = $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(query, datetime.now(), user_id)
            return result == "UPDATE 1"
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """停用用户"""
        query = """
        UPDATE users 
        SET is_active = FALSE, updated_at = $1
        WHERE id = $2
        """
        
        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(query, datetime.now(), user_id)
            return result == "UPDATE 1"

    async def get_user_preferences(self, user_id: UUID) -> List[UserPreference]:
        """获取用户偏好"""
        query = """
        SELECT preference_type, preference_value, weight, created_at, updated_at
        FROM user_preferences
        WHERE user_id = $1
        ORDER BY preference_type, weight DESC
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            rows = await conn.fetch(query, user_id)

            preferences = []
            for row in rows:
                preferences.append(UserPreference(
                    type=row['preference_type'],
                    value=row['preference_value'],
                    weight=row['weight']
                ))

            return preferences

    async def add_user_preference(self, user_id: UUID, preference: AddPreferenceRequest) -> bool:
        """添加用户偏好"""
        query = """
        INSERT INTO user_preferences (user_id, preference_type, preference_value, weight)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, preference_type, preference_value)
        DO UPDATE SET weight = $4, updated_at = CURRENT_TIMESTAMP
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(
                query, user_id, preference.type, preference.value, preference.weight
            )
            return "INSERT" in result or "UPDATE" in result

    async def remove_user_preference(self, user_id: UUID, preference_type: str, preference_value: str) -> bool:
        """删除用户偏好"""
        query = """
        DELETE FROM user_preferences
        WHERE user_id = $1 AND preference_type = $2 AND preference_value = $3
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(query, user_id, preference_type, preference_value)
            return result == "DELETE 1"

    async def get_current_mood(self, user_id: UUID) -> Optional[UserMood]:
        """获取用户当前情绪"""
        query = """
        SELECT mood, intensity, context, created_at
        FROM user_mood_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            row = await conn.fetchrow(query, user_id)

            if row:
                return UserMood(
                    mood=row['mood'],
                    intensity=row['intensity'],
                    context=row['context'],
                    created_at=row['created_at']
                )

            return None

    async def add_mood_record(self, user_id: UUID, mood_data: UpdateMoodRequest) -> bool:
        """添加情绪记录"""
        query = """
        INSERT INTO user_mood_history (user_id, mood, intensity, context)
        VALUES ($1, $2, $3, $4)
        """

        conn_ctx = await self.db.get_connection()
        async with conn_ctx as conn:            
            result = await conn.execute(
                query, user_id, mood_data.mood, mood_data.intensity, mood_data.context
            )
            return "INSERT" in result
