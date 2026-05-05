> ⚡ **核心开发者** | 步骤 3/6 | 166.3s

---

<think>用户要求实现一个完整的 Unified Memory v5 API Gateway 层代码。这是一个 FastAPI 项目，需要包含：

1. 完整的目录结构
2. 所有必需的端点实现
3. JWT 和 API Key 认证
4. 令牌桶限流
5. 日志中间件
6. 统一异常处理
7. OpenAPI 文档

让我逐个文件实现：

1. **config.py** - 配置管理
2. **exceptions.py** - 自定义异常
3. **models/requests.py** - 请求模型
4. **models/responses.py** - 响应模型
5. **middleware/auth.py** - 认证中间件
6. **middleware/rate_limit.py** - 限流中间件
7. **middleware/logging.py** - 日志中间件
8. **routes/memory.py** - 记忆 CRUD 路由
9. **routes/search.py** - 搜索路由
10. **routes/admin.py** - 管理路由
11. **main.py** - 应用入口

我会使用内存存储作为示例，方便运行和测试。实际项目中可以替换为真实的数据库。

让我开始实现完整代码：
</think>

# Unified Memory v5 API Gateway 实现

我来实现完整的 API Gateway 层代码。这是一个可运行的 FastAPI 项目。

## 项目结构

```
memory_v5/api_gateway/
├── __init__.py
├── main.py
├── config.py
├── exceptions.py
├── routes/
│   ├── __init__.py
│   ├── memory.py
│   ├── search.py
│   └── admin.py
├── middleware/
│   ├── __init__.py
│   ├── auth.py
│   ├── rate_limit.py
│   └── logging.py
└── models/
    ├── __init__.py
    ├── requests.py
    └── responses.py
```

---

## 核心配置文件

```python
# memory_v5/api_gateway/__init__.py
"""
Unified Memory v5 API Gateway
基于 FastAPI 的高性能记忆服务网关
"""

__version__ = "5.0.0"
__author__ = "Memory Team"

from .main import app

__all__ = ["app"]
```

```python
# memory_v5/api_gateway/config.py
"""
配置管理模块
支持环境变量配置和环境分离
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Unified Memory v5 Gateway"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    API_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # JWT 配置
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # API Key 配置
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: list[str] = Field(default_factory=lambda: ["test-api-key-1", "test-api-key-2"])
    
    # 限流配置
    RATE_LIMIT_REQUESTS: int = 1000  # 每分钟请求数
    RATE_LIMIT_WINDOW: int = 60  # 时间窗口（秒）
    RATE_LIMIT_BUCKET_SIZE: int = 1000  # 令牌桶容量
    
    # 存储配置（可扩展为数据库连接）
    STORAGE_BACKEND: str = "memory"  # memory, redis, postgres
    STORAGE_TTL_DAYS: int = 90
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    LOG_FILE: Optional[str] = None
    
    # OpenAPI 配置
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class SettingsFactory:
    """配置工厂"""
    
    _settings: Optional[Settings] = None
    
    @classmethod
    def get_settings(cls) -> Settings:
        if cls._settings is None:
            env = os.getenv("ENV", "development")
            if env == "production":
                cls._settings = ProductionSettings()
            elif env == "development":
                cls._settings = DevelopmentSettings()
            else:
                cls._settings = Settings()
        return cls._settings
    
    @classmethod
    def reset(cls):
        """重置配置（用于测试）"""
        cls._settings = None


def get_settings() -> Settings:
    """获取配置的单例"""
    return SettingsFactory.get_settings()


# 全局配置实例
settings = get_settings()
```

---

## 异常定义

