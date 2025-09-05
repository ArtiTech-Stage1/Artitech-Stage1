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
CLERK_JWT_VERIFICATION_URL = "https://api.clerk.dev/v1/jwks"

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
        """验证 JWT token"""
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
            logger.error(f"Token 验证异常: {e}")
            raise HTTPException(status_code=500, detail="认证验证失败")
    
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
    """获取当前认证用户"""
    if not credentials:
        raise HTTPException(status_code=401, detail="需要认证")
    
    # 验证 token
    payload = await clerk_auth.verify_token(credentials.credentials)
    
    # 从 payload 中提取用户信息
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
