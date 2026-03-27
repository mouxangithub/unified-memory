#!/usr/bin/env python3
"""
性能基准测试 - Benchmark

测试指标：
- 存储延迟
- 搜索延迟
- 召回精度
- 内存占用
"""

import json
import time
import psutil
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class Benchmark:
    """基准测试"""
    
    def __init__(self):
        self.results = []
        self.process = psutil.Process()
    
    def generate_text(self, length: int = 100) -> str:
        """生成随机文本"""
        words = ["用户", "喜欢", "简洁", "界面", "微服务", "架构", "Python", "开发", "测试"]
        return "".join(random.choice(words) for _ in range(length))
    
    def generate_vector(self, dim: int = 768) -> List[float]:
        """生成随机向量"""
        return [random.random() for _ in range(dim)]
    
    def generate_memories(self, count: int = 100) -> List[Dict]:
        """生成测试记忆"""
        memories = []
        for i in range(count):
            memories.append({
                "id": f"bench_{i}",
                "text": self.generate_text(50),
                "vector": self.generate_vector(),
                "category": random.choice(["fact", "decision", "preference"]),
                "confidence": random.uniform(0.5, 1.0)
            })
        return memories
    
    # ===== 存储基准 =====
    
    def benchmark_store(self, count: int = 100) -> Dict:
        """存储性能测试"""
        from memory_sqlite import SQLiteMemory
        
        db = SQLiteMemory(":memory:")
        memories = self.generate_memories(count)
        
        start_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        for mem in memories:
            db.store(mem)
        
        end_time = time.time()
        end_mem = self.process.memory_info().rss / 1024 / 1024
        
        db.close()
        
        return {
            "operation": "store",
            "count": count,
            "duration_ms": (end_time - start_time) * 1000,
            "avg_latency_ms": (end_time - start_time) * 1000 / count,
            "memory_mb": end_mem - start_mem
        }
    
    # ===== 搜索基准 =====
    
    def benchmark_search(self, count: int = 100, iterations: int = 10) -> Dict:
        """搜索性能测试"""
        from memory_sqlite import SQLiteMemory
        from memory_bm25 import BM25Index
        
        # 准备数据
        db = SQLiteMemory(":memory:")
        memories = self.generate_memories(count)
        for mem in memories:
            db.store(mem)
        
        texts = [m["text"] for m in memories]
        
        # BM25 索引
        bm25 = BM25Index()
        bm25.build(texts)
        
        # 测试查询
        queries = [self.generate_text(5) for _ in range(iterations)]
        
        start_time = time.time()
        for q in queries:
            bm25.search(q, top_k=10)
        end_time = time.time()
        
        db.close()
        
        return {
            "operation": "search_bm25",
            "iterations": iterations,
            "total_duration_ms": (end_time - start_time) * 1000,
            "avg_latency_ms": (end_time - start_time) * 1000 / iterations,
            "queries_per_second": iterations / (end_time - start_time)
        }
    
    # ===== 向量基准 =====
    
    def benchmark_vector(self, count: int = 100) -> Dict:
        """向量操作测试"""
        from memory_bm25 import hybrid_search
        
        texts = [self.generate_text(50) for _ in range(count)]
        vectors = [self.generate_vector() for _ in range(count)]
        query = self.generate_vector()
        
        start_time = time.time()
        results = hybrid_search("test", texts, vectors, top_k=10, alpha=0.5)
        end_time = time.time()
        
        return {
            "operation": "vector_search",
            "count": count,
            "duration_ms": (end_time - start_time) * 1000,
            "avg_latency_ms": (end_time - start_time) * 1000
        }
    
    # ===== 完整基准 =====
    
    def run_full_benchmark(self) -> Dict:
        """运行完整基准测试"""
        print("=" * 60)
        print("记忆系统性能基准测试")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_pid": self.process.pid
            },
            "benchmarks": {}
        }
        
        # 存储基准
        print("\n📦 存储基准...")
        for count in [100, 500, 1000]:
            r = self.benchmark_store(count)
            results["benchmarks"][f"store_{count}"] = r
            print(f"  {count} 条: {r['avg_latency_ms']:.2f}ms/条")
        
        # 搜索基准
        print("\n🔍 搜索基准...")
        for count in [100, 500, 1000]:
            r = self.benchmark_search(count, iterations=10)
            results["benchmarks"][f"search_{count}"] = r
            print(f"  {count} 条: {r['avg_latency_ms']:.2f}ms/查询")
        
        # 向量基准
        print("\n📐 向量基准...")
        for count in [100, 500, 1000]:
            r = self.benchmark_vector(count)
            results["benchmarks"][f"vector_{count}"] = r
            print(f"  {count} 条: {r['duration_ms']:.2f}ms")
        
        # 保存结果
        output_file = Path.home() / ".openclaw" / "workspace" / "memory" / "benchmark_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 结果已保存: {output_file}")
        
        return results


def run_benchmark():
    """运行基准测试"""
    benchmark = Benchmark()
    return benchmark.run_full_benchmark()


if __name__ == "__main__":
    results = run_benchmark()
    
    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)
    
    print("\n📊 总结:")
    print(f"  系统: {results['system']['cpu_count']} CPU, {results['system']['memory_total_gb']:.1f}GB 内存")
    
    # 提取关键指标
    store_1k = results["benchmarks"].get("store_1000", {})
    search_1k = results["benchmarks"].get("search_1000", {})
    
    if store_1k:
        print(f"  存储 (1k): {store_1k.get('avg_latency_ms', 0):.2f}ms/条")
    if search_1k:
        print(f"  搜索 (1k): {search_1k.get('avg_latency_ms', 0):.2f}ms/查询")
        print(f"  吞吐量: {search_1k.get('queries_per_second', 0):.1f} 查询/秒")
