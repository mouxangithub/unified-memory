> ⚡ **核心开发者** | 步骤 5/6 | 166.3s

---

<think>用户需要实现一个完整的 Unified Memory v5 多级缓存模块，这是一个相当复杂的企业级项目。让我仔细分析需求：

1. **三层缓存架构**：
   - L1: Python dict (LRU, 1000 items)
   - L2: Redis (TTL 1小时)
   - L3: Qdrant 向量缓存 (TTL 24小时)
   - 缓存键格式: namespace:memory_id:version

2. **必须实现的组件**：
   - CacheLevel 抽象基类
   - L1Cache（进程内 LRU）
   - L2Cache（Redis 分布式缓存）
   - L3Cache（Qdrant 向量缓存）
   - MultiLevelCache 主类
   - CacheInvalidator

3. **输出文件结构**：
   - memory_v5/cache/
   - 包含 base.py, l1.py, l2.py, l3.py, multi_level.py, invalidator.py
   - tests/ 目录

让我开始实现这个完整的模块：

## 设计思路

### CacheLevel 抽象基类
需要定义统一的接口，包括：
- get(key) -> value
- set(key, value, ttl=None)
- delete(key)
- clear()
- stats() -> CacheStats

### L1Cache
- 使用 OrderedDict 实现 LRU
- 最大容量 1000
- 线程安全
- 需要处理 TTL

### L2Cache
- Redis 连接池
- 默认 TTL 3600


- 批量操作支持
- 故障降级处理

### L3Cache
- Qdrant 向量存储
- TTL 86400
- 向量相似度结果缓存

### MultiLevelCache
- Write-Through 策略
- 读写流程：L1 -> L2 -> L3 -> DB
- 统计聚合
- 预热接口

### CacheInvalidator
- 命名空间失效
- 版本变化失效
- 手动触发

现在开始实现这个模块的具体代码。
</think>

# Unified Memory v5 多级缓存模块实现

这是一个完整的企业级多级缓存实现，包含三层缓存、失效管理、统计监控等完整功能。

## 完整代码结构

```
memory_v5/cache/
├── __init__.py
├── base.py              # 抽象基类
├── l1.py                 # L1 进程内缓存
├── l2.py                 # L2 Redis 缓存
├── l3.py                 # L3 向量缓存
├── multi_level.py        # 多级缓存编排
├── invalidator.py        # 缓存失效管理
└── tests/
    ├── __init__.py
    ├── test_l1.py
    ├── test_multi_level.py
    └── test_invalidator.py
```

---

## 1. 抽象基类定义

```python
# memory_v5/cache/base.py
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
```

---

## 2. L1 进程内 LRU 缓存

