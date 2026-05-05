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