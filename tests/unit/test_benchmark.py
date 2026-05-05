"""
Benchmark 单元测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from benchmark.benchmark import BenchmarkRunner, BenchmarkConfig


class TestBenchmarkConfig:
    def test_default_config(self):
        config = BenchmarkConfig()
        assert config.num_operations == 10000
        assert config.num_workers == 10
        assert config.num_warmup == 1000


class TestBenchmarkRunner:
    def test_run_small_benchmark(self):
        config = BenchmarkConfig(name="small_test", num_operations=50, num_warmup=5, num_workers=2)
        runner = BenchmarkRunner(config)
        result = runner.run()
        assert result.total_operations > 0
        assert result.ops_per_second > 0
    
    def test_result_serialization(self):
        config = BenchmarkConfig(num_operations=30, num_workers=2)
        runner = BenchmarkRunner(config)
        result = runner.run()
        json_str = result.to_json()
        assert "total_operations" in json_str
        assert "ops_per_second" in json_str
    
    def test_result_dict(self):
        config = BenchmarkConfig(num_operations=30, num_workers=2)
        runner = BenchmarkRunner(config)
        result = runner.run()
        data = result.to_dict()
        assert isinstance(data, dict)
        assert "config" in data
