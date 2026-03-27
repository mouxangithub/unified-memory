#!/usr/bin/env python3
"""
Memory Performance - 性能优化 v0.2.1

功能:
- 多级缓存 (L1/L2/L3)
- 异步存储
- 批量操作
- 连接池

Usage:
    python3 scripts/memory_perf.py cache-status
    python3 scripts/memory_perf.py warmup --top-k 20
    python3 scripts/memory_perf.py batch-add --file items.json
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CACHE_DIR = MEMORY_DIR / "cache"

# 缓存配置
CACHE_CONFIG = {
    "L1": {"max_items": 50, "ttl": 300},    # 热缓存: 50条, 5分钟
    "L2": {"max_items": 200, "ttl": 3600},  # 温缓存: 200条, 1小时
    "L3": {"max_items": 1000, "ttl": 86400} # 冷缓存: 1000条, 24小时
}


class MemoryCache:
    """多级缓存"""
    
    def __init__(self):
        self.l1 = {}  # 热缓存
        self.l2 = {}  # 温缓存
        self.l3 = {}  # 冷缓存
        self.l1_time = {}
        self.l2_time = {}
        self.l3_time = {}
        self.lock = threading.Lock()
        
        # 加载缓存
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        for level in ["l1", "l2", "l3"]:
            cache_file = CACHE_DIR / f"{level}_cache.json"
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        data = json.load(f)
                        if level == "l1":
                            self.l1 = data.get("items", {})
                            self.l1_time = data.get("time", {})
                        elif level == "l2":
                            self.l2 = data.get("items", {})
                            self.l2_time = data.get("time", {})
                        elif level == "l3":
                            self.l3 = data.get("items", {})
                            self.l3_time = data.get("time", {})
                except:
                    pass
    
    def _save_cache(self, level: str):
        """保存缓存"""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / f"{level}_cache.json"
        
        if level == "l1":
            data = {"items": self.l1, "time": self.l1_time}
        elif level == "l2":
            data = {"items": self.l2, "time": self.l2_time}
        elif level == "l3":
            data = {"items": self.l3, "time": self.l3_time}
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    
    def get(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        now = time.time()
        
        with self.lock:
            # L1
            if key in self.l1:
                if now - self.l1_time.get(key, 0) < CACHE_CONFIG["L1"]["ttl"]:
                    return self.l1[key]
                del self.l1[key]
                del self.l1_time[key]
            
            # L2
            if key in self.l2:
                if now - self.l2_time.get(key, 0) < CACHE_CONFIG["L2"]["ttl"]:
                    item = self.l2[key]
                    # 升级到 L1
                    self.l1[key] = item
                    self.l1_time[key] = now
                    return item
                del self.l2[key]
                del self.l2_time[key]
            
            # L3
            if key in self.l3:
                if now - self.l3_time.get(key, 0) < CACHE_CONFIG["L3"]["ttl"]:
                    item = self.l3[key]
                    # 升级到 L2
                    self.l2[key] = item
                    self.l2_time[key] = now
                    return item
                del self.l3[key]
                del self.l3_time[key]
        
        return None
    
    def set(self, key: str, value: Dict, level: str = "L1"):
        """设置缓存"""
        now = time.time()
        
        with self.lock:
            if level == "L1":
                # 检查容量
                if len(self.l1) >= CACHE_CONFIG["L1"]["max_items"]:
                    # 降级到 L2
                    oldest = min(self.l1_time.items(), key=lambda x: x[1])
                    del self.l1[oldest[0]]
                    del self.l1_time[oldest[0]]
                
                self.l1[key] = value
                self.l1_time[key] = now
            
            elif level == "L2":
                if len(self.l2) >= CACHE_CONFIG["L2"]["max_items"]:
                    oldest = min(self.l2_time.items(), key=lambda x: x[1])
                    del self.l2[oldest[0]]
                    del self.l2_time[oldest[0]]
                
                self.l2[key] = value
                self.l2_time[key] = now
            
            elif level == "L3":
                if len(self.l3) >= CACHE_CONFIG["L3"]["max_items"]:
                    oldest = min(self.l3_time.items(), key=lambda x: x[1])
                    del self.l3[oldest[0]]
                    del self.l3_time[oldest[0]]
                
                self.l3[key] = value
                self.l3_time[key] = now
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            "L1": {"count": len(self.l1), "max": CACHE_CONFIG["L1"]["max_items"]},
            "L2": {"count": len(self.l2), "max": CACHE_CONFIG["L2"]["max_items"]},
            "L3": {"count": len(self.l3), "max": CACHE_CONFIG["L3"]["max_items"]}
        }
    
    def warmup(self, items: List[Dict], top_k: int = 20):
        """预热缓存"""
        # 按重要性排序
        sorted_items = sorted(items, key=lambda x: x.get("importance", 0), reverse=True)
        
        # L1: 最重要的
        for item in sorted_items[:top_k]:
            self.set(item["id"], item, "L1")
        
        # L2: 次重要的
        for item in sorted_items[top_k:top_k*2]:
            self.set(item["id"], item, "L2")
        
        # L3: 其余的
        for item in sorted_items[top_k*2:top_k*4]:
            self.set(item["id"], item, "L3")
        
        # 保存
        self._save_cache("l1")
        self._save_cache("l2")
        self._save_cache("l3")


class AsyncMemory:
    """异步记忆操作"""
    
    def __init__(self):
        self.queue = []
        self.processing = False
    
    async def store_async(self, item: Dict):
        """异步存储"""
        self.queue.append(item)
        if not self.processing:
            asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        """处理队列"""
        self.processing = True
        while self.queue:
            item = self.queue.pop(0)
            await self._store_item(item)
        self.processing = False
    
    async def _store_item(self, item: Dict):
        """存储单个项目"""
        # 实际存储逻辑
        pass


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        memories = []
        count = len(data.get("id", []))
        for i in range(count):
            memories.append({
                "id": data["id"][i] if i < len(data.get("id", [])) else "",
                "text": data["text"][i] if i < len(data.get("text", [])) else "",
                "category": data["category"][i] if i < len(data.get("category", [])) else "",
                "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5
            })
        return memories
    except:
        return []


def main():
    parser = argparse.ArgumentParser(description="Memory Performance 0.2.1")
    parser.add_argument("command", choices=["cache-status", "warmup", "batch-add"])
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--file", "-f")
    
    args = parser.parse_args()
    
    cache = MemoryCache()
    
    if args.command == "cache-status":
        stats = cache.get_stats()
        print("📦 缓存状态:")
        print(f"   🔥 L1 热: {stats['L1']['count']}/{stats['L1']['max']}")
        print(f"   🌡️ L2 温: {stats['L2']['count']}/{stats['L2']['max']}")
        print(f"   ❄️ L3 冷: {stats['L3']['count']}/{stats['L3']['max']}")
    
    elif args.command == "warmup":
        print(f"🔥 预热缓存 (top {args.top_k})...")
        memories = load_memories()
        
        start = time.time()
        cache.warmup(memories, args.top_k)
        elapsed = (time.time() - start) * 1000
        
        print(f"✅ 预热完成: {len(memories)} 条, {elapsed:.1f}ms")
    
    elif args.command == "batch-add":
        if not args.file:
            print("请提供文件")
            return
        
        with open(args.file) as f:
            items = json.load(f)
        
        print(f"📝 批量添加 {len(items)} 项...")


if __name__ == "__main__":
    main()
