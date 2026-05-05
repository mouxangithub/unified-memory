"""
性能基准测试
"""
import json
import time
import random
import string
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    name: str = "unified_memory_benchmark"
    
    # 操作数
    num_operations: int = 10000
    num_warmup: int = 1000
    
    # 并发
    num_workers: int = 10
    batch_size: int = 100
    
    # 数据大小
    min_memory_size: int = 100
    max_memory_size: int = 10000
    num_memories: int = 1000
    
    # 目标 QPS
    target_qps: int = 1000


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    config: BenchmarkConfig
    start_time: str
    end_time: str
    duration_seconds: float
    
    # 吞吐量
    total_operations: int
    ops_per_second: float
    
    # 延迟
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    
    # 错误
    total_errors: int
    error_rate: float
    
    # 详细统计
    operation_stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['config'] = asdict(self.config)
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self._latencies: List[float] = []
        self._errors: int = 0
        self._operation_counts: Dict[str, int] = {}
    
    def run(self) -> BenchmarkResult:
        """运行基准测试"""
        print(f"Starting benchmark: {self.config.name}")
        print(f"Operations: {self.config.num_operations}, Workers: {self.config.num_workers}")
        
        start_time = datetime.now()
        
        # 预热
        print("Warming up...")
        self._run_warmup()
        
        # 运行测试
        print("Running benchmark...")
        self._run_benchmark()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成结果
        result = self._generate_result(start_time, end_time, duration)
        
        print(f"\nBenchmark completed in {duration:.2f}s")
        print(f"Operations: {result.total_operations}, OPS: {result.ops_per_second:.2f}")
        print(f"Avg latency: {result.avg_latency_ms:.2f}ms, P99: {result.p99_latency_ms:.2f}ms")
        print(f"Errors: {result.total_errors} ({result.error_rate:.2%})")
        
        return result
    
    def _run_warmup(self) -> None:
        """运行预热"""
        for i in range(self.config.num_warmup):
            self._execute_operation("write", i)
    
    def _run_benchmark(self) -> None:
        """运行基准测试"""
        self._latencies = []
        self._errors = 0
        self._operation_counts = {}
        
        with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
            futures = []
            
            for i in range(self.config.num_operations):
                op_type = random.choice(["write", "read", "search", "delete"])
                future = executor.submit(self._execute_operation, op_type, i)
                futures.append(future)
            
            for future in as_completed(futures):
                pass  # 等待完成
    
    def _execute_operation(self, op_type: str, index: int) -> None:
        """执行单个操作"""
        start = time.time()
        
        try:
            if op_type == "write":
                self._simulate_write(index)
            elif op_type == "read":
                self._simulate_read(index)
            elif op_type == "search":
                self._simulate_search(index)
            elif op_type == "delete":
                self._simulate_delete(index)
            
            latency = (time.time() - start) * 1000
            self._latencies.append(latency)
            
            self._operation_counts[op_type] = self._operation_counts.get(op_type, 0) + 1
            
        except Exception as e:
            self._errors += 1
    
    def _simulate_write(self, index: int) -> None:
        """模拟写入操作"""
        size = random.randint(self.config.min_memory_size, self.config.max_memory_size)
        data = ''.join(random.choices(string.ascii_letters, k=size))
        # 模拟延迟
        time.sleep(random.uniform(0.0001, 0.001))
    
    def _simulate_read(self, index: int) -> None:
        """模拟读取操作"""
        time.sleep(random.uniform(0.00005, 0.0005))
    
    def _simulate_search(self, index: int) -> None:
        """模拟搜索操作"""
        time.sleep(random.uniform(0.001, 0.005))
    
    def _simulate_delete(self, index: int) -> None:
        """模拟删除操作"""
        time.sleep(random.uniform(0.0001, 0.0005))
    
    def _generate_result(
        self,
        start_time: datetime,
        end_time: datetime,
        duration: float
    ) -> BenchmarkResult:
        """生成结果"""
        total_ops = len(self._latencies)
        ops_per_sec = total_ops / duration if duration > 0 else 0
        
        sorted_latencies = sorted(self._latencies)
        
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0
            idx = int(len(data) * p)
            return data[min(idx, len(data) - 1)]
        
        return BenchmarkResult(
            config=self.config,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            total_operations=total_ops,
            ops_per_second=ops_per_sec,
            avg_latency_ms=sum(self._latencies) / len(self._latencies) if self._latencies else 0,
            p50_latency_ms=percentile(sorted_latencies, 0.50),
            p90_latency_ms=percentile(sorted_latencies, 0.90),
            p99_latency_ms=percentile(sorted_latencies, 0.99),
            min_latency_ms=min(self._latencies) if self._latencies else 0,
            max_latency_ms=max(self._latencies) if self._latencies else 0,
            total_errors=self._errors,
            error_rate=self._errors / total_ops if total_ops > 0 else 0,
            operation_stats={
                "counts": self._operation_counts,
            }
        )
    
    def save_results(self, result: BenchmarkResult, output_path: str) -> None:
        """保存结果"""
        with open(output_path, 'w') as f:
            f.write(result.to_json())
        print(f"Results saved to {output_path}")
