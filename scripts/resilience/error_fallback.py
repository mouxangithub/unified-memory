#!/usr/bin/env python3
"""
Error Fallback - 三层错误降级机制

降级策略:
1. 向量搜索 → BM25 关键词搜索
2. BM25 失败 → 缓存查询
3. 全部失败 → 返回默认结果

特点:
- 自动检测故障
- 无缝切换
- 故障恢复
- 健康监控
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))


class FallbackLevel(str, Enum):
    PRIMARY = "primary"      # 主要方法（向量搜索）
    SECONDARY = "secondary"  # 次要方法（BM25）
    TERTIARY = "tertiary"    # 第三方法（缓存）
    FAILED = "failed"        # 全部失败


@dataclass
class FallbackResult:
    """降级结果"""
    success: bool
    level: FallbackLevel
    data: Any
    error: Optional[str] = None
    latency_ms: float = 0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ErrorFallback:
    """错误降级机制"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or Path.home() / ".openclaw" / "workspace" / "memory" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 健康状态
        self.health = {
            "vector": {"healthy": True, "last_check": None, "fail_count": 0},
            "bm25": {"healthy": True, "last_check": None, "fail_count": 0},
            "cache": {"healthy": True, "last_check": None, "fail_count": 0}
        }
        
        # 配置
        self.max_fail_count = 3
        self.recovery_interval = 300  # 5分钟
    
    def execute_with_fallback(
        self,
        primary_func: Callable,
        secondary_func: Callable,
        tertiary_func: Callable,
        *args,
        **kwargs
    ) -> FallbackResult:
        """执行三层降级"""
        
        # Level 1: 向量搜索
        if self._is_healthy("vector"):
            try:
                start = time.time()
                result = primary_func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                
                self._mark_healthy("vector")
                
                return FallbackResult(
                    success=True,
                    level=FallbackLevel.PRIMARY,
                    data=result,
                    latency_ms=latency
                )
            except Exception as e:
                self._mark_unhealthy("vector", str(e))
        
        # Level 2: BM25 搜索
        if self._is_healthy("bm25"):
            try:
                start = time.time()
                result = secondary_func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                
                self._mark_healthy("bm25")
                
                return FallbackResult(
                    success=True,
                    level=FallbackLevel.SECONDARY,
                    data=result,
                    latency_ms=latency
                )
            except Exception as e:
                self._mark_unhealthy("bm25", str(e))
        
        # Level 3: 缓存查询
        if self._is_healthy("cache"):
            try:
                start = time.time()
                result = tertiary_func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                
                self._mark_healthy("cache")
                
                return FallbackResult(
                    success=True,
                    level=FallbackLevel.TERTIARY,
                    data=result,
                    latency_ms=latency
                )
            except Exception as e:
                self._mark_unhealthy("cache", str(e))
        
        # 全部失败
        return FallbackResult(
            success=False,
            level=FallbackLevel.FAILED,
            data=None,
            error="所有搜索方法都失败"
        )
    
    def search_with_fallback(self, query: str, limit: int = 10) -> FallbackResult:
        """搜索（自动降级）"""
        
        def vector_search(q, l):
            """向量搜索"""
            try:
                from unified_memory import UnifiedMemory
                um = UnifiedMemory()
                return um.search(q, limit=l, mode="vector")
            except:
                raise RuntimeError("向量搜索失败")
        
        def bm25_search(q, l):
            """BM25 搜索"""
            try:
                from unified_memory import UnifiedMemory
                um = UnifiedMemory()
                return um.search(q, limit=l, mode="bm25")
            except:
                raise RuntimeError("BM25 搜索失败")
        
        def cache_search(q, l):
            """缓存查询"""
            cache_key = self._get_cache_key(q)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                return data.get("results", [])[:l]
            
            raise RuntimeError("缓存未命中")
        
        result = self.execute_with_fallback(
            vector_search,
            bm25_search,
            cache_search,
            query,
            limit
        )
        
        # 成功时更新缓存
        if result.success and result.level in [FallbackLevel.PRIMARY, FallbackLevel.SECONDARY]:
            self._update_cache(query, result.data)
        
        return result
    
    def _is_healthy(self, component: str) -> bool:
        """检查组件健康"""
        health = self.health[component]
        
        # 检查是否需要尝试恢复
        if not health["healthy"]:
            last_check = health.get("last_check")
            if last_check:
                last_time = datetime.fromisoformat(last_check)
                if datetime.now() - last_time > timedelta(seconds=self.recovery_interval):
                    # 尝试恢复
                    return True
            return False
        
        return True
    
    def _mark_healthy(self, component: str):
        """标记健康"""
        self.health[component] = {
            "healthy": True,
            "last_check": datetime.now().isoformat(),
            "fail_count": 0
        }
    
    def _mark_unhealthy(self, component: str, error: str):
        """标记不健康"""
        health = self.health[component]
        health["fail_count"] += 1
        health["last_check"] = datetime.now().isoformat()
        
        if health["fail_count"] >= self.max_fail_count:
            health["healthy"] = False
            print(f"⚠️ {component} 标记为不健康: {error}")
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _update_cache(self, query: str, results: List):
        """更新缓存"""
        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_file.write_text(json.dumps({
            "query": query,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
    
    def get_health_report(self) -> Dict:
        """获取健康报告"""
        return {
            "health": self.health,
            "cache_count": len(list(self.cache_dir.glob("*.json"))),
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """清除缓存"""
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
        print("✅ 缓存已清除")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="错误降级机制")
    parser.add_argument("--test", action="store_true", help="测试降级")
    parser.add_argument("--health", action="store_true", help="健康报告")
    parser.add_argument("--clear-cache", action="store_true", help="清除缓存")
    
    args = parser.parse_args()
    
    fallback = ErrorFallback()
    
    if args.test:
        print("🔍 测试搜索降级...")
        result = fallback.search_with_fallback("测试查询")
        print(f"结果: {result.level} - {'成功' if result.success else '失败'}")
        print(f"延迟: {result.latency_ms:.2f}ms")
    
    elif args.health:
        report = fallback.get_health_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.clear_cache:
        fallback.clear_cache()
    
    else:
        # 默认健康报告
        report = fallback.get_health_report()
        print("健康状态:")
        for component, status in report["health"].items():
            emoji = "✅" if status["healthy"] else "❌"
            print(f"  {emoji} {component}: {'健康' if status['healthy'] else '不健康'}")
        print(f"缓存数量: {report['cache_count']}")


if __name__ == "__main__":
    main()
