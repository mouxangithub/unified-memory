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