"""
数据库配置模块
"""

import os
import asyncpg
import asyncio
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "artech_db")
        self.username = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")
        self.min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
        
    @property
    def connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        required_fields = [self.host, self.database, self.username]
        return all(field for field in required_fields)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=60
            )
            logger.info("数据库连接池初始化成功")
            
            # 测试连接
            async with self.pool.acquire() as connection:
                await connection.execute("SELECT 1")
            logger.info("数据库连接测试成功")
            
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("数据库连接池已关闭")
    
    async def get_connection(self):
        """获取数据库连接"""
        if not self.pool:
            raise RuntimeError("数据库连接池未初始化")
        return self.pool.acquire()
    
    async def execute_query(self, query: str, *args):
        """执行查询"""
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """执行命令（INSERT, UPDATE, DELETE）"""
        async with self.pool.acquire() as connection:
            return await connection.execute(command, *args)
    
    async def execute_transaction(self, commands: list):
        """执行事务"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for command, args in commands:
                    result = await connection.execute(command, *args)
                    results.append(result)
                return results

# 全局数据库管理器实例
db_config = DatabaseConfig()
db_manager = DatabaseManager(db_config)

async def init_database():
    """初始化数据库"""
    await db_manager.initialize()

async def close_database():
    """关闭数据库连接"""
    await db_manager.close()

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return db_manager
