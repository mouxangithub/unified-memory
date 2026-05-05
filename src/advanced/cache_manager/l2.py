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