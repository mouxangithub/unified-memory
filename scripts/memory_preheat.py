#!/usr/bin/env python3
"""
Memory Preheat - 批量预热 v0.1.2

功能:
- Agent 启动时预加载热点记忆
- L1 缓存预热
- 智能加载策略
- 预热状态追踪

Usage:
    memory_preheat.py warmup [--top-k 20]
    memory_preheat.py status
    memory_preheat.py schedule  # 设置预热计划
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CACHE_DIR = MEMORY_DIR / "cache"
PREHEAT_STATE = MEMORY_DIR / "preheat" / "state.json"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False


class MemoryPreheat:
    """批量预热"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.state = self._load_state()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        memories = []
        
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                
                if result:
                    count = len(result.get("id", []))
                    for i in range(count):
                        mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        memories.append(mem)
            except:
                pass
        
        return memories
    
    def _load_state(self) -> Dict:
        """加载预热状态"""
        if PREHEAT_STATE.exists():
            try:
                return json.loads(PREHEAT_STATE.read_text())
            except:
                pass
        return {
            "last_preheat": None,
            "preheated_ids": [],
            "stats": {"total_preheats": 0, "avg_time_ms": 0}
        }
    
    def _save_state(self):
        """保存预热状态"""
        PREHEAT_STATE.parent.mkdir(parents=True, exist_ok=True)
        PREHEAT_STATE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
    
    def _calculate_hot_score(self, mem: Dict) -> float:
        """计算热度分数"""
        score = 0.0
        
        # 1. 重要性
        importance = mem.get("importance", 0.5)
        score += importance * 40
        
        # 2. 时间新鲜度
        created_at = mem.get("created_at") or mem.get("timestamp") or ""
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                hours_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
                freshness = max(0, 1 - hours_ago / (24 * 7))  # 7天内衰减
                score += freshness * 30
            except:
                pass
        
        # 3. 访问频率
        access_count = mem.get("access_count", 0)
        score += min(access_count * 2, 20)
        
        # 4. 分类权重
        category = mem.get("category", "")
        if category in ["preference", "decision", "entity"]:
            score += 10
        
        return score
    
    def warmup(self, top_k: int = 20) -> Dict:
        """预热热点记忆"""
        start_time = datetime.now()
        
        # 计算热度
        scored = []
        for mem in self.memories:
            score = self._calculate_hot_score(mem)
            scored.append((mem, score))
        
        # 排序
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # 选择热点
        hot = [m for m, s in scored[:top_k]]
        
        # 更新状态
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        self.state["last_preheat"] = datetime.now().isoformat()
        self.state["preheated_ids"] = [m.get("id") for m in hot]
        self.state["stats"]["total_preheats"] += 1
        
        # 更新平均时间
        prev_avg = self.state["stats"].get("avg_time_ms", 0)
        count = self.state["stats"]["total_preheats"]
        self.state["stats"]["avg_time_ms"] = (prev_avg * (count - 1) + elapsed_ms) / count
        
        self._save_state()
        
        # 写入缓存
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / "l1_hot.json"
        cache_file.write_text(json.dumps({
            "memories": hot,
            "preheated_at": datetime.now().isoformat(),
            "count": len(hot)
        }, ensure_ascii=False, indent=2))
        
        return {
            "preheated": len(hot),
            "elapsed_ms": round(elapsed_ms, 2),
            "top_score": scored[0][1] if scored else 0,
            "avg_score": sum(s for _, s in scored[:top_k]) / top_k if scored and top_k > 0 else 0,
            "cache_file": str(cache_file)
        }
    
    def get_status(self) -> Dict:
        """获取预热状态"""
        return {
            "last_preheat": self.state.get("last_preheat"),
            "preheated_count": len(self.state.get("preheated_ids", [])),
            "total_preheats": self.state.get("stats", {}).get("total_preheats", 0),
            "avg_time_ms": round(self.state.get("stats", {}).get("avg_time_ms", 0), 2),
            "cache_exists": (CACHE_DIR / "l1_hot.json").exists()
        }
    
    def get_preheated_memories(self) -> List[Dict]:
        """获取预热记忆"""
        cache_file = CACHE_DIR / "l1_hot.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                return data.get("memories", [])
            except:
                pass
        return []


def main():
    parser = argparse.ArgumentParser(description="Memory Preheat 0.1.2")
    parser.add_argument("command", choices=["warmup", "status", "get"])
    parser.add_argument("--top-k", "-k", type=int, default=20, help="预热数量")
    
    args = parser.parse_args()
    
    preheat = MemoryPreheat()
    
    if args.command == "warmup":
        print(f"🔥 预热热点记忆 (top {args.top_k})...")
        result = preheat.warmup(args.top_k)
        
        print(f"\n✅ 预热完成:")
        print(f"  预热记忆: {result['preheated']} 条")
        print(f"  耗时: {result['elapsed_ms']} ms")
        print(f"  最高分: {result['top_score']:.2f}")
        print(f"  平均分: {result['avg_score']:.2f}")
        print(f"  缓存: {result['cache_file']}")
    
    elif args.command == "status":
        status = preheat.get_status()
        print(f"📊 预热状态:")
        print(f"  最近预热: {status['last_preheat'] or '从未'}")
        print(f"  预热数量: {status['preheated_count']}")
        print(f"  总预热次数: {status['total_preheats']}")
        print(f"  平均耗时: {status['avg_time_ms']} ms")
        print(f"  缓存状态: {'✅ 存在' if status['cache_exists'] else '❌ 不存在'}")
    
    elif args.command == "get":
        memories = preheat.get_preheated_memories()
        print(f"📋 预热记忆 ({len(memories)} 条):")
        for i, mem in enumerate(memories[:10], 1):
            text = mem.get("text", "")[:50]
            score = mem.get("importance", 0)
            print(f"  {i}. [{score:.2f}] {text}...")
        
        if len(memories) > 10:
            print(f"  ... 还有 {len(memories) - 10} 条")


if __name__ == "__main__":
    main()