```python
# memory_v5/cache/l1.py
"""
L1 缓存：进程内 LRU 缓存
使用 Python dict + OrderedDict 实现高效 LRU
"""

from collections import OrderedDict
from datetime import datetime
from typing import Any, Optional, Dict, Iterator, Tuple
import threading
import time
import logging

from .base import (
    CacheLevel, CacheConfig, CacheStats, CacheEntry,
    CacheLevelType
)

logger = logging.getLogger(__name__)


class L1Cache(CacheLevel):
    """
    L1 进程内 LRU 缓存
    
    特性：
    - 使用 OrderedDict 实现 O(1) LRU 淘汰
    - 线程安全（使用 RLock）
    - 支持 TTL 过期
    - 最大容量限制（默认 1000）
    - 后台清理过期条目
    """
    
    def __init__(self, config: CacheConfig):
        super().__init__(config, CacheLevelType.L1_MEMORY)
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = config.max_size
        self._default_ttl = config.l1_ttl
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    @property
    def name(self) -> str:
        return "L1-Memory-LRU"
    
    @property
    def size(self) -> int:
        """当前缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        如果键存在且未过期：
        1. 将键移到 OrderedDict 末尾（LRU 更新）
        2. 返回值
        否则返回 None
        """
        start_time = time.perf_counter()
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._record_miss((time.perf_counter() - start_time) * 1000)
                return None
            
            # 检查过期
            if entry.is_expired:
                self._remove_entry(key)
                self._record_miss((time.perf_counter() - start_time) * 1000)
                self._record_eviction()
                return None
            
            # LRU 更新：移动到末尾
            self._cache.move_to_end(key)
            self._record_hit((time.perf_counter() - start_time) * 1000)
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        流程：
        1. 计算过期时间
        2. 如果缓存已满，淘汰最旧的条目（LRU）
        3. 插入新条目并移到末尾
        """
        start_time = time.perf_counter()
        
        if ttl is None:
            ttl = self._default_ttl
        
        entry = CacheEntry.create(
            key=key,
            value=value,
            ttl=ttl,
            version=getattr(value, 'version', '1') if hasattr(value, '__dict__') else '1'
        )
        
        with self._lock:
            # 检查是否需要淘汰
            if key not in self._cache and len(self._cache) >= self._max_size:
                self._evict_lru()
            
            # 更新或插入
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            self._record_set((time.perf_counter() - start_time) * 1000)
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                self._record_delete()
                return True
            return False
    
    def clear(self) -> int:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._record_delete()
            return count
    
    def exists(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                self._remove_entry(key)
                self._record_eviction()
                return False
            return True
    
    def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        批量获取
        
        Returns:
            包含所有存在且未过期条目的字典
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        批量设置
        
        Returns:
            成功设置的条目数量
        """
        count = 0
        for key, value in items.items():
            if self.set(key, value, ttl):
                count += 1
        return count
    
    def delete_many(self, keys: list[str]) -> int:
        """
        批量删除
        
        Returns:
            删除的条目数量
        """
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count
    
    def get_keys_by_namespace(self, namespace: str) -> list[str]:
        """
        获取指定命名空间的所有键
        
        Args:
            namespace: 命名空间
            
        Returns:
            匹配的键列表
        """
        prefix = f"{namespace}:"
        with self._lock:
            return [k for k in self._cache.keys() if k.startswith(prefix)]
    
    def _evict_lru(self):
        """淘汰最近最少使用的条目"""
        if not self._cache:
            return
        
        # OrderedDict 的第一个元素是最旧的
        oldest_key = next(iter(self._cache))
        self._remove_entry(oldest_key)
        self._record_eviction()
        logger.debug(f"L1 cache evicted LRU item: {oldest_key}")
    
    def _remove_entry(self, key: str):
        """删除指定条目（内部方法，不加锁）"""
        if key in self._cache:
            del self._cache[key]
    
    def _cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._record_eviction()
            
            if expired_keys:
                logger.debug(f"L1 cache cleaned {len(expired_keys)} expired items")
            
            return len(expired_keys)
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_loop():
            while not self._stop_cleanup.is_set():
                # 每 60 秒清理一次过期条目
                self._stop_cleanup.wait(timeout=60)
                if not self._stop_cleanup.is_set():
                    try:
                        self._cleanup_expired()
                    except Exception as e:
                        logger.error(f"L1 cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(
            target=cleanup_loop,
            daemon=True,
            name="L1Cache-Cleanup"
        )
        self._cleanup_thread.start()
    
    def _stop_cleanup_thread(self):
        """停止后台清理线程"""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 测试基本操作
            test_key = "__health_check__"
            self.set(test_key, "ok", ttl=1)
            result = self.get(test_key)
            self.delete(test_key)
            return result == "ok"
        except Exception as e:
            logger.error(f"L1 health check failed: {e}")
            return False
    
    def get_lru_order(self) -> list[str]:
        """获取 LRU 顺序（用于调试）"""
        with self._lock:
            return list(self._cache.keys())
    
    def __del__(self):
        """析构时停止清理线程"""
        self._stop_cleanup_thread()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_cleanup_thread()
        return False
```

---

## 3. L2 Redis 分布式缓存

