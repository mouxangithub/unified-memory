#!/usr/bin/env python3
"""
Monitoring System - 监控和可观测性

功能:
- Metrics (延迟、成功率、Token 消耗)
- Traces (请求链路追踪)
- Alerts (异常告警)
- Dashboard (可视化)
"""

import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
import functools

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============ 数据模型 ============

@dataclass
class Metric:
    """指标"""
    name: str
    value: float
    timestamp: str
    labels: Dict[str, str]


@dataclass
class Trace:
    """链路追踪"""
    trace_id: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    error: Optional[str] = None


@dataclass
class Alert:
    """告警"""
    name: str
    level: str  # info, warning, error, critical
    message: str
    timestamp: str
    resolved: bool = False


# ============ Metrics 收集器 ============

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or Path.home() / ".openclaw" / "workspace" / "memory" / "metrics.json")
        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def counter(self, name: str, value: float = 1, labels: Dict = None):
        """计数器"""
        with self._lock:
            key = f"{name}:{json.dumps(labels or {})}"
            self.counters[key] += value
            
            self.metrics.append(Metric(
                name=name,
                value=self.counters[key],
                timestamp=datetime.now().isoformat(),
                labels=labels or {}
            ))
    
    def gauge(self, name: str, value: float, labels: Dict = None):
        """仪表盘"""
        with self._lock:
            self.metrics.append(Metric(
                name=name,
                value=value,
                timestamp=datetime.now().isoformat(),
                labels=labels or {}
            ))
    
    def histogram(self, name: str, value: float, labels: Dict = None):
        """直方图"""
        with self._lock:
            key = f"{name}:{json.dumps(labels or {})}"
            self.histograms[key].append(value)
            
            self.metrics.append(Metric(
                name=name,
                value=value,
                timestamp=datetime.now().isoformat(),
                labels=labels or {}
            ))
    
    def get_stats(self) -> Dict:
        """获取统计"""
        with self._lock:
            stats = {
                "counters": dict(self.counters),
                "histograms": {}
            }
            
            # 直方图统计
            for key, values in self.histograms.items():
                if values:
                    stats["histograms"][key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": sorted(values)[int(len(values) * 0.5)] if len(values) > 1 else values[0],
                        "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
                        "p99": sorted(values)[int(len(values) * 0.99)] if len(values) > 1 else values[0],
                    }
            
            return stats
    
    def save(self):
        """保存到文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.get_stats(), ensure_ascii=False, indent=2))


# ============ Tracer ============

class Tracer:
    """链路追踪"""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self._lock = threading.Lock()
    
    def start(self, operation: str, trace_id: str = None) -> str:
        """开始追踪"""
        import uuid
        trace_id = trace_id or str(uuid.uuid4())[:8]
        
        with self._lock:
            self.traces[trace_id] = Trace(
                trace_id=trace_id,
                operation=operation,
                start_time=time.time()
            )
        
        return trace_id
    
    def end(self, trace_id: str, error: str = None):
        """结束追踪"""
        with self._lock:
            if trace_id in self.traces:
                trace = self.traces[trace_id]
                trace.end_time = time.time()
                trace.duration_ms = (trace.end_time - trace.start_time) * 1000
                trace.status = "error" if error else "success"
                trace.error = error
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取追踪"""
        return self.traces.get(trace_id)
    
    def get_recent(self, limit: int = 100) -> List[Trace]:
        """获取最近的追踪"""
        with self._lock:
            return sorted(self.traces.values(), key=lambda t: t.start_time, reverse=True)[:limit]


# ============ Alert Manager ============

class AlertManager:
    """告警管理"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or Path.home() / ".openclaw" / "workspace" / "memory" / "alerts.json")
        self.alerts: List[Alert] = []
        self.handlers: List[Callable] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: Callable):
        """添加告警处理器"""
        self.handlers.append(handler)
    
    def alert(self, name: str, level: str, message: str):
        """触发告警"""
        alert = Alert(
            name=name,
            level=level,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # 调用处理器
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"⚠️ 告警处理器错误: {e}")
        
        # 打印
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🔥"}.get(level, "❓")
        print(f"{emoji} [{level.upper()}] {name}: {message}")
    
    def resolve(self, alert_name: str):
        """解决告警"""
        with self._lock:
            for alert in self.alerts:
                if alert.name == alert_name and not alert.resolved:
                    alert.resolved = True
    
    def get_active(self) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            return [a for a in self.alerts if not a.resolved]


# ============ 装饰器 ============

def monitored(operation: str, metrics: MetricsCollector = None, tracer: Tracer = None):
    """监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = None
            
            # 开始追踪
            if tracer:
                trace_id = tracer.start(operation)
            
            start_time = time.time()
            error = None
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功
                if metrics:
                    metrics.counter(f"{operation}_total", labels={"status": "success"})
                    metrics.histogram(f"{operation}_duration_ms", (time.time() - start_time) * 1000)
                
                return result
            
            except Exception as e:
                error = str(e)
                
                # 记录失败
                if metrics:
                    metrics.counter(f"{operation}_total", labels={"status": "error"})
                    metrics.histogram(f"{operation}_duration_ms", (time.time() - start_time) * 1000)
                
                raise
            
            finally:
                # 结束追踪
                if tracer and trace_id:
                    tracer.end(trace_id, error)
        
        return wrapper
    return decorator


# ============ 监控系统 ============

class MonitoringSystem:
    """监控系统"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = MetricsCollector()
            cls._instance.tracer = Tracer()
            cls._instance.alerts = AlertManager()
        return cls._instance
    
    def record_operation(self, operation: str, duration_ms: float, success: bool = True):
        """记录操作"""
        self.metrics.counter(f"{operation}_total", labels={"status": "success" if success else "error"})
        self.metrics.histogram(f"{operation}_duration_ms", duration_ms)
    
    def get_dashboard_data(self) -> Dict:
        """获取仪表盘数据"""
        return {
            "metrics": self.metrics.get_stats(),
            "recent_traces": [asdict(t) for t in self.tracer.get_recent(20)],
            "active_alerts": [asdict(a) for a in self.alerts.get_active()],
            "timestamp": datetime.now().isoformat()
        }


# 全局实例
monitoring = MonitoringSystem()


# ============ CLI 入口 ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="监控系统")
    parser.add_argument("command", choices=["stats", "traces", "alerts", "dashboard"])
    
    args = parser.parse_args()
    
    if args.command == "stats":
        stats = monitoring.metrics.get_stats()
        print("📊 指标统计\n")
        print(f"Counters: {len(stats['counters'])}")
        print(f"Histograms: {len(stats['histograms'])}")
        
        for key, hist in stats['histograms'].items():
            print(f"\n{key}:")
            print(f"  Count: {hist['count']}")
            print(f"  Avg: {hist['avg']:.2f}ms")
            print(f"  P95: {hist['p95']:.2f}ms")
    
    elif args.command == "traces":
        traces = monitoring.tracer.get_recent(10)
        print("🔍 最近追踪\n")
        for trace in traces:
            status = "✅" if trace.status == "success" else "❌"
            print(f"{status} {trace.operation} ({trace.duration_ms:.2f}ms)")
    
    elif args.command == "alerts":
        alerts = monitoring.alerts.get_active()
        print("🚨 活跃告警\n")
        if alerts:
            for alert in alerts:
                print(f"[{alert.level}] {alert.name}: {alert.message}")
        else:
            print("无活跃告警")
    
    elif args.command == "dashboard":
        import json
        print(json.dumps(monitoring.get_dashboard_data(), indent=2))


if __name__ == "__main__":
    main()
