#!/usr/bin/env python3
"""
监控与可观测性 - Memory Analytics

核心：记忆系统指标、召回精度、运维监控
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ANALYTICS_DIR = MEMORY_DIR / "analytics"


class MemoryAnalytics:
    """记忆系统分析引擎"""
    
    def __init__(self):
        ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
        self.metrics_file = ANALYTICS_DIR / "metrics.json"
        self.events_file = ANALYTICS_DIR / "events.jsonl"
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "total_memories": 0,
            "total_queries": 0,
            "total_recalls": 0,
            "total_storage": 0,
            "query_latencies": [],
            "recall_scores": [],
            "last_updated": None
        }
    
    def _save_metrics(self):
        self.metrics["last_updated"] = datetime.now().isoformat()
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def _append_event(self, event: Dict):
        """追加事件到日志"""
        with open(self.events_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                **event
            }, ensure_ascii=False) + "\n")
    
    # ===== 记录操作 =====
    
    def record_storage(self, memory_size: int):
        """记录存储操作"""
        self.metrics["total_memories"] += 1
        self.metrics["total_storage"] += memory_size
        self._append_event({"type": "storage", "size": memory_size})
        self._save_metrics()
    
    def record_query(self, latency_ms: float):
        """记录查询延迟"""
        self.metrics["total_queries"] += 1
        self.metrics["query_latencies"].append(latency_ms)
        # 只保留最近 1000 条
        if len(self.metrics["query_latencies"]) > 1000:
            self.metrics["query_latencies"] = self.metrics["query_latencies"][-1000:]
        self._append_event({"type": "query", "latency_ms": latency_ms})
        self._save_metrics()
    
    def record_recall(self, relevance_score: float):
        """记录召回质量"""
        self.metrics["total_recalls"] += 1
        self.metrics["recall_scores"].append(relevance_score)
        if len(self.metrics["recall_scores"]) > 1000:
            self.metrics["recall_scores"] = self.metrics["recall_scores"][-1000:]
        self._append_event({"type": "recall", "score": relevance_score})
        self._save_metrics()
    
    def record_feedback(self, memory_id: str, feedback_type: str):
        """记录用户反馈"""
        self._append_event({
            "type": "feedback",
            "memory_id": memory_id,
            "feedback": feedback_type
        })
    
    # ===== 聚合统计 =====
    
    def get_percentile(self, values: List[float], p: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * p / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]
    
    def get_latency_stats(self) -> Dict:
        """延迟统计"""
        latencies = self.metrics.get("query_latencies", [])
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "max": 0}
        
        return {
            "p50": self.get_percentile(latencies, 50),
            "p95": self.get_percentile(latencies, 95),
            "p99": self.get_percentile(latencies, 99),
            "avg": sum(latencies) / len(latencies),
            "max": max(latencies)
        }
    
    def get_recall_stats(self) -> Dict:
        """召回质量统计"""
        scores = self.metrics.get("recall_scores", [])
        if not scores:
            return {"precision": 0, "avg_relevance": 0, "total_recalls": 0}
        
        return {
            "avg_precision": sum(scores) / len(scores),
            "p50_relevance": self.get_percentile(scores, 50),
            "p95_relevance": self.get_percentile(scores, 95),
            "total_recalls": len(scores)
        }
    
    def get_storage_stats(self) -> Dict:
        """存储统计"""
        return {
            "total_memories": self.metrics.get("total_memories", 0),
            "total_bytes": self.metrics.get("total_storage", 0),
            "avg_bytes_per_memory": (
                self.metrics.get("total_storage", 0) / 
                max(1, self.metrics.get("total_memories", 0))
            )
        }
    
    # ===== 健康检查 =====
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        返回系统健康状态
        """
        issues = []
        score = 100
        
        # 检查延迟
        latency_stats = self.get_latency_stats()
        if latency_stats["p99"] > 500:
            issues.append(f"延迟过高: p99={latency_stats['p99']:.0f}ms")
            score -= 20
        
        # 检查召回质量
        recall_stats = self.get_recall_stats()
        if recall_stats["avg_precision"] < 0.5:
            issues.append(f"召回质量低: {recall_stats['avg_precision']:.2f}")
            score -= 30
        
        # 检查存储
        storage_stats = self.get_storage_stats()
        if storage_stats["total_memories"] == 0:
            issues.append("无记忆数据")
            score -= 10
        
        return {
            "status": "healthy" if score >= 80 else "degraded" if score >= 60 else "critical",
            "score": max(0, score),
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
    
    # ===== 完整报告 =====
    
    def get_full_report(self) -> Dict:
        """获取完整分析报告"""
        return {
            "health": self.health_check(),
            "latency": self.get_latency_stats(),
            "recall": self.get_recall_stats(),
            "storage": self.get_storage_stats(),
            "summary": {
                "total_queries": self.metrics.get("total_queries", 0),
                "total_recalls": self.metrics.get("total_recalls", 0),
                "uptime_hours": self._calculate_uptime()
            }
        }
    
    def _calculate_uptime(self) -> float:
        """计算运行时长（小时）"""
        if not self.metrics.get("last_updated"):
            return 0
        last = datetime.fromisoformat(self.metrics["last_updated"])
        delta = datetime.now() - last
        return delta.total_seconds() / 3600
    
    # ===== 导出 =====
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        if format == "json":
            return json.dumps(self.get_full_report(), indent=2)
        elif format == "prometheus":
            # Prometheus 格式
            lines = []
            lines.append(f'# HELP memory_total_memories Total number of memories')
            lines.append(f'# TYPE memory_total_memories gauge')
            lines.append(f'memory_total_memories {self.metrics.get("total_memories", 0)}')
            
            lines.append(f'# HELP memory_total_queries Total number of queries')
            lines.append(f'# TYPE memory_total_queries counter')
            lines.append(f'memory_total_queries {self.metrics.get("total_queries", 0)}')
            
            lines.append(f'# HELP memory_query_latency Query latency in ms')
            lines.append(f'# TYPE memory_query_latency summary')
            lat = self.get_latency_stats()
            lines.append(f'memory_query_latency{{quantile="0.5"}} {lat["p50"]}')
            lines.append(f'memory_query_latency{{quantile="0.95"}} {lat["p95"]}')
            lines.append(f'memory_query_latency{{quantile="0.99"}} {lat["p99"]}')
            
            return "\n".join(lines)
        
        return str(self.metrics)
    
    def reset(self):
        """重置指标"""
        self.metrics = {
            "total_memories": 0,
            "total_queries": 0,
            "total_recalls": 0,
            "total_storage": 0,
            "query_latencies": [],
            "recall_scores": [],
            "last_updated": None
        }
        self._save_metrics()


# 全局实例
_analytics = None

def get_analytics() -> MemoryAnalytics:
    global _analytics
    if _analytics is None:
        _analytics = MemoryAnalytics()
    return _analytics


if __name__ == "__main__":
    print("=" * 50)
    print("监控分析测试")
    print("=" * 50)
    
    analytics = MemoryAnalytics()
    
    # 模拟数据
    for i in range(10):
        analytics.record_storage(1000 + i * 100)
        analytics.record_query(30 + i * 5)
        analytics.record_recall(0.7 + i * 0.02)
    
    # 报告
    report = analytics.get_full_report()
    
    print("\n📊 健康检查:")
    health = report["health"]
    print(f"  状态: {health['status']}")
    print(f"  分数: {health['score']}/100")
    if health["issues"]:
        print(f"  问题: {health['issues']}")
    
    print("\n📊 延迟统计:")
    latency = report["latency"]
    print(f"  p50: {latency['p50']:.0f}ms")
    print(f"  p95: {latency['p95']:.0f}ms")
    print(f"  p99: {latency['p99']:.0f}ms")
    
    print("\n📊 召回质量:")
    recall = report["recall"]
    print(f"  平均精度: {recall['avg_precision']:.2f}")
    print(f"  总召回: {recall['total_recalls']}")
    
    print("\n📊 存储统计:")
    storage = report["storage"]
    print(f"  总记忆: {storage['total_memories']}")
    print(f"  总存储: {storage['total_bytes']} bytes")
    
    print("\n✅ 监控分析测试完成")
