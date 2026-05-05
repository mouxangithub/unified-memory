> 📊 **核心开发者** | 步骤 6/6 | 166.3s

---

<think>The user wants me to implement a complete Unified Memory v5 monitoring metrics module. This is a comprehensive request that includes:

1. Core metrics collector with Counter, Gauge, Histogram, Summary
2. Predefined metrics for API, Cache, System, and Business monitoring
3. Prometheus integration with /metrics endpoint and Pushgateway support
4. Grafana Dashboard configuration
5. Health checks for dependencies

Let me create a well-structured, production-ready implementation with:
- Type hints
- Docstrings
- Proper error handling
- Comprehensive unit tests
- Configuration management

I'll structure it as:
- `memory_v5/monitoring/__init__.py`
- `memory_v5/monitoring/metrics.py` - Core MetricsCollector
- `memory_v5/monitoring/collector.py` - System metrics collection
- `memory_v5/monitoring/prometheus.py` - Prometheus integration
- `memory_v5/monitoring/health.py` - Health checks
- `memory_v5/monitoring/grafana/dashboard.json` - Grafana dashboard
- `memory_v5/monitoring/grafana/alerts.yaml` - Alert rules
- `memory_v5/monitoring/tests/test_metrics.py` - Unit tests
- `memory_v5/monitoring/tests/test_collector.py` - Collector tests

Let me start implementing this comprehensively.
</think>

# Unified Memory v5 监控指标模块实现

我将实现一个完整的生产级监控模块，包含指标收集、Prometheus 集成、Grafana 配置和健康检查。

## 项目结构

```
memory_v5/
└── monitoring/
    ├── __init__.py
    ├── metrics.py            # 核心指标收集器
    ├── collector.py          # 系统指标采集器
    ├── prometheus.py         # Prometheus 集成
    ├── health.py             # 健康检查
    ├── grafana/
    │   ├── __init__.py
    │   ├── dashboard.json    # Dashboard 配置
    │   └── alerts.yaml       # 告警规则
    └── tests/
        ├── __init__.py
        ├── test_metrics.py
        └── test_collector.py
```

## 核心实现

### 1. metrics.py - 核心指标收集器