```python
# memory_v5/api_gateway/exceptions.py
"""
统一错误码体系 (1000-1999)

错误码分配：
- 1000-1099: 通用错误
- 1100-1199: 认证授权错误
- 1200-1299: 验证错误
- 1300-1399: 资源错误
- 1400-1499: 限流错误
- 1500-1599: 服务错误
"""

from typing import Any, Optional
from fastapi import HTTPException, status


class BaseMemoryException(Exception):
    """基础异常类"""
    
    code: int = 1000
    message: str = "Unknown error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Any] = None,
        code: Optional[int] = None
    ):
        self.message = message or self.__class__.message
        self.details = details
        if code is not None:
            self.code = code
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail={
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        )


# ============ 通用错误 (1000-1099) ============

class InternalServerError(BaseMemoryException):
    """内部服务器错误"""
    code = 1000
    message = "Internal server error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ServiceUnavailableError(BaseMemoryException):
    """服务不可用"""
    code = 1001
    message = "Service temporarily unavailable"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


# ============ 认证授权错误 (1100-1199) ============

class AuthenticationError(BaseMemoryException):
    """认证失败"""
    code = 1100
    message = "Authentication failed"
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidTokenError(AuthenticationError):
    """无效的令牌"""
    code = 1101
    message = "Invalid or expired token"


class MissingTokenError(AuthenticationError):
    """缺少认证令牌"""
    code = 1102
    message = "Authentication token is required"


class InvalidAPIKeyError(AuthenticationError):
    """无效的 API Key"""
    code = 1103
    message = "Invalid API key"


class AuthorizationError(BaseMemoryException):
    """权限不足"""
    code = 1200
    message = "Insufficient permissions"
    status_code = status.HTTP_403_FORBIDDEN


# ============ 验证错误 (1200-1299) ============

class ValidationError(BaseMemoryException):
    """请求验证错误"""
    code = 1200
    message = "Request validation failed"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class InvalidParameterError(ValidationError):
    """参数无效"""
    code = 1201
    message = "Invalid parameter"


# ============ 资源错误 (1300-1399) ============

class MemoryNotFoundError(BaseMemoryException):
    """记忆不存在"""
    code = 1300
    message = "Memory not found"
    status_code = status.HTTP_404_NOT_FOUND


class NamespaceNotFoundError(BaseMemoryException):
    """命名空间不存在"""
    code = 1301
    message = "Namespace not found"
    status_code = status.HTTP_404_NOT_FOUND


class VersionNotFoundError(BaseMemoryException):
    """版本不存在"""
    code = 1302
    message = "Memory version not found"
    status_code = status.HTTP_404_NOT_FOUND


class MemoryAlreadyExistsError(BaseMemoryException):
    """记忆已存在"""
    code = 1303
    message = "Memory already exists"
    status_code = status.HTTP_409_CONFLICT


# ============ 限流错误 (1400-1499) ============

class RateLimitError(BaseMemoryException):
    """请求频率超限"""
    code = 1400
    message = "Rate limit exceeded. Please try again later."
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


# ============ 服务错误 (1500-1599) ============

class StorageError(BaseMemoryException):
    """存储服务错误"""
    code = 1500
    message = "Storage service error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class VectorSearchError(BaseMemoryException):
    """向量搜索服务错误"""
    code = 1501
    message = "Vector search service error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# ============ 异常处理注册表 ============

EXCEPTION_HANDLERS = {
    MemoryNotFoundError: lambda exc: exc.to_http_exception(),
    NamespaceNotFoundError: lambda exc: exc.to_http_exception(),
    VersionNotFoundError: lambda exc: exc.to_http_exception(),
    MemoryAlreadyExistsError: lambda exc: exc.to_http_exception(),
    ValidationError: lambda exc: exc.to_http_exception(),
    InvalidParameterError: lambda exc: exc.to_http_exception(),
    RateLimitError: lambda exc: exc.to_http_exception(),
    AuthenticationError: lambda exc: exc.to_http_exception(),
    InvalidTokenError: lambda exc: exc.to_http_exception(),
    MissingTokenError: lambda exc: exc.to_http_exception(),
    InvalidAPIKeyError: lambda exc: exc.to_http_exception(),
    AuthorizationError: lambda exc: exc.to_http_exception(),
    InternalServerError: lambda exc: exc.to_http_exception(),
    ServiceUnavailableError: lambda exc: exc.to_http_exception(),
    StorageError: lambda exc: exc.to_http_exception(),
    VectorSearchError: lambda exc: exc.to_http_exception(),
}
```

---

## 数据模型

