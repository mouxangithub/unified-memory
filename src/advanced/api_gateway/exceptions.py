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