```python
"""
Unified Memory v5 监控指标核心模块

提供 Counter、Gauge、Histogram、Summary 四种指标类型，
支持 Prometheus 格式导出和多维度标签。
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict
import math


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class LabelSet:
    """标签集合"""
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.labels.items())))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LabelSet):
            return False
        return self.labels == other.labels
    
    def matches(self, label_selector: Optional[Dict[str, str]]) -> bool:
        """检查标签是否匹配选择器"""
        if label_selector is None:
            return True
        return all(
            self.labels.get(k) == v 
            for k, v in label_selector.items()
        )


class Metric(ABC):
    """指标基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        metric_type: MetricType,
        label_names: Tuple[str, ...] = (),
        namespace: str = ""
    ):
        self.name = name
        self.full_name = f"{namespace}_{name}" if namespace else name
        self.description = description
        self.metric_type = metric_type
        self.label_names = label_names
        self.namespace = namespace
        
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """收集指标数据"""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """重置指标"""
        pass
    
    def _format_labels(self, label_values: Tuple[str, ...]) -> str:
        """格式化标签为 Prometheus 格式"""
        if not label_values:
            return ""
        return ",".join(
            f'{ln}="{lv}"' 
            for ln, lv in zip(self.label_names, label_values)
        )


class Counter(Metric):
    """
    计数器 - 只增不减的指标
    用于：请求数、错误数、字节数等
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        namespace: str = ""
    ):
        super().__init__(name, description, MetricType.COUNTER, label_names, namespace)
        self._values: Dict[LabelSet, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器"""
        with self._lock:
            label_set = LabelSet(labels or {})
            self._values[label_set] += value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取当前值"""
        label_set = LabelSet(labels or {})
        return self._values.get(label_set, 0)
    
    def collect(self) -> List[Dict[str, Any]]:
        """收集指标数据"""
        with self._lock:
            result = []
            for label_set, value in self._values.items():
                result.append({
                    "name": self.full_name,
                    "description": self.description,
                    "type": "counter",
                    "labels": label_set.labels,
                    "value": value
                })
            return result
    
    def reset(self) -> None:
        """重置所有计数器"""
        with self._lock:
            self._values.clear()


class Gauge(Metric):
    """
    仪表 - 可以增减的指标
    用于：当前连接数、队列长度、当前内存使用等
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        namespace: str = ""
    ):
        super().__init__(name, description, MetricType.GAUGE, label_names, namespace)
        self._values: Dict[LabelSet, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置 gauge 值"""
        with self._lock:
            label_set = LabelSet(labels or {})
            self._values[label_set] = value
    
    def inc(self, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """增加 gauge 值"""
        with self._lock:
            label_set = LabelSet(labels or {})
            self._values[label_set] += value
    
    def dec(self, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """减少 gauge 值"""
        with self._lock:
            label_set = LabelSet(labels or {})
            self._values[label_set] -= value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取当前值"""
        label_set = LabelSet(labels or {})
        return self._values.get(label_set, 0)
    
    def collect(self) -> List[Dict[str, Any]]:
        """收集指标数据"""
        with self._lock:
            result = []
            for label_set, value in self._values.items():
                result.append({
                    "name": self.full_name,
                    "description": self.description,
                    "type": "gauge",
                    "labels": label_set.labels,
                    "value": value
                })
            return result
    
    def reset(self) -> None:
        """重置所有 gauge"""
        with self._lock:
            self._values.clear()


class Histogram(Metric):
    """
    直方图 - 记录值的分布
    用于：请求延迟、响应大小等
    
    预定义的 bucket 边界：0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
    """
    
    DEFAULT_BUCKETS = (
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    )
    
    def __init__(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        buckets: Tuple[float, ...] = None,
        namespace: str = ""
    ):
        super().__init__(name, description, MetricType.HISTOGRAM, label_names, namespace)
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[LabelSet, Dict[str, int]] = defaultdict(
            lambda: {"+Inf": 0}
        )
        self._sums: Dict[LabelSet, float] = defaultdict(float)
        self._totals: Dict[LabelSet, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录观测值"""
        with self._lock:
            label_set = LabelSet(labels or {})
            
            # 更新 bucket 计数
            for boundary in self.buckets:
                if value <= boundary:
                    bucket_key = f"{boundary}"
                    if bucket_key not in self._counts[label_set]:
                        self._counts[label_set][bucket_key] = 0
                    self._counts[label_set][bucket_key] += 1
            
            self._counts[label_set]["+Inf"] += 1
            self._sums[label_set] += value
            self._totals[label_set] += 1
    
    def collect(self) -> List[Dict[str, Any]]:
        """收集指标数据"""
        with self._lock:
            result = []
            for label_set in self._counts:
                labels = label_set.labels
                
                # 计算累积计数
                cumulative = 0
                for boundary in self.buckets:
                    bucket_key = str(boundary)
                    cumulative += self._counts[label_set].get(bucket_key, 0)
                    result.append({
                        "name": f"{self.full_name}_bucket",
                        "description": f"{self.description} (bucket <= {boundary})",
                        "type": "histogram",
                        "labels": {**labels, "le": str(boundary)},
                        "value": cumulative
                    })
                
                # +Inf bucket
                result.append({
                    "name": f"{self.full_name}_bucket",
                    "description": f"{self.description} (bucket <= +Inf)",
                    "type": "histogram",
                    "labels": {**labels, "le": "+Inf"},
                    "value": self._counts[label_set]["+Inf"]
                })
                
                # sum 和 count
                result.append({
                    "name": f"{self.full_name}_sum",
                    "description": f"{self.description} (sum)",
                    "type": "histogram",
                    "labels": labels,
                    "value": self._sums[label_set]
                })
                result.append({
                    "name": f"{self.full_name}_count",
                    "description": f"{self.description} (count)",
                    "type": "histogram",
                    "labels": labels,
                    "value": self._totals[label_set]
                })
            
            return result
    
    def reset(self) -> None:
        """重置直方图"""
        with self._lock:
            self._counts.clear()
            self._sums.clear()
            self._totals.clear()


class Summary(Metric):
    """
    汇总 - 记录分位数
    用于：计算 P50、P95、P99 等延迟指标
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        quantiles: Tuple[Tuple[str, float], ...] = None,
        namespace: str = ""
    ):
        super().__init__(name, description, MetricType.SUMMARY, label_names, namespace)
        self.quantiles = quantiles or (
            ("0.5", 0.5),
            ("0.9", 0.9),
            ("0.95", 0.95),
            ("0.99", 0.99),
        )
        self._values: Dict[LabelSet, List[float]] = defaultdict(list)
        self._sums: Dict[LabelSet, float] = defaultdict(float)
        self._totals: Dict[LabelSet, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._max_values = 10000  # 保留最近的值用于计算分位数
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录观测值"""
        with self._lock:
            label_set = LabelSet(labels or {})
            
            # 保留最近的值
            values_list = self._values[label_set]
            values_list.append(value)
            if len(values_list) > self._max_values:
                # 移除最早的一半值
                self._values[label_set] = values_list[len(values_list) // 2:]
            
            self._sums[label_set] += value
            self._totals[label_set] += 1
    
    def _calculate_quantile(self, values: List[float], quantile: float) -> float:
        """计算分位数"""
        if not values:
            return float('nan')
        
        sorted_values = sorted(values)
        index = quantile * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        
        lower = int(math.floor(index))
        upper = int(math.ceil(index))
        weight = index - lower
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def collect(self) -> List[Dict[str, Any]]:
        """收集指标数据"""
        with self._lock:
            result = []
            for label_set, values in self._values.items():
                labels = label_set.labels
                
                # 计算每个分位数
                for q_name, q_value in self.quantiles:
                    quantile_result = self._calculate_quantile(values, q_value)
                    result.append({
                        "name": f"{self.full_name}",
                        "description": f"{self.description} (quantile {q_name})",
                        "type": "summary",
                        "labels": {**labels, "quantile": q_name},
                        "value": quantile_result
                    })
                
                # sum 和 count
                result.append({
                    "name": f"{self.full_name}_sum",
                    "description": f"{self.description} (sum)",
                    "type": "summary",
                    "labels": labels,
                    "value": self._sums[label_set]
                })
                result.append({
                    "name": f"{self.full_name}_count",
                    "description": f"{self.description} (count)",
                    "type": "summary",
                    "labels": labels,
                    "value": self._totals[label_set]
                })
            
            return result
    
    def reset(self) -> None:
        """重置汇总"""
        with self._lock:
            self._values.clear()
            self._sums.clear()
            self._totals.clear()


class MetricsCollector:
    """
    指标收集器 - 统一管理所有指标
    
    支持:
    - 自动注册预定义指标
    - Prometheus 格式导出
    - 线程安全
    """
    
    # 预定义指标常量
    # API 指标
    API_REQUESTS_TOTAL = "api_requests_total"
    API_REQUEST_DURATION_SECONDS = "api_request_duration_seconds"
    API_REQUEST_SIZE_BYTES = "api_request_size_bytes"
    API_RESPONSE_SIZE_BYTES = "api_response_size_bytes"
    
    # 缓存指标
    CACHE_HITS_TOTAL = "cache_hits_total"
    CACHE_MISSES_TOTAL = "cache_misses_total"
    CACHE_HIT_RATIO = "cache_hit_ratio"
    CACHE_SIZE_BYTES = "cache_size_bytes"
    
    # 系统指标
    SYSTEM_CPU_PERCENT = "system_cpu_percent"
    SYSTEM_MEMORY_PERCENT = "system_memory_percent"
    SYSTEM_MEMORY_BYTES = "system_memory_bytes"
    SYSTEM_DISK_IO_BYTES = "system_disk_io_bytes"
    SYSTEM_NETWORK_IO_BYTES = "system_network_io_bytes"
    
    # 业务指标
    MEMORY_COUNT = "memory_count"
    VERSION_COUNT = "version_count"
    ARCHIVE_RATIO = "archive_ratio"
    QUEUE_LENGTH = "queue_length"
    ACTIVE_CONNECTIONS = "active_connections"
    
    # 健康指标
    HEALTH_CHECK_STATUS = "health_check_status"
    
    def __init__(self, namespace: str = "memory_v5"):
        self.namespace = namespace
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.RLock()
        
        # 注册预定义指标
        self._register_builtin_metrics()
    
    def _register_builtin_metrics(self) -> None:
        """注册预定义指标"""
        # API 指标
        self.register_counter(
            self.API_REQUESTS_TOTAL,
            "Total number of API requests",
            label_names=("namespace", "method", "status")
        )
        self.register_histogram(
            self.API_REQUEST_DURATION_SECONDS,
            "API request duration in seconds",
            label_names=("namespace", "method")
        )
        self.register_histogram(
            self.API_REQUEST_SIZE_BYTES,
            "API request size in bytes",
            label_names=("namespace", "method")
        )
        self.register_histogram(
            self.API_RESPONSE_SIZE_BYTES,
            "API response size in bytes",
            label_names=("namespace", "method")
        )
        
        # 缓存指标
        self.register_counter(
            self.CACHE_HITS_TOTAL,
            "Total number of cache hits",
            label_names=("level", "namespace")
        )
        self.register_counter(
            self.CACHE_MISSES_TOTAL,
            "Total number of cache misses",
            label_names=("level", "namespace")
        )
        self.register_gauge(
            self.CACHE_HIT_RATIO,
            "Cache hit ratio",
            label_names=("level", "namespace")
        )
        self.register_gauge(
            self.CACHE_SIZE_BYTES,
            "Cache size in bytes",
            label_names=("level", "namespace")
        )
        
        # 系统指标
        self.register_gauge(
            self.SYSTEM_CPU_PERCENT,
            "System CPU usage percent"
        )
        self.register_gauge(
            self.SYSTEM_MEMORY_PERCENT,
            "System memory usage percent"
        )
        self.register_gauge(
            self.SYSTEM_MEMORY_BYTES,
            "System memory usage in bytes",
            label_names=("type",)  # used, free, available
        )
        self.register_counter(
            self.SYSTEM_DISK_IO_BYTES,
            "System disk I/O in bytes",
            label_names=("direction",)  # read, write
        )
        self.register_counter(
            self.SYSTEM_NETWORK_IO_BYTES,
            "System network I/O in bytes",
            label_names=("direction",)  # sent, received
        )
        
        # 业务指标
        self.register_gauge(
            self.MEMORY_COUNT,
            "Number of memories",
            label_names=("namespace",)
        )
        self.register_gauge(
            self.VERSION_COUNT,
            "Number of versions per memory",
            label_names=("memory_id",)
        )
        self.register_gauge(
            self.ARCHIVE_RATIO,
            "Archive ratio",
            label_names=("namespace",)
        )
        self.register_gauge(
            self.QUEUE_LENGTH,
            "Queue length"
        )
        self.register_gauge(
            self.ACTIVE_CONNECTIONS,
            "Number of active connections"
        )
        
        # 健康检查指标
        self.register_gauge(
            self.HEALTH_CHECK_STATUS,
            "Health check status (1=healthy, 0=unhealthy)",
            label_names=("component",)
        )
    
    def register_counter(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = ()
    ) -> Counter:
        """注册计数器"""
        with self._lock:
            metric = Counter(name, description, label_names, self.namespace)
            self._metrics[name] = metric
            return metric
    
    def register_gauge(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = ()
    ) -> Gauge:
        """注册仪表"""
        with self._lock:
            metric = Gauge(name, description, label_names, self.namespace)
            self._metrics[name] = metric
            return metric
    
    def register_histogram(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        buckets: Tuple[float, ...] = None
    ) -> Histogram:
        """注册直方图"""
        with self._lock:
            metric = Histogram(
                name, description, label_names, buckets, self.namespace
            )
            self._metrics[name] = metric
            return metric
    
    def register_summary(
        self,
        name: str,
        description: str,
        label_names: Tuple[str, ...] = (),
        quantiles: Tuple[Tuple[str, float], ...] = None
    ) -> Summary:
        """注册汇总"""
        with self._lock:
            metric = Summary(
                name, description, label_names, quantiles, self.namespace
            )
            self._metrics[name] = metric
            return metric
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        with self._lock:
            return self._metrics.get(name)
    
    def counter(self, name: str) -> Counter:
        """获取或创建计数器"""
        with self._lock:
            if name not in self._metrics:
                self.register_counter(name, f"Counter for {name}")
            return self._metrics[name]
    
    def gauge(self, name: str) -> Gauge:
        """获取或创建仪表"""
        with self._lock:
            if name not in self._metrics:
                self.register_gauge(name, f"Gauge for {name}")
            return self._metrics[name]
    
    def histogram(self, name: str) -> Histogram:
        """获取或创建直方图"""
        with self._lock:
            if name not in self._metrics:
                self.register_histogram(name, f"Histogram for {name}")
            return self._metrics[name]
    
    def summary(self, name: str) -> Summary:
        """获取或创建汇总"""
        with self._lock:
            if name not in self._metrics:
                self.register_summary(name, f"Summary for {name}")
            return self._metrics[name]
    
    def record_request(
        self,
        namespace: str,
        method: str,
        status: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0
    ) -> None:
        """记录 API 请求"""
        # 请求计数
        self.counter(self.API_REQUESTS_TOTAL).inc(
            labels={"namespace": namespace, "method": method, "status": str(status)}
        )
        
        # 延迟直方图
        self.histogram(self.API_REQUEST_DURATION_SECONDS).observe(
            duration,
            labels={"namespace": namespace, "method": method}
        )
        
        # 请求大小
        if request_size > 0:
            self.histogram(self.API_REQUEST_SIZE_BYTES).observe(
                float(request_size),
                labels={"namespace": namespace, "method": method}
            )
        
        # 响应大小
        if response_size > 0:
            self.histogram(self.API_RESPONSE_SIZE_BYTES).observe(
                float(response_size),
                labels={"namespace": namespace, "method": method}
            )
    
    def record_cache_operation(
        self,
        level: str,
        namespace: str,
        hit: bool
    ) -> None:
        """记录缓存操作"""
        labels = {"level": level, "namespace": namespace}
        
        if hit:
            self.counter(self.CACHE_HITS_TOTAL).inc(labels=labels)
        else:
            self.counter(self.CACHE_MISSES_TOTAL).inc(labels=labels)
        
        # 更新命中率
        hits = self.counter(self.CACHE_HITS_TOTAL).get(labels=labels)
        misses = self.counter(self.CACHE_MISSES_TOTAL).get(labels=labels)
        total = hits + misses
        
        if total > 0:
            self.gauge(self.CACHE_HIT_RATIO).set(
                hits / total,
                labels=labels
            )
    
    def collect_all(self) -> List[Dict[str, Any]]:
        """收集所有指标"""
        with self._lock:
            all_metrics = []
            for metric in self._metrics.values():
                all_metrics.extend(metric.collect())
            return all_metrics
    
    def export_prometheus(self) -> str:
        """导出 Prometheus 格式"""
        lines = []
        metrics = self.collect_all()
        
        # 按指标名称分组
        by_name: Dict[str, List[Dict]] = defaultdict(list)
        for m in metrics:
            by_name[m["name"]].append(m)
        
        for name, metric_list in by_name.items():
            if not metric_list:
                continue
            
            # 获取第一个指标获取类型和帮助
            first = metric_list[0]
            metric_type = first["type"]
            description = first["description"]
            
            lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} {metric_type}")
            
            for m in metric_list:
                labels_str = ""
                if m["labels"]:
                    label_parts = []
                    for k, v in m["labels"].items():
                        label_parts.append(f'{k}="{v}"')
                    labels_str = "{" + ",".join(label_parts) + "}"
                
                value = m["value"]
                if metric_type == "summary" and value is not None:
                    if math.isnan(value):
                        value = "NaN"
                    elif math.isinf(value):
                        value = "+Inf"
                
                lines.append(f"{name}{labels_str} {value}")
        
        return "\n".join(lines) + "\n"
    
    def reset_all(self) -> None:
        """重置所有指标"""
        with self._lock:
            for metric in self._metrics.values():
                metric.reset()


# 全局单例
_global_collector: Optional[MetricsCollector] = None


def get_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def reset_collector() -> None:
    """重置全局指标收集器"""
    global _global_collector
    if _global_collector is not None:
        _global_collector.reset_all()
        _global_collector = None
```