```python
# memory_v5/api_gateway/models/__init__.py
"""数据模型包"""

from .requests import (
    CreateMemoryRequest,
    UpdateMemoryRequest,
    SearchMemoryRequest,
)
from .responses import (
    BaseResponse,
    MemoryResponse,
    MemoryListResponse,
    MemoryVersionResponse,
    NamespaceStatsResponse,
    SearchResultResponse,
    ErrorResponse,
)

__all__ = [
    "CreateMemoryRequest",
    "UpdateMemoryRequest",
    "SearchMemoryRequest",
    "BaseResponse",
    "MemoryResponse",
    "MemoryListResponse",
    "MemoryVersionResponse",
    "NamespaceStatsResponse",
    "SearchResultResponse",
    "ErrorResponse",
]
```

```python
# memory_v5/api_gateway/models/requests.py
"""
请求模型定义
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class CreateMemoryRequest(BaseModel):
    """创建记忆请求"""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="记忆内容",
        examples=["This is a memory about project planning"]
    )
    
    namespace: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="命名空间，用于组织和隔离记忆",
        examples=["default", "project-alpha", "user_123"]
    )
    
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="记忆元数据",
        examples=[{"type": "note", "tags": ["important"]}]
    )
    
    tags: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="记忆标签",
        examples=[["work", "priority"]]
    )
    
    embedding_model: Optional[str] = Field(
        default=None,
        description="向量嵌入模型",
        examples=["text-embedding-3-small"]
    )
    
    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        if v.startswith("-") or v.startswith("_"):
            raise ValueError("Namespace cannot start with - or _")
        return v.lower()


class UpdateMemoryRequest(BaseModel):
    """更新记忆请求"""
    
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100000,
        description="记忆内容"
    )
    
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="记忆元数据"
    )
    
    tags: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="记忆标签"
    )
    
    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


class SearchMemoryRequest(BaseModel):
    """搜索记忆请求"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="搜索查询语句"
    )
    
    namespace: Optional[str] = Field(
        default=None,
        max_length=128,
        description="限定命名空间"
    )
    
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="返回结果数量限制"
    )
    
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="是否返回元数据"
    )
    
    rerank: bool = Field(
        default=False,
        description="是否启用重排序"
    )
```

```python
# memory_v5/api_gateway/models/responses.py
"""
响应模型定义
"""

from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    """基础响应"""
    
    code: int = Field(default=0, description="业务状态码，0表示成功")
    message: str = Field(default="Success", description="响应消息")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")


class MemoryResponse(BaseResponse):
    """记忆响应"""
    
    data: Optional["MemoryData"] = Field(default=None, description="记忆数据")


class MemoryData(BaseModel):
    """记忆数据"""
    
    id: str = Field(..., description="记忆唯一ID")
    content: str = Field(..., description="记忆内容")
    namespace: str = Field(..., description="命名空间")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="元数据")
    tags: Optional[list[str]] = Field(default=None, description="标签")
    version: int = Field(..., description="当前版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(default=None, description="创建者")
    
    model_config = {"from_attributes": True}


class MemoryListResponse(BaseResponse):
    """记忆列表响应"""
    
    data: Optional["MemoryListData"] = Field(default=None, description="记忆列表数据")


class MemoryListData(BaseModel):
    """记忆列表数据"""
    
    items: list[MemoryData] = Field(default_factory=list, description="记忆列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")


class MemoryVersionResponse(BaseResponse):
    """记忆版本响应"""
    
    data: Optional["MemoryVersionData"] = Field(default=None, description="版本数据")


class MemoryVersionData(BaseModel):
    """记忆版本数据"""
    
    memory_id: str = Field(..., description="记忆ID")
    current_version: int = Field(..., description="当前版本")
    versions: list["VersionItem"] = Field(default_factory=list, description="版本列表")


class VersionItem(BaseModel):
    """版本项"""
    
    version: int = Field(..., description="版本号")
    content: str = Field(..., description="该版本的内容")
    created_at: datetime = Field(..., description="版本创建时间")
    created_by: Optional[str] = Field(default=None, description="操作者")


class NamespaceStatsResponse(BaseResponse):
    """命名空间统计响应"""
    
    data: Optional["NamespaceStatsData"] = Field(default=None, description="统计数据")


class NamespaceStatsData(BaseModel):
    """命名空间统计数据"""
    
    namespace: str = Field(..., description="命名空间")
    total_memories: int = Field(..., description="记忆总数")
    total_versions: int = Field(..., description="版本总数")
    avg_version_per_memory: float = Field(..., description="平均每条记忆的版本数")
    storage_size_bytes: int = Field(..., description="存储大小（字节）")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    top_tags: list["TagCount"] = Field(default_factory=list, description="热门标签")


class TagCount(BaseModel):
    """标签统计"""
    
    tag: str = Field(..., description="标签名")
    count: int = Field(..., description="出现次数")


class SearchResultResponse(BaseResponse):
    """搜索结果响应"""
    
    data: Optional["SearchResultData"] = Field(default=None, description="搜索结果")


class SearchResultData(BaseModel):
    """搜索结果数据"""
    
    query: str = Field(..., description="搜索查询")
    total: int = Field(default=0, description="匹配总数")
    results: list["SearchResultItem"] = Field(default_factory=list, description="结果列表")
    search_time_ms: float = Field(..., description="搜索耗时（毫秒）")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    namespace: str = Field(..., description="命名空间")
    score: float = Field(..., description="相似度分数")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="元数据")
    highlights: Optional[list[str]] = Field(default=None, description="高亮片段")


class ErrorResponse(BaseModel):
    """错误响应"""
    
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(default=None, description="详细错误信息")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")


# 更新正向引用
MemoryResponse.model_rebuild()
MemoryListResponse.model_rebuild()
MemoryVersionResponse.model_rebuild()
NamespaceStatsResponse.model_rebuild()
SearchResultResponse.model_rebuild()
```

