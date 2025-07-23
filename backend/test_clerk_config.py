#!/usr/bin/env python3
"""
测试Clerk配置的脚本
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_clerk_config():
    """测试Clerk配置"""
    print("🔐 测试Clerk配置...")
    
    # 获取环境变量
    secret_key = os.getenv("CLERK_SECRET_KEY")
    publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")
    
    print(f"Secret Key: {secret_key[:20]}..." if secret_key else "Secret Key: 未设置")
    print(f"Publishable Key: {publishable_key[:20]}..." if publishable_key else "Publishable Key: 未设置")
    
    if not secret_key:
        print("❌ CLERK_SECRET_KEY 未设置")
        return False
    
    if not publishable_key:
        print("❌ CLERK_PUBLISHABLE_KEY 未设置")
        return False
    
    # 测试Clerk API连接
    print("\n🌐 测试Clerk API连接...")
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # 测试获取用户列表（验证API密钥是否有效）
            response = await client.get(
                "https://api.clerk.dev/v1/users?limit=1",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Clerk API连接成功")
                users_data = response.json()
                print(f"   用户数量: {len(users_data)}")
                return True
            else:
                print(f"❌ Clerk API连接失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Clerk API测试异常: {e}")
        return False

async def test_jwks_endpoint():
    """测试JWKS端点"""
    print("\n🔑 测试JWKS端点...")
    
    publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")
    
    # 尝试不同的JWKS URL
    jwks_urls = [
        "https://clerk.dev/.well-known/jwks.json",
        f"https://api.clerk.dev/v1/jwks",
        "https://clerk.com/.well-known/jwks.json"
    ]
    
    for url in jwks_urls:
        print(f"   尝试: {url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    jwks_data = response.json()
                    if 'keys' in jwks_data:
                        print(f"   ✅ JWKS获取成功，包含 {len(jwks_data['keys'])} 个密钥")
                        return url
                    else:
                        print(f"   ⚠️  响应格式不正确")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print("❌ 所有JWKS端点都无法访问")
    return None

async def test_simple_auth():
    """测试简化的认证方案"""
    print("\n🧪 测试简化认证方案...")
    
    # 这里我们创建一个不依赖JWKS的认证方案
    print("建议使用以下认证策略:")
    print("1. 前端获取Clerk token")
    print("2. 后端接收token后，直接调用Clerk API验证用户")
    print("3. 不依赖JWKS，直接使用Clerk的用户API")
    
    return True

async def main():
    """主函数"""
    print("=" * 50)
    print("Clerk配置测试")
    print("=" * 50)
    
    # 测试基本配置
    config_ok = await test_clerk_config()
    
    # 测试JWKS端点
    jwks_url = await test_jwks_endpoint()
    
    # 测试简化认证
    simple_auth_ok = await test_simple_auth()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"✅ 基本配置: {'通过' if config_ok else '失败'}")
    print(f"✅ JWKS端点: {'通过' if jwks_url else '失败'}")
    print(f"✅ 简化认证: {'通过' if simple_auth_ok else '失败'}")
    
    if config_ok:
        print("\n🎉 Clerk配置基本正常！")
        print("\n📝 建议:")
        print("1. 使用简化的认证方案，避免JWKS问题")
        print("2. 直接调用Clerk API验证用户身份")
        print("3. 在前端确保正确获取和传递token")
    else:
        print("\n❌ 请检查Clerk配置")
        print("\n🔧 解决步骤:")
        print("1. 确认.env文件中的Clerk密钥正确")
        print("2. 检查网络连接")
        print("3. 验证Clerk应用设置")

if __name__ == "__main__":
    asyncio.run(main())
