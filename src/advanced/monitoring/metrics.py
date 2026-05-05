"""
指标收集器
"""
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class MetricLabel:
    """指标标签"""
    name: str
    value: str


class MetricValue:
    """指标值"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._values: Dict[str, float] = defaultdict(float)
        self._sums: Dict[str, float] = defaultdict(float)
        self._totals: Dict[str, int] = defaultdict(int)
    
    def inc(self, labels: str, value: float = 1) -> None:
        """递增"""
        with self._lock:
            self._values[labels] += value
    
    def set(self, labels: str, value: float) -> None:
        """设置值"""
        with self._lock:
            self._values[labels] = value
    
    def observe(self, labels: str, value: float) -> None:
        """记录值（用于 Histogram/Summary）"""
        with self._lock:
            self._values[labels] = value
            self._sums[labels] += value
            self._totals[labels] += 1
    
    def get(self, labels: str) -> float:
        """获取值"""
        return self._values.get(labels, 0)
    
    def get_all(self) -> Dict[str, float]:
        """获取所有值"""
        with self._lock:
            return dict(self._values)


class Counter:
    """计数器"""
    
    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values = MetricValue()
    
    def inc(self, value: float = 1, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.inc(labels, value)
    
    def get(self, **label_values) -> float:
        labels = self._make_label_key(label_values)
        return self._values.get(labels)
    
    def get_all(self) -> Dict[str, float]:
        return self._values.get_all()
    
    def _make_label_key(self, label_values: Dict[str, str]) -> str:
        if not self.labels:
            return "_"
        return ",".join(str(label_values.get(l, "")) for l in self.labels)


class Gauge:
    """仪表"""
    
    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values = MetricValue()
    
    def set(self, value: float, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.set(labels, value)
    
    def inc(self, value: float = 1, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.inc(labels, value)
    
    def dec(self, value: float = 1, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.inc(labels, -value)
    
    def get(self, **label_values) -> float:
        labels = self._make_label_key(label_values)
        return self._values.get(labels)
    
    def _make_label_key(self, label_values: Dict[str, str]) -> str:
        if not self.labels:
            return "_"
        return ",".join(str(label_values.get(l, "")) for l in self.labels)


class Histogram:
    """直方图"""
    
    BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: tuple = BUCKETS
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets
        self._values = MetricValue()
        self._counts: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.Lock()
    
    def observe(self, value: float, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.observe(labels, value)
        
        with self._lock:
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[labels][bucket] += 1
    
    def _make_label_key(self, label_values: Dict[str, str]) -> str:
        if not self.labels:
            return "_"
        return ",".join(str(label_values.get(l, "")) for l in self.labels)


class Summary:
    """摘要"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        objectives: tuple = None
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.objectives = objectives or ((0.5, 0.05), (0.9, 0.01), (0.99, 0.001))
        self._values = MetricValue()
        self._lock = threading.Lock()
        self._samples: Dict[str, List[float]] = defaultdict(list)
    
    def observe(self, value: float, **label_values) -> None:
        labels = self._make_label_key(label_values)
        self._values.observe(labels, value)
        
        with self._lock:
            self._samples[labels].append(value)
    
    def _make_label_key(self, label_values: Dict[str, str]) -> str:
        if not self.labels:
            return "_"
        return ",".join(str(label_values.get(l, "")) for l in self.labels)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def register(self, metric) -> None:
        """注册指标"""
        with self._lock:
            self._metrics[metric.name] = metric
    
    def counter(self, name: str, description: str = "", labels: List[str] = None) -> Counter:
        """创建计数器"""
        metric = Counter(name, description, labels)
        self.register(metric)
        return metric
    
    def gauge(self, name: str, description: str = "", labels: List[str] = None) -> Gauge:
        """创建仪表"""
        metric = Gauge(name, description, labels)
        self.register(metric)
        return metric
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: tuple = Histogram.BUCKETS
    ) -> Histogram:
        """创建直方图"""
        metric = Histogram(name, description, labels, buckets)
        self.register(metric)
        return metric
    
    def summary(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        objectives: tuple = None
    ) -> Summary:
        """创建摘要"""
        metric = Summary(name, description, labels, objectives)
        self.register(metric)
        return metric
    
    def render_prometheus(self) -> str:
        """渲染 Prometheus 格式"""
        lines = []
        
        for name, metric in self._metrics.items():
            if isinstance(metric, Counter):
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} counter")
                for labels_key, value in metric.get_all().items():
                    if labels_key == "_":
                        lines.append(f"{name} {value}")
                    else:
                        label_parts = []
                        for i, label in enumerate(metric.labels):
                            parts = labels_key.split(",")
                            if i < len(parts):
                                label_parts.append(f'{label}="{parts[i]}"')
                        lines.append(f"{name}{{{','.join(label_parts)}}} {value}")
            
            elif isinstance(metric, Gauge):
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} gauge")
                for labels_key, value in metric.get_all().items():
                    if labels_key == "_":
                        lines.append(f"{name} {value}")
                    else:
                        label_parts = []
                        for i, label in enumerate(metric.labels):
                            parts = labels_key.split(",")
                            if i < len(parts):
                                label_parts.append(f'{label}="{parts[i]}"')
                        lines.append(f"{name}{{{','.join(label_parts)}}} {value}")
        
        return "\n".join(lines)
