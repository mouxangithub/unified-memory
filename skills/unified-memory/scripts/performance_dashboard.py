#!/usr/bin/env python3
"""
Performance Dashboard - 性能可视化仪表板 v1.0

功能:
- 实时性能监控
- 可视化图表
- 健康告警
- 历史趋势分析
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# 添加脚本目录
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from memory import MemorySystemV7
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DASHBOARD_DIR = MEMORY_DIR / "dashboard"

# 文件路径
METRICS_FILE = DASHBOARD_DIR / "metrics.json"
ALERTS_FILE = DASHBOARD_DIR / "alerts.json"
HISTORY_FILE = DASHBOARD_DIR / "history.json"

# 告警阈值
ALERT_THRESHOLDS = {
    "memory_count_high": 1000,      # 记忆数量过高
    "search_latency_high": 1.0,      # 搜索延迟过高（秒）
    "conflict_rate_high": 0.1,       # 矛盾率过高
    "storage_mb_high": 100,          # 存储空间过高（MB）
}

# 确保目录存在
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)


class PerformanceDashboard:
    """性能仪表板"""
    
    def __init__(self):
        self.memory = MemorySystemV7() if HAS_MEMORY else None
        self.metrics: Dict[str, Any] = {}
        self.alerts: List[Dict] = []
        self.history: List[Dict] = []
        self._load()
    
    def _load(self):
        """加载数据"""
        try:
            if METRICS_FILE.exists():
                self.metrics = json.loads(METRICS_FILE.read_text())
            if ALERTS_FILE.exists():
                self.alerts = json.loads(ALERTS_FILE.read_text())
            if HISTORY_FILE.exists():
                self.history = json.loads(HISTORY_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载仪表板数据失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存数据"""
        try:
            METRICS_FILE.write_text(json.dumps(self.metrics, ensure_ascii=False, indent=2))
            ALERTS_FILE.write_text(json.dumps(self.alerts, ensure_ascii=False, indent=2))
            HISTORY_FILE.write_text(json.dumps(self.history, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存仪表板数据失败: {e}", file=sys.stderr)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": {},
            "performance": {},
            "health": {},
            "alerts": []
        }
        
        if self.memory:
            # 记忆统计
            all_memories = self.memory.memories if self.memory else []
            metrics["memory_stats"] = {
                "total_count": len(all_memories),
                "by_importance": {
                    "high": len([m for m in all_memories if m.get("importance", 0) > 0.7]),
                    "medium": len([m for m in all_memories if 0.3 <= m.get("importance", 0) <= 0.7]),
                    "low": len([m for m in all_memories if m.get("importance", 0) < 0.3])
                },
                "by_age": {
                    "last_24h": len([m for m in all_memories if self._is_recent(m, hours=24)]),
                    "last_7d": len([m for m in all_memories if self._is_recent(m, days=7)]),
                    "older": len([m for m in all_memories if not self._is_recent(m, days=7)])
                }
            }
            
            # 性能指标
            start_time = time.time()
            test_query = "测试查询"
            try:
                _ = self.memory.get_context(test_query, top_k=5)
            except:
                pass
            search_latency = time.time() - start_time
            
            metrics["performance"] = {
                "search_latency_ms": search_latency * 1000,
                "avg_memory_size_bytes": sum(len(json.dumps(m)) for m in all_memories) / max(len(all_memories), 1),
                "total_storage_mb": self._calculate_storage_size()
            }
            
            # 健康指标
            conflict_count = len([m for m in all_memories if m.get("confidence") == "❌ 矛盾"])
            conflict_rate = conflict_count / max(len(all_memories), 1)
            
            metrics["health"] = {
                "conflict_count": conflict_count,
                "conflict_rate": conflict_rate,
                "stale_count": len([m for m in all_memories if m.get("confidence") == "⚠️ 可能过时"]),
                "health_score": self._calculate_health_score(all_memories)
            }
            
            # 检查告警
            metrics["alerts"] = self._check_alerts(metrics)
        
        self.metrics = metrics
        
        # 添加到历史记录
        self.history.append({
            "timestamp": metrics["timestamp"],
            "memory_count": metrics["memory_stats"].get("total_count", 0),
            "search_latency_ms": metrics["performance"].get("search_latency_ms", 0),
            "health_score": metrics["health"].get("health_score", 0)
        })
        
        # 只保留最近100条历史记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self._save()
        
        return metrics
    
    def _is_recent(self, memory: Dict, hours: int = None, days: int = None) -> bool:
        """检查记忆是否是最近的"""
        timestamp = memory.get("timestamp") or memory.get("created_at")
        if not timestamp:
            return False
        
        try:
            if "T" in timestamp:
                mem_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
            else:
                mem_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            
            threshold = timedelta(hours=hours) if hours else timedelta(days=days)
            return (datetime.now() - mem_time) < threshold
        except:
            return False
    
    def _calculate_storage_size(self) -> float:
        """计算存储大小（MB）"""
        total_size = 0
        
        for file_path in MEMORY_DIR.rglob("*.json"):
            try:
                total_size += file_path.stat().st_size
            except:
                pass
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def _calculate_health_score(self, memories: List[Dict]) -> float:
        """计算健康评分（0-100）"""
        if not memories:
            return 100.0
        
        # 基础分数
        score = 100.0
        
        # 矛盾扣分
        conflict_count = len([m for m in memories if m.get("confidence") == "❌ 矛盾"])
        score -= conflict_count * 5
        
        # 过时扣分
        stale_count = len([m for m in memories if m.get("confidence") == "⚠️ 可能过时"])
        score -= stale_count * 2
        
        # 存储大小扣分
        storage_mb = self._calculate_storage_size()
        if storage_mb > 100:
            score -= (storage_mb - 100) * 0.5
        
        return max(min(score, 100), 0)
    
    def _check_alerts(self, metrics: Dict) -> List[Dict]:
        """检查告警"""
        alerts = []
        
        # 记忆数量告警
        total_count = metrics["memory_stats"].get("total_count", 0)
        if total_count > ALERT_THRESHOLDS["memory_count_high"]:
            alerts.append({
                "level": "warning",
                "type": "memory_count_high",
                "message": f"记忆数量过高: {total_count} (阈值: {ALERT_THRESHOLDS['memory_count_high']})",
                "timestamp": datetime.now().isoformat()
            })
        
        # 搜索延迟告警
        search_latency = metrics["performance"].get("search_latency_ms", 0) / 1000
        if search_latency > ALERT_THRESHOLDS["search_latency_high"]:
            alerts.append({
                "level": "warning",
                "type": "search_latency_high",
                "message": f"搜索延迟过高: {search_latency:.2f}s (阈值: {ALERT_THRESHOLDS['search_latency_high']}s)",
                "timestamp": datetime.now().isoformat()
            })
        
        # 矛盾率告警
        conflict_rate = metrics["health"].get("conflict_rate", 0)
        if conflict_rate > ALERT_THRESHOLDS["conflict_rate_high"]:
            alerts.append({
                "level": "error",
                "type": "conflict_rate_high",
                "message": f"矛盾率过高: {conflict_rate:.1%} (阈值: {ALERT_THRESHOLDS['conflict_rate_high']:.1%})",
                "timestamp": datetime.now().isoformat()
            })
        
        # 存储空间告警
        storage_mb = metrics["performance"].get("total_storage_mb", 0)
        if storage_mb > ALERT_THRESHOLDS["storage_mb_high"]:
            alerts.append({
                "level": "warning",
                "type": "storage_mb_high",
                "message": f"存储空间过高: {storage_mb:.1f}MB (阈值: {ALERT_THRESHOLDS['storage_mb_high']}MB)",
                "timestamp": datetime.now().isoformat()
            })
        
        # 添加到告警历史
        self.alerts.extend(alerts)
        
        # 只保留最近50条告警
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        return alerts
    
    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """获取趋势分析"""
        if not self.history:
            return {"error": "无历史数据"}
        
        # 过滤指定天数的数据
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in self.history
            if datetime.fromisoformat(h["timestamp"]) > cutoff_time
        ]
        
        if not recent_history:
            return {"error": "指定时间范围内无数据"}
        
        # 计算趋势
        memory_counts = [h["memory_count"] for h in recent_history]
        latencies = [h["search_latency_ms"] for h in recent_history]
        health_scores = [h["health_score"] for h in recent_history]
        
        return {
            "period": f"最近 {days} 天",
            "data_points": len(recent_history),
            "memory_count": {
                "min": min(memory_counts),
                "max": max(memory_counts),
                "avg": sum(memory_counts) / len(memory_counts),
                "trend": "increasing" if memory_counts[-1] > memory_counts[0] else "stable"
            },
            "search_latency": {
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": sum(latencies) / len(latencies),
                "trend": "improving" if latencies[-1] < latencies[0] else "stable"
            },
            "health_score": {
                "min": min(health_scores),
                "max": max(health_scores),
                "avg": sum(health_scores) / len(health_scores),
                "trend": "improving" if health_scores[-1] > health_scores[0] else "stable"
            }
        }
    
    def display_dashboard(self):
        """显示仪表板"""
        metrics = self.collect_metrics()
        
        print("\n" + "="*60)
        print("📊 记忆系统性能仪表板")
        print("="*60)
        
        # 记忆统计
        print("\n📈 记忆统计:")
        stats = metrics["memory_stats"]
        print(f"  总数: {stats.get('total_count', 0)}")
        print(f"  高重要性: {stats.get('by_importance', {}).get('high', 0)}")
        print(f"  最近24h: {stats.get('by_age', {}).get('last_24h', 0)}")
        
        # 性能指标
        print("\n⚡ 性能指标:")
        perf = metrics["performance"]
        print(f"  搜索延迟: {perf.get('search_latency_ms', 0):.1f}ms")
        print(f"  平均记忆大小: {perf.get('avg_memory_size_bytes', 0):.0f} 字节")
        print(f"  总存储: {perf.get('total_storage_mb', 0):.2f}MB")
        
        # 健康状态
        print("\n💚 健康状态:")
        health = metrics["health"]
        print(f"  健康评分: {health.get('health_score', 0):.1f}/100")
        print(f"  矛盾记忆: {health.get('conflict_count', 0)} ({health.get('conflict_rate', 0):.1%})")
        print(f"  过时记忆: {health.get('stale_count', 0)}")
        
        # 告警
        if metrics["alerts"]:
            print("\n⚠️ 告警:")
            for alert in metrics["alerts"]:
                level_icon = "🚨" if alert["level"] == "error" else "⚠️"
                print(f"  {level_icon} {alert['message']}")
        else:
            print("\n✅ 无告警")
        
        print("\n" + "="*60)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="性能仪表板")
    parser.add_argument("command", choices=["show", "collect", "trends", "alerts", "history"])
    parser.add_argument("--days", "-d", type=int, default=7, help="趋势分析天数")
    
    args = parser.parse_args()
    
    dashboard = PerformanceDashboard()
    
    if args.command == "show":
        dashboard.display_dashboard()
    
    elif args.command == "collect":
        metrics = dashboard.collect_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    elif args.command == "trends":
        trends = dashboard.get_trends(args.days)
        print(json.dumps(trends, indent=2, ensure_ascii=False))
    
    elif args.command == "alerts":
        print(f"\n⚠️ 最近告警:")
        for i, alert in enumerate(dashboard.alerts[-10:], 1):
            print(f"\n#{i} [{alert['level']}] {alert['type']}")
            print(f"  {alert['message']}")
            print(f"  时间: {alert['timestamp']}")
    
    elif args.command == "history":
        print(f"\n📊 历史记录 (最近10条):")
        for i, h in enumerate(dashboard.history[-10:], 1):
            print(f"\n#{i} {h['timestamp']}")
            print(f"  记忆数: {h['memory_count']}")
            print(f"  延迟: {h['search_latency_ms']:.1f}ms")
            print(f"  健康: {h['health_score']:.1f}/100")


if __name__ == "__main__":
    main()
