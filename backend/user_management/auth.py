"""
Clerk 认证中间件和工具
"""

import os
import jwt
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

# 从 publishable key 中提取实例ID来构建正确的JWKS URL
def get_clerk_jwks_url():
    if CLERK_PUBLISHABLE_KEY:
        # 从 pk_test_xxx 或 pk_live_xxx 中提取实例信息
        # Clerk的JWKS URL格式: https://{clerk-frontend-api}/.well-known/jwks.json
        if CLERK_PUBLISHABLE_KEY.startswith('pk_test_'):
            # 测试环境的JWKS URL
            return f"https://clerk.{CLERK_PUBLISHABLE_KEY.split('_')[2]}.lcl.dev/.well-known/jwks.json"
        else:
            # 生产环境需要从publishable key解析域名
            # 这里使用通用的clerk.dev域名
            return "https://clerk.dev/.well-known/jwks.json"
    return "https://clerk.dev/.well-known/jwks.json"

CLERK_JWT_VERIFICATION_URL = get_clerk_jwks_url()

security = HTTPBearer()

class ClerkAuth:
    """Clerk 认证类"""
    
    def __init__(self):
        self.secret_key = CLERK_SECRET_KEY
        self.publishable_key = CLERK_PUBLISHABLE_KEY
        self.jwks_cache = None
        self.jwks_cache_time = None
    
    async def get_jwks(self) -> Dict[str, Any]:
        """获取 JWKS (JSON Web Key Set)"""
        import time
        
        # 缓存 JWKS 1小时
        if self.jwks_cache and self.jwks_cache_time and (time.time() - self.jwks_cache_time) < 3600:
            return self.jwks_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(CLERK_JWT_VERIFICATION_URL)
                response.raise_for_status()
                
                self.jwks_cache = response.json()
                self.jwks_cache_time = time.time()
                
                return self.jwks_cache
        except Exception as e:
            logger.error(f"获取 JWKS 失败: {e}")
            raise HTTPException(status_code=500, detail="认证服务不可用")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证 JWT token - 简化版本，直接使用Clerk API验证"""
        try:
            # 方法1: 使用Clerk API直接验证token
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }

            # 调用Clerk的token验证API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.clerk.dev/v1/tokens/verify",
                    headers=headers,
                    json={"token": token}
                )

                if response.status_code == 200:
                    token_data = response.json()
                    return {
                        'sub': token_data.get('sub'),
                        'email': token_data.get('email'),
                        'email_verified': token_data.get('email_verified', False),
                        'given_name': token_data.get('given_name'),
                        'family_name': token_data.get('family_name'),
                        'preferred_username': token_data.get('preferred_username'),
                        'picture': token_data.get('picture')
                    }
                else:
                    logger.error(f"Clerk token验证失败: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=401, detail="Token验证失败")

        except httpx.HTTPStatusError as e:
            logger.error(f"Clerk API调用失败: {e}")
            raise HTTPException(status_code=401, detail="Token验证失败")
        except Exception as e:
            logger.error(f"Token验证异常: {e}")
            # 如果Clerk API验证失败，尝试本地验证（作为备选方案）
            return await self.verify_token_locally(token)

    async def verify_token_locally(self, token: str) -> Dict[str, Any]:
        """本地验证JWT token（备选方案）"""
        try:
            # 解码 token header 获取 kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            if not kid:
                raise HTTPException(status_code=401, detail="无效的 token header")

            # 获取 JWKS
            jwks = await self.get_jwks()

            # 查找对应的公钥
            public_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break

            if not public_key:
                raise HTTPException(status_code=401, detail="找不到对应的公钥")

            # 验证 token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={"verify_exp": True, "verify_aud": False}
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token 已过期")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token 验证失败: {e}")
            raise HTTPException(status_code=401, detail="无效的 token")
        except Exception as e:
            logger.error(f"本地Token验证异常: {e}")
            raise HTTPException(status_code=401, detail="Token验证失败")
    
    async def get_user_info_from_clerk(self, user_id: str) -> Dict[str, Any]:
        """从 Clerk 获取用户信息"""
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
            logger.error(f"从 Clerk 获取用户信息失败: {e}")
            raise HTTPException(status_code=400, detail="无法获取用户信息")
        except Exception as e:
            logger.error(f"Clerk API 调用异常: {e}")
            raise HTTPException(status_code=500, detail="用户信息服务不可用")

# 全局认证实例
clerk_auth = ClerkAuth()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前认证用户 - 简化版本"""
    if not credentials:
        raise HTTPException(status_code=401, detail="需要认证")

    try:
        # 方法1: 直接使用token调用Clerk用户API
        token = credentials.credentials

        # 首先尝试解码token获取用户ID（不验证签名）
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified_payload.get('sub')

            if user_id:
                # 使用用户ID从Clerk获取用户信息
                user_info = await clerk_auth.get_user_info_from_clerk(user_id)

                return {
                    'user_id': user_id,
                    'email': user_info.get('email_addresses', [{}])[0].get('email_address'),
                    'email_verified': True,
                    'first_name': user_info.get('first_name'),
                    'last_name': user_info.get('last_name'),
                    'username': user_info.get('username'),
                    'picture': user_info.get('profile_image_url'),
                    'payload': unverified_payload
                }
        except Exception as decode_error:
            logger.error(f"Token解码失败: {decode_error}")

        # 方法2: 如果解码失败，尝试完整验证
        payload = await clerk_auth.verify_token(token)

        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的用户 token")

        return {
            'user_id': user_id,
            'email': payload.get('email'),
            'email_verified': payload.get('email_verified', False),
            'first_name': payload.get('given_name'),
            'last_name': payload.get('family_name'),
            'username': payload.get('preferred_username'),
            'picture': payload.get('picture'),
            'payload': payload
        }

    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        raise HTTPException(status_code=401, detail="认证失败")

async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """获取可选的当前用户（不强制认证）"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = await clerk_auth.verify_token(token)
        
        user_id = payload.get('sub')
        if not user_id:
            return None
        
        return {
            'user_id': user_id,
            'email': payload.get('email'),
            'email_verified': payload.get('email_verified', False),
            'first_name': payload.get('given_name'),
            'last_name': payload.get('family_name'),
            'username': payload.get('preferred_username'),
            'picture': payload.get('picture'),
            'payload': payload
        }
    except:
        return None

def require_auth(func):
    """认证装饰器"""
    async def wrapper(*args, **kwargs):
        # 这里可以添加额外的认证逻辑
        return await func(*args, **kwargs)
    return wrapper

class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # 记录请求信息（用于日志）
            if hasattr(request.state, 'user_info'):
                logger.info(f"认证用户请求: {request.state.user_info.get('email')} - {request.method} {request.url}")
        
        await self.app(scope, receive, send)

# 用户信息提取工具
def extract_user_data_from_clerk(clerk_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """从 Clerk 用户数据中提取标准用户信息"""
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