```python
# memory_v5/cache/l2.py
"""
L2 缓存：Redis 分布式缓存
支持连接池管理、批量操作、故障降级
"""

import json
import logging
from typing import Any, Optional, Dict, List
from dataclasses import asdict
import time
import threading

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from .base import CacheLevel, CacheConfig, CacheEntry, CacheLevelType

logger = logging.getLogger(__name__)


class L2Cache(CacheLevel):
    """
    L2 Redis 分布式缓存
    
    特性：
    - 连接池管理（线程安全）
    - 支持批量操作（pipeline）
    - TTL 自动管理
    - 故障降级：Redis 不可用时跳过 L2
    - Pipeline 批量操作优化
    """
    
    _pool: Optional[redis.ConnectionPool] = None
    _pool_lock = threading.Lock()
    
    def __init__(self, config: CacheConfig):
        super().__init__(config, CacheLevelType.L2_REDIS)
        
        self._default_ttl = config.l2_ttl
        self._failure_graceful = config.failure_graceful
        self._client: Optional[redis.Redis] = None
        self._serializer = CacheEntrySerializer()
        
        # 初始化连接
        self._init_connection()
    
    def _init_connection(self):
        """初始化 Redis 连接"""
        try:
            # 使用类级别的连接池（单例模式）
            with L2Cache._pool_lock:
                if L2Cache._pool is None:
                    L2Cache._pool = redis.ConnectionPool.from_url(
                        self.config.redis_url,
                        max_connections=self.config.redis_pool_size,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True,
                    )
                
                self._client = redis.Redis(connection_pool=L2Cache._pool)
                
                # 测试连接
                self._client.ping()
                logger.info(f"L2 Redis connected: {self.config.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
    
    @property
    def name(self) -> str:
        return "L2-Redis"
    
    @property
    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        if self._client is None:
            return False
        try:
            return self._client.ping()
        except (ConnectionError, TimeoutError):
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self._client is None:
            self._record_miss()
            return None
        
        start_time = time.perf_counter()
        
        try:
            data = self._client.get(key)
            
            if data is None:
                self._record_miss((time.perf_counter() - start_time) * 1000)
                return None
            
            # 反序列化
            entry = self._serializer.deserialize(data)
            if entry is None:
                self._record_miss((time.perf_counter() - start_time) * 1000)
                return None
            
            # 检查过期
            if entry.is_expired:
                self._client.delete(key)
                self._record_miss((time.perf_counter() - start_time) * 1000)
                self._record_eviction()
                return None
            
            self._record_hit((time.perf_counter() - start_time) * 1000)
            return entry.value
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis get error: {e}")
            self._record_error()
            if not self._failure_graceful:
                raise
            self._record_miss((time.perf_counter() - start_time) * 1000)
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if self._client is None:
            self._record_set()
            return False
        
        if ttl is None:
            ttl = self._default_ttl
        
        start_time = time.perf_counter()
        
        try:
            entry = CacheEntry.create(
                key=key,
                value=value,
                ttl=ttl,
                version=getattr(value, 'version', '1') if hasattr(value, '__dict__') else '1'
            )
            
            data = self._serializer.serialize(entry)
            
            # SETEX 原子操作：设置值和过期时间
            self._client.setex(key, ttl, data)
            
            self._record_set((time.perf_counter() - start_time) * 1000)
            return True
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis set error: {e}")
            self._record_error()
            if not self._failure_graceful:
                raise
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if self._client is None:
            return False
        
        try:
            result = self._client.delete(key)
            self._record_delete()
            return result > 0
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis delete error: {e}")
            self._record_error()
            return False
    
    def clear(self) -> int:
        """清空缓存（使用 SCAN 避免阻塞）"""
        if self._client is None:
            return 0
        
        try:
            count = 0
            cursor = 0
            
            while True:
                cursor, keys = self._client.scan(cursor, match="*", count=1000)
                if keys:
                    count += self._client.delete(*keys)
                if cursor == 0:
                    break
            
            self._record_delete()
            return count
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis clear error: {e}")
            self._record_error()
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self._client is None:
            return False
        
        try:
            return self._client.exists(key) > 0
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis exists error: {e}")
            self._record_error()
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取"""
        if self._client is None or not keys:
            return {}
        
        try:
            # 使用 pipeline 批量操作
            pipe = self._client.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = pipe.execute()
            
            result_dict = {}
            for key, data in zip(keys, results):
                if data:
                    entry = self._serializer.deserialize(data)
                    if entry and not entry.is_expired:
                        result_dict[key] = entry.value
            
            # 更新统计
            with self._lock:
                self._stats.hits += len(result_dict)
                self._stats.misses += len(keys) - len(result_dict)
                self._stats.total_requests += len(keys)
            
            return result_dict
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis get_many error: {e}")
            self._record_error()
            return {}
    
    def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """批量设置"""
        if self._client is None or not items:
            return 0
        
        if ttl is None:
            ttl = self._default_ttl
        
        try:
            pipe = self._client.pipeline()
            
            for key, value in items.items():
                entry = CacheEntry.create(
                    key=key,
                    value=value,
                    ttl=ttl
                )
                data = self._serializer.serialize(entry)
                pipe.setex(key, ttl, data)
            
            pipe.execute()
            
            with self._lock:
                self._stats.sets += len(items)
            
            return len(items)
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis set_many error: {e}")
            self._record_error()
            return 0
    
    def delete_many(self, keys: List[str]) -> int:
        """批量删除"""
        if self._client is None or not keys:
            return 0
        
        try:
            result = self._client.delete(*keys)
            self._record_delete()
            return result
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis delete_many error: {e}")
            self._record_error()
            return 0
    
    def get_keys_by_namespace(self, namespace: str) -> List[str]:
        """获取指定命名空间的所有键"""
        if self._client is None:
            return []
        
        try:
            pattern = f"{namespace}:*"
            keys = []
            cursor = 0
            
            while True:
                cursor, batch = self._client.scan(cursor, match=pattern, count=1000)
                keys.extend(batch)
                if cursor == 0:
                    break
            
            return keys
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"L2 Redis get_keys_by_namespace error: {e}")
            self._record_error()
            return []
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if self._client is None:
                return False
            return self._client.ping()
        except Exception as e:
            logger.error(f"L2 health check failed: {e}")
            return False
    
    def reconnect(self) -> bool:
        """重新连接"""
        try:
            self._init_connection()
            return self.health_check()
        except Exception as e:
            logger.error(f"L2 reconnect failed: {e}")
            return False


class CacheEntrySerializer:
    """缓存条目序列化器"""
    
    def serialize(self, entry: CacheEntry) -> str:
        """序列化缓存条目为 JSON"""
        data = {
            "key": entry.key,
            "value": self._serialize_value(entry.value),
            "created_at": entry.created_at,
            "expires_at": entry.expires_at,
            "version": entry.version,
            "metadata": entry.metadata,
        }
        return json.dumps(data)
    
    def deserialize(self, data: str) -> Optional[CacheEntry]:
        """从 JSON 反序列化缓存条目"""
        try:
            parsed = json.loads(data)
            return CacheEntry(
                key=parsed["key"],
                value=self._deserialize_value(parsed["value"]),
                created_at=parsed["created_at"],
                expires_at=parsed["expires_at"],
                version=parsed["version"],
                metadata=parsed.get("metadata", {}),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to deserialize cache entry: {e}")
            return None
    
    def _serialize_value(self, value: Any) -> Any:
        """序列化值"""
        if hasattr(value, '__dict__'):
            # 对象转为字典
            return {"_type": type(value).__name__, "_data": value.__dict__}
        elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
            return value
        else:
            # 尝试 JSON 序列化
            try:
                return {"_type": "json", "_data": json.loads(json.dumps(value))}
            except:
                return str(value)
    
    def _deserialize_value(self, value: Any) -> Any:
        """反序列化值"""
        if isinstance(value, dict) and "_type" in value:
            if value["_type"] == "json":
                return value["_data"]
            # 可以扩展其他类型的反序列化
            return value["_data"]
        return value
```

