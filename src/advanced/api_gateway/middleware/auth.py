"""
认证中间件
支持 JWT Bearer Token 和 API Key 两种认证方式
"""

import time
import hashlib
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from ..config import get_settings
from ..exceptions import (
    AuthenticationError,
    InvalidTokenError,
    MissingTokenError,
    InvalidAPIKeyError,
)


settings = get_settings()


class TokenPayload(BaseModel):
    """JWT 载荷"""
    sub: str  # 用户ID
    exp: int  # 过期时间戳
    iat: int  # 签发时间戳
    scopes: list[str] = []  # 权限范围


class CurrentUser(BaseModel):
    """当前用户"""
    
    user_id: str
    auth_type: str  # "jwt" or "api_key"
    scopes: list[str] = []
    metadata: dict = {}


# HTTP Bearer 安全方案
bearer_scheme = HTTPBearer(auto_error=False)


def decode_jwt_token(token: str) -> TokenPayload:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def create_jwt_token(
    user_id: str,
    scopes: list[str] = None,
    expires_delta: int = None
) -> str:
    """创建 JWT Token（用于测试）"""
    from datetime import datetime, timedelta
    
    if expires_delta is None:
        expires_delta = settings.JWT_EXPIRATION_MINUTES
    
    now = datetime.utcnow()
    expire = now + timedelta(minutes=expires_delta)
    
    payload = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "scopes": scopes or [],
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_api_key(api_key: str) -> bool:
    """验证 API Key"""
    # 支持 hash 后的 key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # 简单验证：直接匹配或 hash 后匹配
    return (
        api_key in settings.API_KEYS or
        key_hash in [hashlib.sha256(k.encode()).hexdigest() for k in settings.API_KEYS]
    )


async def jwt_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> CurrentUser:
    """JWT Bearer Token 认证"""
    if credentials is None:
        raise MissingTokenError("Bearer token is required")
    
    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Invalid authentication scheme")
    
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    return CurrentUser(
        user_id=payload.sub,
        auth_type="jwt",
        scopes=payload.scopes,
        metadata={"exp": payload.exp, "iat": payload.iat}
    )


async def api_key_auth(request: Request) -> CurrentUser:
    """API Key 认证"""
    api_key = request.headers.get(settings.API_KEY_HEADER)
    
    if not api_key:
        raise MissingTokenError(f"Header {settings.API_KEY_HEADER} is required")
    
    if not verify_api_key(api_key):
        raise InvalidAPIKeyError("Invalid API key")
    
    # API Key 方式不携带用户信息，使用 key 的 hash 作为标识
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
    
    return CurrentUser(
        user_id=f"api_key_{key_hash}",
        auth_type="api_key",
        scopes=["read", "write"],
        metadata={"api_key_suffix": key_hash}
    )


async def get_current_user(
    request: Request,
    jwt_user: Optional[CurrentUser] = Depends(jwt_auth),
) -> CurrentUser:
    """
    获取当前用户
    优先使用 JWT 认证，失败则尝试 API Key
    """
    # 如果 JWT 认证成功
    if jwt_user:
        return jwt_user
    
    # 尝试 API Key 认证
    return await api_key_auth(request)


class AuthMiddleware:
    """认证中间件（依赖注入方式，更灵活）"""
    
    def __init__(
        self,
        optional: bool = False,
        required_scopes: list[str] = None
    ):
        self.optional = optional
        self.required_scopes = required_scopes or []
    
    async def __call__(
        self,
        request: Request,
        call_next
    ):
        # 公开端点跳过认证
        if self._is_public_endpoint(request):
            return await call_next(request)
        
        try:
            # 尝试从请求中获取用户
            user = await self._authenticate(request)
            
            if user:
                # 验证权限范围
                if self.required_scopes:
                    self._check_scopes(user, self.required_scopes)
                
                # 将用户信息存入 request state
                request.state.user = user
            elif not self.optional:
                raise MissingTokenError()
            
        except AuthenticationError:
            raise
        
        response = await call_next(request)
        return response
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """检查是否为公开端点"""
        public_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            f"{settings.API_PREFIX}/health",
        ]
        return request.url.path in public_paths
    
    async def _authenticate(self, request: Request) -> Optional[CurrentUser]:
        """认证"""
        # 优先 JWT
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_jwt_token(token)
            return CurrentUser(
                user_id=payload.sub,
                auth_type="jwt",
                scopes=payload.scopes
            )
        
        # 其次 API Key
        api_key = request.headers.get(settings.API_KEY_HEADER)
        if api_key and verify_api_key(api_key):
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
            return CurrentUser(
                user_id=f"api_key_{key_hash}",
                auth_type="api_key",
                scopes=["read", "write"]
            )
        
        return None
    
    def _check_scopes(self, user: CurrentUser, required: list[str]):
        """检查权限范围"""
        if not any(scope in user.scopes for scope in required):
            from ..exceptions import AuthorizationError
            raise AuthorizationError(f"Required scopes: {required}")