### 2. collector.py - 系统指标采集器

```python
"""
Unified Memory v5 系统指标采集器

采集系统级指标：CPU、内存、磁盘IO、网络IO等
"""

from __future__ import annotations

import os
import time
import platform
import threading
import psutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

from .metrics import MetricsCollector, get_collector


@dataclass
class SystemMetrics:
    """系统指标快照"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_bytes: int
    memory_free_bytes: int
    memory_available_bytes: int
    disk_read_bytes: int
    disk_write_bytes: int
    network_sent_bytes: int
    network_recv_bytes: int


class MetricsSource(ABC):
    """指标源抽象基类"""
    
    @abstractmethod
    def collect(self) -> Dict[str, float]:
        """采集指标"""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """指标源名称"""
        pass


class CPUCollector(MetricsSource):
    """CPU 指标采集器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._last_cpu_times: Optional[psutil._pslinux.cpu_times] = None
        self._last_time: Optional[float] = None
        self._lock = threading.Lock()
    
    def name(self) -> str:
        return "cpu"
    
    def collect(self) -> Dict[str, float]:
        with self._lock:
            current = psutil.cpu_percent(interval=None, percpu=False)
            return {"cpu_percent": current}
    
    def collect_detailed(self) -> Dict[str, float]:
        """采集详细 CPU 指标"""
        cpu_times = psutil.cpu_times()
        cpu_stats = psutil.cpu_stats()
        
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        
        result = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_user_percent": cpu_times.user,
            "cpu_system_percent": cpu_times.system,
            "cpu_idle_percent": cpu_times.idle,
            "cpu_interrupt_count": cpu_stats.interrupts,
            "cpu_soft_interrupt_count": cpu_stats.soft_interrupts,
        }
        
        for i, pct in enumerate(per_cpu):
            result[f"cpu_percent_core_{i}"] = pct
        
        return result


class MemoryCollector(MetricsSource):
    """内存指标采集器"""
    
    def name(self) -> str:
        return "memory"
    
    def collect(self) -> Dict[str, float]:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "memory_percent": mem.percent,
            "memory_used_bytes": mem.used,
            "memory_free_bytes": mem.free,
            "memory_available_bytes": mem.available,
            "memory_total_bytes": mem.total,
            "swap_percent": swap.percent,
            "swap_used_bytes": swap.used,
            "swap_free_bytes": swap.free,
        }


class DiskIOCollector(MetricsSource):
    """磁盘 IO 指标采集器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._last_io_counters: Optional[psutil.DiskIOStats] = None
        self._last_time: Optional[float] = None
        self._lock = threading.Lock()
    
    def name(self) -> str:
        return "disk_io"
    
    def collect(self) -> Dict[str, float]:
        with self._lock:
            try:
                io_counters = psutil.disk_io_counters()
            except Exception:
                return {}
            
            if io_counters is None:
                return {}
            
            current_time = time.time()
            
            result = {
                "disk_read_bytes": io_counters.read_bytes,
                "disk_write_bytes": io_counters.write_bytes,
                "disk_read_count": io_counters.read_count,
                "disk_write_count": io_counters.write_count,
            }
            
            if self._last_io_counters and self._last_time:
                time_delta = current_time - self._last_time
                
                if time_delta > 0:
                    read_bytes_delta = io_counters.read_bytes - self._last_io_counters.read_bytes
                    write_bytes_delta = io_counters.write_bytes - self._last_io_counters.write_bytes
                    
                    result["disk_read_bytes_per_sec"] = max(0, read_bytes_delta / time_delta)
                    result["disk_write_bytes_per_sec"] = max(0, write_bytes_delta / time_delta)
            
            self._last_io_counters = io_counters
            self._last_time = current_time
            
            return result


class NetworkIOCollector(MetricsSource):
    """网络 IO 指标采集器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._last_counters: Optional[Dict[str, psutil.net_io_counters]] = None
        self._last_time: Optional[float] = None
        self._lock = threading.Lock()
    
    def name(self) -> str:
        return "network_io"
    
    def collect(self) -> Dict[str, float]:
        with self._lock:
            try:
                net_counters = psutil.net_io_counters(pernic=True)
            except Exception:
                return {}
            
            current_time = time.time()
            
            # 聚合所有网卡的总数
            total_sent = sum(c.bytes_sent for c in net_counters.values())
            total_recv = sum(c.bytes_recv for c in net_counters.values())
            
            result = {
                "network_sent_bytes": total_sent,
                "network_recv_bytes": total_recv,
                "network_sent_packets": sum(c.packets_sent for c in net_counters.values()),
                "network_recv_packets": sum(c.packets_recv for c in net_counters.values()),
                "network_err_in": sum(c.errin for c in net_counters.values()),
                "network_err_out": sum(c.errout for c in net_counters.values()),
                "network_drop_in": sum(c.dropin for c in net_counters.values()),
                "network_drop_out": sum(c.dropout for c in net_counters.values()),
            }
            
            if self._last_counters and self._last_time:
                time_delta = current_time - self._last_time
                
                if time_delta > 0:
                    last_total_sent = sum(c.bytes_sent for c in self._last_counters.values())
                    last_total_recv = sum(c.bytes_recv for c in self._last_counters.values())
                    
                    result["network_sent_bytes_per_sec"] = max(0, (total_sent - last_total_sent) / time_delta)
                    result["network_recv_bytes_per_sec"] = max(0, (total_recv - last_total_recv) / time_delta)
            
            self._last_counters = net_counters
            self._last_time = current_time
            
            return result


class ProcessCollector(MetricsSource):
    """进程级指标采集器"""
    
    def __init__(self, pid: Optional[int] = None):
        self.pid = pid or os.getpid()
        self._process: Optional[psutil.Process] = None
    
    def name(self) -> str:
        return "process"
    
    def _get_process(self) -> psutil.Process:
        if self._process is None:
            self._process = psutil.Process(self.pid)
        return self._process
    
    def collect(self) -> Dict[str, float]:
        try:
            process = self._get_process()
            
            with process.oneshot():
                cpu_percent = process.cpu_percent()
                mem_info = process.memory_info()
                mem_full_info = process.memory_full_info()
                
                result = {
                    "process_cpu_percent": cpu_percent,
                    "process_memory_rss_bytes": mem_info.rss,
                    "process_memory_vms_bytes": mem_info.vms,
                    "process_memory_shared_bytes": getattr(mem_info, 'shared', 0),
                    "process_memory_percent": process.memory_percent(),
                }
                
                # 尝试获取更多指标
                try:
                    io_counters = process.io_counters()
                    result["process_io_read_bytes"] = io_counters.read_bytes
                    result["process_io_write_bytes"] = io_counters.write_bytes
                except (AttributeError, psutil.AccessDenied):
                    pass
                
                try:
                    num_fds = process.num_fds()
                    result["process_num_fds"] = num_fds
                except (AttributeError, psutil.AccessDenied):
                    pass
                
                try:
                    threads = process.num_threads()
                    result["process_num_threads"] = threads
                except psutil.NoSuchProcess:
                    pass
                
                return result
                
        except psutil.NoSuchProcess:
            return {}
        except Exception as e:
            return {"error": str(e)}


class SystemMetricsCollector:
    """
    系统指标采集器 - 周期性采集系统级指标
    
    支持:
    - 多种指标源
    - 回调函数注册
    - 速率计算
    """
    
    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        collection_interval: float = 10.0
    ):
        self.metrics_collector = collector or get_collector()
        self.collection_interval = collection_interval
        self._sources: List[MetricsSource] = []
        self._callbacks: List[Callable[[SystemMetrics], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self._disk_io_collector = DiskIOCollector()
        self._network_io_collector = NetworkIOCollector()
        
        self._register_default_sources()
    
    def _register_default_sources(self) -> None:
        """注册默认指标源"""
        self.add_source(CPUCollector())
        self.add_source(MemoryCollector())
        self.add_source(DiskIOCollector())
        self.add_source(NetworkIOCollector())
        self.add_source(ProcessCollector())
    
    def add_source(self, source: MetricsSource) -> None:
        """添加指标源"""
        with self._lock:
            self._sources.append(source)
    
    def register_callback(self, callback: Callable[[SystemMetrics], None]) -> None:
        """注册回调函数"""
        with self._lock:
            self._callbacks.append(callback)
    
    def collect_once