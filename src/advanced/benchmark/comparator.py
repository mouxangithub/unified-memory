"""
基准测试对比器
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from .benchmark import BenchmarkResult


@dataclass
class ComparisonReport:
    """对比报告"""
    baseline_result: BenchmarkResult
    current_result: BenchmarkResult
    
    # 性能变化
    ops_per_second_change: float  # 百分比
    latency_change: float  # 百分比
    error_rate_change: float
    
    # 判断
    is_improvement: bool
    summary: str


class BenchmarkComparator:
    """基准测试对比器"""
    
    def compare(
        self,
        baseline_path: str,
        current_path: str
    ) -> ComparisonReport:
        """对比两个基准测试结果"""
        baseline = self._load_result(baseline_path)
        current = self._load_result(current_path)
        
        ops_change = self._calculate_change(
            baseline.ops_per_second,
            current.ops_per_second
        )
        
        latency_change = self._calculate_change(
            baseline.avg_latency_ms,
            current.avg_latency_ms
        )
        
        error_change = self._calculate_change(
            baseline.error_rate,
            current.error_rate
        )
        
        is_improvement = (
            ops_change > 0 and
            latency_change < 0 and
            error_change < 0
        )
        
        summary = self._generate_summary(ops_change, latency_change, error_change, is_improvement)
        
        return ComparisonReport(
            baseline_result=baseline,
            current_result=current,
            ops_per_second_change=ops_change,
            latency_change=latency_change,
            error_rate_change=error_change,
            is_improvement=is_improvement,
            summary=summary
        )
    
    def _load_result(self, path: str) -> BenchmarkResult:
        """加载结果"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        config_data = data.pop('config')
        from .benchmark import BenchmarkConfig
        config = BenchmarkConfig(**config_data)
        data['config'] = config
        
        return BenchmarkResult(**data)
    
    def _calculate_change(self, baseline: float, current: float) -> float:
        """计算变化百分比"""
        if baseline == 0:
            return 0
        return ((current - baseline) / baseline) * 100
    
    def _generate_summary(
        self,
        ops_change: float,
        latency_change: float,
        error_change: float,
        is_improvement: bool
    ) -> str:
        """生成总结"""
        direction = "improved" if is_improvement else "regressed"
        
        parts = []
        if ops_change != 0:
            parts.append(f"throughput {'+' if ops_change > 0 else ''}{ops_change:.1f}%")
        if latency_change != 0:
            parts.append(f"latency {'-' if latency_change < 0 else '+'}{abs(latency_change):.1f}%")
        if error_change != 0:
            parts.append(f"error rate {'-' if error_change < 0 else '+'}{abs(error_change):.1f}%")
        
        return f"Performance {direction}: {', '.join(parts)}"
