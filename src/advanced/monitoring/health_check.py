"""
健康检查模块
"""
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    timestamp: float = 0


class HealthCheck:
    """健康检查"""
    
    def __init__(self, name: str, check_fn: Callable[[], bool], timeout: float = 5.0):
        self.name = name
        self.check_fn = check_fn
        self.timeout = timeout
        self._last_result: Optional[HealthCheckResult] = None
        self._lock = threading.Lock()
    
    def run(self) -> HealthCheckResult:
        """执行健康检查"""
        start = time.time()
        try:
            result = self.check_fn()
            latency = (time.time() - start) * 1000
            
            with self._lock:
                self._last_result = HealthCheckResult(
                    component=self.name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                    message="OK" if result else "Check failed",
                    latency_ms=latency,
                    timestamp=time.time()
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            with self._lock:
                self._last_result = HealthCheckResult(
                    component=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    latency_ms=latency,
                    timestamp=time.time()
                )
        
        return self._last_result
    
    def get_last_result(self) -> Optional[HealthCheckResult]:
        return self._last_result


class HealthMonitor:
    """健康监控"""
    
    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, check_fn: Callable[[], bool], timeout: float = 5.0) -> None:
        """注册健康检查"""
        with self._lock:
            self._checks[name] = HealthCheck(name, check_fn, timeout)
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """执行所有健康检查"""
        results = {}
        for name, check in self._checks.items():
            results[name] = check.run()
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """获取整体状态"""
        results = self.check_all()
        
        if all(r.status == HealthStatus.HEALTHY for r in results.values()):
            return HealthStatus.HEALTHY
        
        if any(r.status == HealthStatus.UNHEALTHY for r in results.values()):
            return HealthStatus.UNHEALTHY
        
        return HealthStatus.DEGRADED
