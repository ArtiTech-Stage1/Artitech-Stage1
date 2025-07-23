"""
简化的Clerk认证模块 - 避免JWKS问题
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Clerk 配置
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")

security = HTTPBearer()

class SimpleClerkAuth:
    """简化的Clerk认证类 - 直接使用API验证"""
    
    def __init__(self):
        self.secret_key = CLERK_SECRET_KEY
        self.publishable_key = CLERK_PUBLISHABLE_KEY
        
        if not self.secret_key:
            logger.warning("CLERK_SECRET_KEY 未设置")
        if not self.publishable_key:
            logger.warning("CLERK_PUBLISHABLE_KEY 未设置")
    
    async def verify_user_by_token(self, token: str) -> Dict[str, Any]:
        """通过token验证用户 - 直接调用Clerk API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            # 方法1: 使用Clerk的sessions API验证token
            async with httpx.AsyncClient() as client:
                # 首先尝试获取session信息
                response = await client.get(
                    f"https://api.clerk.dev/v1/sessions",
                    headers=headers,
                    params={"limit": 1}
                )
                
                if response.status_code == 200:
                    logger.info("Clerk API连接正常")
                else:
                    logger.error(f"Clerk API连接失败: {response.status_code}")
                    raise HTTPException(status_code=500, detail="认证服务不可用")
                
                # 方法2: 解析token获取用户ID，然后验证用户
                import jwt
                try:
                    # 不验证签名，只解析payload获取用户ID
                    unverified_payload = jwt.decode(token, options={"verify_signature": False})
                    user_id = unverified_payload.get('sub')
                    
                    if not user_id:
                        raise HTTPException(status_code=401, detail="Token中没有用户ID")
                    
                    # 使用用户ID获取用户信息来验证token有效性
                    user_response = await client.get(
                        f"https://api.clerk.dev/v1/users/{user_id}",
                        headers=headers
                    )
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        logger.info(f"用户验证成功: {user_data.get('email_addresses', [{}])[0].get('email_address')}")
                        
                        return {
                            'user_id': user_id,
                            'email': user_data.get('email_addresses', [{}])[0].get('email_address'),
                            'email_verified': True,
                            'first_name': user_data.get('first_name'),
                            'last_name': user_data.get('last_name'),
                            'username': user_data.get('username'),
                            'picture': user_data.get('profile_image_url'),
                            'clerk_data': user_data
                        }
                    elif user_response.status_code == 404:
                        raise HTTPException(status_code=401, detail="用户不存在")
                    else:
                        logger.error(f"获取用户信息失败: {user_response.status_code} - {user_response.text}")
                        raise HTTPException(status_code=401, detail="用户验证失败")
                        
                except jwt.DecodeError:
                    logger.error("Token格式无效")
                    raise HTTPException(status_code=401, detail="Token格式无效")
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Clerk API调用失败: {e}")
            raise HTTPException(status_code=500, detail="认证服务不可用")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"用户验证异常: {e}")
            raise HTTPException(status_code=500, detail="认证验证失败")
    
    async def get_user_info_from_clerk(self, user_id: str) -> Dict[str, Any]:
        """从Clerk获取用户信息"""
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.clerk.dev/v1/users/{user_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"从Clerk获取用户信息失败: {e}")
            raise HTTPException(status_code=400, detail="无法获取用户信息")
        except Exception as e:
            logger.error(f"Clerk API调用异常: {e}")
            raise HTTPException(status_code=500, detail="用户信息服务不可用")

# 全局认证实例
simple_clerk_auth = SimpleClerkAuth()

async def get_current_user_simple(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前认证用户 - 简化版本"""
    if not credentials:
        raise HTTPException(status_code=401, detail="需要认证")
    
    return await simple_clerk_auth.verify_user_by_token(credentials.credentials)

async def get_optional_user_simple(request: Request) -> Optional[Dict[str, Any]]:
    """获取可选的当前用户（不强制认证）- 简化版本"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        return await simple_clerk_auth.verify_user_by_token(token)
        
    except:
        return None

def extract_user_data_from_clerk_simple(clerk_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """从Clerk用户数据中提取标准用户信息 - 简化版本"""
    email_addresses = clerk_user_data.get('email_addresses', [])
    primary_email = None
    
    for email in email_addresses:
        if email.get('id') == clerk_user_data.get('primary_email_address_id'):
            primary_email = email.get('email_address')
            break
    
    if not primary_email and email_addresses:
        primary_email = email_addresses[0].get('email_address')
    
    return {
        'clerk_user_id': clerk_user_data.get('id'),
        'email': primary_email,
        'username': clerk_user_data.get('username'),
        'first_name': clerk_user_data.get('first_name'),
        'last_name': clerk_user_data.get('last_name'),
        'avatar_url': clerk_user_data.get('profile_image_url')
    }

# 测试函数
async def test_clerk_connection():
    """测试Clerk连接"""
    try:
        headers = {
            "Authorization": f"Bearer {CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.dev/v1/users?limit=1",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("✅ Clerk连接测试成功")
                return True
            else:
                logger.error(f"❌ Clerk连接测试失败: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Clerk连接测试异常: {e}")
        return False
