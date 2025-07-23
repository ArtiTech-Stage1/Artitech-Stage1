#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def create_database():
    """创建数据库（如果不存在）"""
    
    # 数据库配置
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "artech_db")
    
    print(f"🔗 连接到 PostgreSQL 服务器 {host}:{port}")
    
    try:
        # 连接到默认的 postgres 数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        
        # 检查数据库是否存在
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )
        
        if exists:
            print(f"✅ 数据库 '{database}' 已存在")
        else:
            # 创建数据库
            await conn.execute(f'CREATE DATABASE "{database}"')
            print(f"✅ 数据库 '{database}' 创建成功")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        return False

async def run_schema_script():
    """运行数据库架构脚本"""
    
    # 数据库配置
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "artech_db")
    
    # 读取 SQL 脚本
    script_path = Path(__file__).parent / "schema.sql"
    
    if not script_path.exists():
        print(f"❌ SQL 脚本文件不存在: {script_path}")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print(f"📄 读取 SQL 脚本: {script_path}")
        
        # 连接到目标数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print(f"🔗 连接到数据库 '{database}'")
        
        # 执行 SQL 脚本
        await conn.execute(sql_script)
        print("✅ 数据库架构创建成功")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库架构创建失败: {e}")
        return False

async def test_connection():
    """测试数据库连接"""
    
    # 数据库配置
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "artech_db")
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # 测试查询
        result = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"✅ 数据库连接测试成功，用户表记录数: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def check_environment():
    """检查环境变量"""
    required_vars = [
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少必需的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请在 .env 文件中配置这些变量")
        return False
    
    print("✅ 环境变量检查通过")
    return True

async def main():
    """主函数"""
    print("=" * 50)
    print("🚀 艺术品推荐系统 - 数据库初始化")
    print("=" * 50)
    
    # 检查环境变量
    if not check_environment():
        sys.exit(1)
    
    print("\n📋 初始化步骤:")
    print("1. 创建数据库")
    print("2. 运行架构脚本")
    print("3. 测试连接")
    print()
    
    # 步骤 1: 创建数据库
    print("🔄 步骤 1: 创建数据库...")
    if not await create_database():
        print("❌ 数据库创建失败，终止初始化")
        sys.exit(1)
    
    # 步骤 2: 运行架构脚本
    print("\n🔄 步骤 2: 运行架构脚本...")
    if not await run_schema_script():
        print("❌ 架构脚本执行失败，终止初始化")
        sys.exit(1)
    
    # 步骤 3: 测试连接
    print("\n🔄 步骤 3: 测试数据库连接...")
    if not await test_connection():
        print("❌ 数据库连接测试失败")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 数据库初始化完成！")
    print("=" * 50)
    print("\n📝 下一步:")
    print("1. 配置 Clerk 认证密钥")
    print("2. 配置 Gemini API 密钥")
    print("3. 启动应用: python main.py")

if __name__ == "__main__":
    asyncio.run(main())