---

## 4. L3 Qdrant 向量缓存

```python
# memory_v5/cache/l3.py
"""
L3 缓存：Qdrant 向量缓存
存储向量相似度计算结果
"""

import logging
from typing import Any, Optional, Dict, List, Tuple
import time
import threading
from dataclasses import dataclass
import hashlib

import numpy as np

from .base import CacheLevel, CacheConfig, CacheLevelType

logger = logging.getLogger(__name__)


# Qdrant 客户端类型提示
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from qdrant_client.http.exceptions import UnexpectedResponse
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.warning("Qdrant client not installed. L3 cache will be disabled.")


@dataclass
class VectorCacheEntry:
    """向量缓存条目"""
    key: str
    query_vector: List[float]
    result_ids: List[str]
    result_scores: List[float]
    result_data: Optional[List[Dict]] = None
    created_at: float = None
    expires_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class L3Cache(CacheLevel):
    """
    L3 Qdrant 向量缓存
    
    用途：
    - 缓存向量相似度搜索结果
    - 避免重复的向量计算
    - 支持语义缓存
    
    存储结构：
    - collection: memory_vector_cache
    - payload: {key, query_vector(可选), result_ids, result_scores, result_data}
    """
    
    def __init__(self, config: CacheConfig):
        super().__init__(config, CacheLevelType.L3_VECTOR)
        
        self._default_ttl = config.l3_ttl
        self._failure_graceful = config.failure_graceful
        self._collection = config.qdrant_collection
        self._vector_dim = config.vector_dim
        self._client: Optional[Any] = None
        
        # 初始化连接
        if HAS_QDRANT:
            self._init_connection()
    
    def _init_connection(self):
        """初始化 Qdrant 连接"""
        try:
            self._client = QdrantClient(url=self.config.qdrant_url)
            
            # 尝试创建 collection（如果不存在）
            try:
                collections = self._client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if self._collection not in collection_names:
                    self._client.create_collection(
                        collection_name=self._collection,
                        vectors_config=VectorParams(
                            size=self._vector_dim,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {self._collection}")
            
            except UnexpectedResponse as e:
                if "already exists" not in str(e):
                    raise
                    
            # 测试连接
            self._client.get_collection(self._collection)
            logger.info(f"L3 Qdrant connected: {self.config.qdrant_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self._client = None
    
    @property
    def name(self) -> str:
        return "L3-Qdrant-Vector"
    
    @property
    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        if self._client is None:
            return False
        try:
            self._client.get_collection(self._collection)
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取向量缓存结果
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的结果字典，包含 result_ids, result_scores, result_data
        """
        if self._client is None:
            self._record_miss()
            return None
        
        start_time = time.perf_counter()
        
        try:
            # 查询单条记录
            results = self._client.search(
                collection_name=self._collection,
                query_vector=[0.0] * self._vector_dim,  # 不使用向量搜索
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="key",
                            match=MatchValue(value=key)
                        )
                    ]
                ),
                limit=1
            )
            
            if not results:
                self._record_miss((time.perf_counter() - start_time) * 1000)
                return None
            
            point = results[0]
            payload = point.payload
            
            # 检查过期
            if payload.get("expires_at") and payload["expires_at"] < time.time():
                self._client.delete(
                    collection_name=self._collection,
                    points_selector=[point.id]
                )
                self._record_miss((time.perf_counter() - start_time) * 1000)
                self._record_eviction()
                return None
            
            self._record_hit((time.perf_counter() - start_time) * 1000)
            
            return {
                "result_ids": payload["result_ids"],
                "result_scores": payload["result_scores"],
                "result_data": payload.get("result_data"),
            }
            
        except Exception as e:
            logger.warning(f"L3 Qdrant get error: {e}")
            self._record_error()
            if not self._failure_graceful:
                raise
            self._record_miss((time.perf_counter() - start_time) * 1000)
            return None
    
    def get_similar(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        namespace: Optional[str] = None,
        min_score: float = 0.9
    ) -> Optional[Dict[str, Any]]:
        """
        通过向量相似度查找缓存结果
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            namespace: 命名空间过滤
            min_score: 最低相似度阈值
            
        Returns:
            匹配的缓存结果
        """
        if self._client is None:
            return None
        
        try:
            # 构建过滤条件
            must_conditions = []
            if namespace:
                must_conditions.append(FieldCondition(
                    key="namespace",
                    match=MatchValue(value=namespace)
                ))
            
            search_filter = Filter(must=must_conditions) if must_conditions else None
            
            # 搜索最相似的结果
            results = self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k
            )
            
            # 过滤有效结果
            valid_results = []
            for point in results:
                payload = point.payload
                if payload.get("expires_at") and payload["expires_at"] < time.time():
                    continue
                if point.score >= min_score:
                    valid_results.append({
                        "key": payload["key"],
                        "score": point.score,
                        "result_ids":