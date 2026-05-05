"""
Unified Memory v5 - 多级缓存抽象基类定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar, Optional, Dict
import threading
import time

T = TypeVar('T')


class CacheLevelType(Enum):
    """缓存层级类型"""
    L1_MEMORY = "l1_memory"      # 进程内 LRU
    L2_REDIS = "l2_redis"        # Redis 分布式缓存
    L3_VECTOR = "l3_vector"      # Qdrant 向量缓存


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    evicted: int = 0  # 因容量/TTL 淘汰的数量
    total_requests: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """计算命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        """平均延迟(ms)"""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "evicted": self.evicted,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 4),
        }


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    version: str = "1"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def ttl_remaining(self) -> Optional[float]:
        """剩余 TTL 秒数"""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0, remaining)
    
    @classmethod
    def create(cls, key: str, value: T, ttl: Optional[int] = None, 
               version: str = "1", metadata: Optional[Dict] = None) -> 'CacheEntry[T]':
        """创建缓存条目"""
        expires_at = None
        if ttl is not None and ttl > 0:
            expires_at = time.time() + ttl
        
        return cls(
            key=key,
            value=value,
            expires_at=expires_at,
            version=version,
            metadata=metadata or {}
        )


@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 1000              # L1 最大容量
    default_ttl: int = 3600           # 默认 TTL（秒）
    l1_ttl: int = 300                 # L1 TTL（秒）
    l2_ttl: int = 3600                # L2 TTL（秒）
    l3_ttl: int = 86400               # L3 TTL（秒）
    enable_l1: bool = True
    enable_l2: bool = True
    enable_l3: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "memory_cache"
    vector_dim: int = 768
    failure_graceful: bool = True     # 故障时是否优雅降级


class CacheLevel(ABC):
    """
    缓存层级抽象基类
    定义所有缓存层级的统一接口
    """
    
    def __init__(self, config: CacheConfig, level_type: CacheLevelType):
        self.config = config
        self.level_type = level_type
        self._stats = CacheStats()
        self._lock = threading.RLock()
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键（格式: namespace:memory_id:version）
            
        Returns:
            缓存值，如果不存在或过期返回 None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """
        清空缓存
        
        Returns:
            清空的条目数量
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    def stats(self) -> CacheStats:
        """获取统计信息"""
        with self._lock:
            return CacheStats(**self._stats.__dict__)
    
    def _record_hit(self, latency_ms: float = 0):
        """记录命中"""
        with self._lock:
            self._stats.hits += 1
            self._stats.total_requests += 1
            self._stats.total_latency_ms += latency_ms
    
    def _record_miss(self, latency_ms: float = 0):
        """记录未命中"""
        with self._lock:
            self._stats.misses += 1
            self._stats.total_requests += 1
            self._stats.total_latency_ms += latency_ms
    
    def _record_set(self):
        """记录设置操作"""
        with self._lock:
            self._stats.sets += 1
    
    def _record_delete(self):
        """记录删除操作"""
        with self._lock:
            self._stats.deletes += 1
    
    def _record_error(self):
        """记录错误"""
        with self._lock:
            self._stats.errors += 1
    
    def _record_eviction(self):
        """记录淘汰"""
        with self._lock:
            self._stats.evicted += 1
    
    @property
    @abstractmethod
    def name(self) -> str:
        """缓存层级名称"""
        pass
    
    def reset_stats(self):
        """重置统计"""
        with self._lock:
            self._stats = CacheStats()
    
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass