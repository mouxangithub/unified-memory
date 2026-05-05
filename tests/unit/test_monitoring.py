"""
Monitoring 单元测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from monitoring.metrics import Counter, Gauge, Histogram, MetricsCollector
from monitoring.health_check import HealthMonitor, HealthStatus


class TestCounter:
    def test_increment(self):
        counter = Counter("test_counter", "A test counter")
        counter.inc()
        assert counter.get() == 1
        counter.inc(5)
        assert counter.get() == 6


class TestGauge:
    def test_set(self):
        gauge = Gauge("test_gauge", "A test gauge")
        gauge.set(100)
        assert gauge.get() == 100
    
    def test_inc_dec(self):
        gauge = Gauge("test_gauge")
        gauge.set(10)
        gauge.inc(5)
        assert gauge.get() == 15
        gauge.dec(3)
        assert gauge.get() == 12


class TestMetricsCollector:
    def test_register(self):
        collector = MetricsCollector()
        counter = collector.counter("test_counter", "A test counter")
        assert counter is not None
        assert "test_counter" in collector._metrics
    
    def test_render_prometheus(self):
        collector = MetricsCollector()
        counter = collector.counter("test_counter", "A test counter")
        counter.inc()
        output = collector.render_prometheus()
        assert "test_counter" in output


class TestHealthMonitor:
    def test_register_check(self):
        monitor = HealthMonitor()
        monitor.register("test_component", lambda: True)
        assert "test_component" in monitor._checks
    
    def test_all_healthy(self):
        monitor = HealthMonitor()
        monitor.register("comp1", lambda: True)
        monitor.register("comp2", lambda: True)
        assert monitor.get_overall_status() == HealthStatus.HEALTHY
    
    def test_degraded(self):
        monitor = HealthMonitor()
        monitor.register("comp1", lambda: True)
        monitor.register("comp2", lambda: False)
        assert monitor.get_overall_status() == HealthStatus.DEGRADED
    
    def test_unhealthy(self):
        monitor = HealthMonitor()
        monitor.register("comp1", lambda: 1/0)
        assert monitor.get_overall_status() == HealthStatus.UNHEALTHY