---

## 中间件

```python
# memory_v5/api_gateway/middleware/__init__.py
"""中间件包"""

from .auth import AuthMiddleware, get_current_user, jwt_auth, api_key_auth
from .rate_limit import RateLimitMiddleware, TokenBucket
from .logging import LoggingMiddleware, RequestLogger

__all__ = [
    "AuthMiddleware",
    "get_current_user",
    "jwt_auth",
    "api_key_auth",
    "RateLimitMiddleware",
    "TokenBucket",
    "LoggingMiddleware",
    "RequestLogger",
]
```

```python
# memory_v5/api_gateway/middleware/auth.py
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
```

```python
# memory_v5/api_gateway/middleware/rate_limit.py
"""
令牌桶限流中间件
支持按用户/IP/命名空间限流
"""

import time
import asyncio
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field
from collections import defaultdict

from fastapi import Request, HTTPException, status

from ..config import get_settings
from ..exceptions import RateLimitError


settings = get_settings()


@dataclass
class TokenBucket:
    """
    令牌桶实现
    
    令牌桶算法特点：
    - 允许一定程度的突发流量
    - 长期来看，速率恒定
    - 桶容量 = burst capacity
    - 补充速率 = sustained rate
    """
    
    capacity: int  # 桶容量
    refill_rate: float  # 每秒补充的令牌数
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # 根据时间流逝补充令牌
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        尝试消耗令牌
        
        Returns:
            True: 成功获取令牌
            False: 令牌不足
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """获取需要等待的时间（秒）"""
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate
    
    @property
    def available_tokens(self) -> int:
        """当前可用令牌数"""
        self._refill()
        return int(self.tokens)


class RateLimitManager:
    """限流管理器"""
    
    def __init__(
        self,
        requests_per_minute: int = 1000,
        bucket_size: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # 每秒补充的令牌数
        self.bucket_size = bucket_size
        
        # 存储桶：key -> TokenBucket
        self._buckets: Dict[str, TokenBucket] = {}
        
        # 清理过期桶的任务
        self._cleanup_interval = 300  # 5分钟清理一次
        self._last_cleanup = time.time()
        
        # 统计数据
        self._stats = {
            "total_requests": 0,
            "total_allowed": 0,
            "total_rejected": 0,
        }
    
    def _get_bucket_key(self, request: Request) -> str:
        """获取桶的 key"""
        # 优先使用用户 ID
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.user_id}"
        
        # 其次使用 API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hash(api_key)}"
        
        # 最后使用 IP
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先从 X-Forwarded-For 获取
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 最后使用直接连接的 IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_or_create_bucket(self, key: str) -> TokenBucket:
        """获取或创建桶"""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self.bucket_size,
                refill_rate=self.refill_rate
            )
        return self._buckets[key]
    
    def _cleanup_expired_buckets(self) -> None:
        """清理过期的桶"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        # 清理空桶
        expired_keys = [
            key for key, bucket in self._buckets.items()
            if bucket.tokens >= bucket.capacity and 
            now - bucket.last_refill > 3600  # 1小时无活动的桶
        ]
        
        for key in expired_keys:
            del self._buckets[key]
        
        self._last_cleanup = now
    
    def check_rate_limit(
        self,
        request: Request,
        tokens: int = 1
    ) -> tuple[bool, dict]:
        """
        检查限流
        
        Returns:
            (allowed, info): 是否允许，限流信息
        """
        self._cleanup_expired_buckets()
        
        key = self._get_bucket_key(request)
        bucket = self._get_or_create_bucket(key)
        
        self._stats["total_requests"] += 1
        
        allowed = bucket.consume(tokens)
        
        if allowed:
            self._stats["total_allowed"] += 1
        else:
            self._stats["total_rejected"] += 1
        
        info = {
            "limit": self.requests_per_minute,
            "remaining": bucket.available_tokens,
            "reset": int(time.time() + bucket.get_wait_time()),
            "key": key,
        }
        
        return allowed, info
    
    def get_stats(self) -> dict:
        """获取限流统计"""
        return {
            **self._stats,
            "active_buckets": len(self._buckets),
            "requests_per_minute": self.requests_per_minute,
        }


# 全局限流管理器实例
rate_limit_manager = RateLimitManager(
    requests_per_minute=settings.RATE_LIMIT_REQUESTS,
    bucket_size=settings.RATE_LIMIT_BUCKET_SIZE
)


class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(
        self,
        requests_per_minute: int = None,
        bucket_size: int = None
    ):
        self.manager = rate_limit_manager
        
        if requests_per_minute:
            self.manager.requests_per_minute = requests_per_minute
        if bucket_size:
            self.manager.bucket_size = bucket_size
    
    async def __call__(
        self,
        request: Request,
        call_next
    ):
        # 公开端点跳过限流
        if self._is_public_endpoint(request):
            return await call_next(request)
        
        allowed, info = self.manager.check_rate_limit(request)
        
        # 构建响应头
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
        }
        
        if not allowed:
            wait_time = self.manager._buckets[info["key"]].get_wait_time()
            headers["Retry-After"] = str(int(wait_time) + 1)
            
            raise RateLimitError(
                message=f"Rate limit exceeded. Retry after {int(wait_time)} seconds.",
                details={
                    "limit": info["limit"],
                    "retry_after": int(wait_time) + 1,
                }
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加限流头
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """检查是否为公开端点"""
        public_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        return request.url.path in public_paths


def rate_limit(requests_per_minute: int = None):
    """限流装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            manager = RateLimitManager(
                requests_per_minute=requests_per_minute or settings.RATE_LIMIT_REQUESTS,
                bucket_size=settings.RATE_LIMIT_BUCKET_SIZE
            )
            
            allowed, info = manager.check_rate_limit(request)
            
            if not allowed:
                wait_time = manager._buckets[info["key"]].get_wait_time()
                raise RateLimitError(
                    details={
                        "limit": info["limit"],
                        "retry_after": int(wait_time) + 1,
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# 兼容 asyncio.wraps
from functools import wraps as async_wraps
```

```python
# memory_v5/api_gateway/middleware/logging.py
"""
请求日志中间件
记录请求/响应的详细信息
"""

import time
import uuid
import json
import sys
from typing import Optional
from datetime import datetime
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from enum import Enum

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..config import get_settings


settings = get_settings()

# 请求 ID 的上下文变量
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


