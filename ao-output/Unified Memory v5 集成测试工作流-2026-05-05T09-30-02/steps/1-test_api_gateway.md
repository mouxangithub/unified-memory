> 🧪 **测试工程师-网关** | 步骤 1/1 | 136.5s

---

<think>
用户要求我对 Unified Memory v5 的 api_gateway 模块进行单元测试，涵盖五个主要方面：
1. 模块初始化和配置加载
2. API 路由注册与匹配
3. 请求/响应拦截器
4. 错误处理与异常传播
5. 超时与限流机制

我需要创建一套全面的单元测试，遵循测试最佳实践，包括：
- 使用 pytest 框架
- 包含 fixture 设置
- 使用 mock 模拟外部依赖
- 测试边界条件和错误场景
- 清晰的测试结构和注释

让我构建一个完整的测试套件：

```python
"""
Unified Memory v5 - api_gateway 模块单元测试

测试范围：
1. 模块初始化和配置加载
2. API 路由注册与匹配
3. 请求/响应拦截器
4. 错误处理与异常传播
5. 超时与限流机制
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from collections import defaultdict
import threading
from contextlib import asynccontextmanager

# ============================================================
# 1. 模块初始化和配置加载测试
# ============================================================

class TestAPIGatewayInitialization:
    """测试 API Gateway 模块初始化"""
    
    def test_gateway_initialization_with_valid_config(self, valid_gateway_config):
        """测试使用有效配置初始化网关"""
        pass
    
    def test_gateway_initialization_with_minimal_config(self):
        """测试使用最小配置初始化网关"""
        pass
    
    def test_gateway_initialization_with_invalid_config(self):
        """测试使用无效配置初始化网关 - 应抛出配置错误"""
        pass
    
    def test_gateway_initialization_with_missing_required_fields(self):
        """测试缺少必需字段时的初始化"""
        pass
    
    def test_gateway_initialization_with_invalid_port(self):
        """测试使用无效端口初始化"""
        pass
    
    def test_gateway_initialization_with_invalid_timeout(self):
        """测试使用无效超时值初始化"""
        pass
    
    def test_gateway_initialization_with_custom_middleware(self):
        """测试使用自定义中间件初始化"""
        pass
    
    def test_gateway_initialization_with_multiple_instances(self):
        """测试多个网关实例初始化"""
        pass
    
    def test_gateway_initialization_environment_override(self, monkeypatch):
        """测试环境变量覆盖配置"""
        pass
    
    def test_gateway_initialization_with_secrets_config(self):
        """测试密钥配置加载"""
        pass

class TestConfigurationLoading:
    """测试配置加载功能"""
    
    def test_load_config_from_yaml_file(self, yaml_config_file):
        """测试从 YAML 文件加载配置"""
        pass
    
    def test_load_config_from_json_file(self, json_config_file):
        """测试从 JSON 文件加载配置"""
        pass
    
    def test_load_config_from_dict(self):
        """测试从字典加载配置"""
        pass
    
    def test_config_validation_schema_check(self):
        """测试配置模式验证"""
        pass
    
    def test_config_with_env_variable_substitution(self, monkeypatch):
        """测试环境变量替换"""
        pass
    
    def test_config_reload_without_restart(self, running_gateway):
        """测试热重载配置"""
        pass
    
    def test_config_merge_with_defaults(self):
        """测试配置与默认值的合并"""
        pass
    
    def test_config_with_invalid_schema(self):
        """测试无效模式配置"""
        pass

# ============================================================
# 2. API 路由注册与匹配测试
# ============================================================

class TestRouteRegistration:
    """测试路由注册功能"""
    
    def test_register_simple_route(self, gateway):
        """测试注册简单路由"""
        pass
    
    def test_register_route_with_path_params(self, gateway):
        """测试注册带路径参数的路由"""
        pass
    
    def test_register_route_with_query_params(self, gateway):
        """测试注册带查询参数的路由"""
        pass
    
    def test_register_route_with_headers(self, gateway):
        """测试注册带请求头条件的路由"""
        pass
    
    def test_register_duplicate_route(self, gateway):
        """测试注册重复路由"""
        pass
    
    def test_register_route_with_methods(self, gateway):
        """测试注册路由支持多个 HTTP 方法"""
        pass
    
    def test_register_nested_routes(self, gateway):
        """测试注册嵌套路由"""
        pass
    
    def test_register_route_with_middleware(self, gateway):
        """测试注册带中间件的路由"""
        pass
    
    def test_register_route_priority_ordering(self, gateway):
        """测试路由优先级排序"""
        pass
    
    def test_register_route_with_wildcard(self, gateway):
        """测试注册通配符路由"""
        pass
    
    def test_unregister_route(self, gateway):
        """测试注销路由"""
        pass

class TestRouteMatching:
    """测试路由匹配功能"""
    
    def test_match_exact_path(self, gateway):
        """测试精确路径匹配"""
        pass
    
    def test_match_path_with_params(self, gateway):
        """测试带参数的路径匹配"""
        pass
    
    def test_match_path_with_multiple_params(self, gateway):
        """测试带多个参数的路径匹配"""
        pass
    
    def test_match_path_with_optional_params(self, gateway):
        """测试带可选参数的路径匹配"""
        pass
    
    def test_match_path_with_wildcard(self, gateway):
        """测试通配符路径匹配"""
        pass
    
    def test_match_path_priority_over_wildcard(self, gateway):
        """测试精确路径优先级高于通配符"""
        pass
    
    def test_no_match_returns_404(self, gateway):
        """测试无匹配返回 404"""
        pass
    
    def test_match_with_method_constraint(self, gateway):
        """测试带方法约束的匹配"""
        pass
    
    def test_match_with_header_constraint(self, gateway):
        """测试带请求头约束的匹配"""
        pass
    
    def test_match_with_query_constraint(self, gateway):
        """测试带查询参数约束的匹配"""
        pass
    
    def test_case_sensitive_path_matching(self, gateway):
        """测试路径大小写敏感性"""
        pass
    
    def test_trailing_slash_handling(self, gateway):
        """测试尾部斜杠处理"""
        pass

# ============================================================
# 3. 请求/响应拦截器测试
# ============================================================

class TestRequestInterceptors:
    """测试请求拦截器"""
    
    def test_single_request_interceptor(self, gateway):
        """测试单个请求拦截器"""
        pass
    
    def test_multiple_request_interceptors(self, gateway):
        """测试多个请求拦截器按顺序执行"""
        pass
    
    def test_request_interceptor_modifies_request(self, gateway):
        """测试请求拦截器修改请求"""
        pass
    
    def test_request_interceptor_adds_headers(self, gateway):
        """测试请求拦截器添加请求头"""
        pass
    
    def test_request_interceptor_short_circuit(self, gateway):
        """测试请求拦截器短路（提前响应）"""
        pass
    
    def test_request_interceptor_async(self, gateway):
        """测试异步请求拦截器"""
        pass
    
    def test_request_interceptor_error_handling(self, gateway):
        """测试请求拦截器错误处理"""
        pass
    
    def test_global_request_interceptor(self, gateway):
        """测试全局请求拦截器"""
        pass
    
    def test_route_specific_interceptor(self, gateway):
        """测试路由特定拦截器"""
        pass

class TestResponseInterceptors:
    """测试响应拦截器"""
    
    def test_single_response_interceptor(self, gateway):
        """测试单个响应拦截器"""
        pass
    
    def test_multiple_response_interceptors(self, gateway):
        """测试多个响应拦截器按顺序执行"""
        pass
    
    def test_response_interceptor_modifies_response(self, gateway):
        """测试响应拦截器修改响应"""
        pass
    
    def test_response_interceptor_adds_headers(self, gateway):
        """测试响应拦截器添加响应头"""
        pass
    
    def test_response_interceptor_error_handling(self, gateway):
        """测试响应拦截器错误处理"""
        pass
    
    def test_response_interceptor_on_error(self, gateway):
        """测试错误响应的拦截器"""
        pass
    
    def test_global_response_interceptor(self, gateway):
        """测试全局响应拦截器"""
        pass

# ============================================================
# 4. 错误处理与异常传播测试
# ============================================================

class TestErrorHandling:
    """测试错误处理"""
    
    def test_gateway_error_returns_json(self, gateway):
        """测试网关错误返回 JSON 格式"""
        pass
    
    def test_gateway_error_with_stack_trace_in_debug(self, gateway, monkeypatch):
        """测试调试模式下返回堆栈跟踪"""
        pass
    
    def test_custom_error_handler_registration(self, gateway):
        """测试自定义错误处理器注册"""
        pass
    
    def test_error_handler_for_specific_exception(self, gateway):
        """测试特定异常的错误处理器"""
        pass
    
    def test_error_handler_chain_fallback(self, gateway):
        """测试错误处理器链的回退机制"""
        pass
    
    def test_unhandled_exception_logging(self, gateway):
        """测试未处理异常的日志记录"""
        pass
    
    def test_error_response_includes_correlation_id(self, gateway):
        """测试错误响应包含关联 ID"""
        pass

class TestExceptionPropagation:
    """测试异常传播"""
    
    def test_exception_from_handler_propagates(self, gateway):
        """测试处理器异常向上传播"""
        pass
    
    def test_exception_from_interceptor_propagates(self, gateway):
        """测试拦截器异常向上传播"""
        pass
    
    def test_exception_preserves_original_trace(self, gateway):
        """测试异常保留原始堆栈跟踪"""
        pass
    
    def test_nested_exception_wrapping(self, gateway):
        """测试嵌套异常包装"""
        pass
    
    def test_async_exception_propagation(self, gateway):
        """测试异步异常传播"""
        pass
    
    def test_timeout_exception_propagation(self, gateway):
        """测试超时异常传播"""
        pass

# ============================================================
# 5. 超时与限流机制测试
# ============================================================

class TestTimeoutMechanism:
    """测试超时机制"""
    
    def test_request_timeout_configuration(self, gateway):
        """测试请求超时配置"""
        pass
    
    def test_request_timeout_triggered(self, gateway):
        """测试请求超时触发"""
        pass
    
    def test_request_timeout_does_not_affect_fast_requests(self, gateway):
        """测试快速请求不受超时影响"""
        pass
    
    def test_per_route_timeout_override(self, gateway):
        """测试路由级超时覆盖"""
        pass
    
    def test_read_timeout_configuration(self, gateway):
        """测试读取超时配置"""
        pass
    
    def test_write_timeout_configuration(self, gateway):
        """测试写入超时配置"""
        pass
    
    def test_timeout_cancellation_cleanup(self, gateway):
        """测试超时取消时的清理"""
        pass

class TestRateLimiting:
    """测试限流机制"""
    
    def test_rate_limit_per_ip(self, gateway):
        """测试基于 IP 的限流"""
        pass
    
    def test_rate_limit_per_api_key(self, gateway):
        """测试基于 API Key 的限流"""
        pass
    
    def test_rate_limit_exceeded_returns_429(self, gateway):
        """测试超过限流返回 429"""
        pass
    
    def test_rate_limit_with_burst(self, gateway):
        """测试带突发容量的限流"""
        pass
    
    def test_rate_limit_window_reset(self, gateway):
        """测试限流窗口重置"""
        pass
    
    def test_rate_limit_custom_key_extractor(self, gateway):
        """测试自定义限流键提取器"""
        pass
    
    def test_rate_limit_whitelist(self, gateway):
        """测试限流白名单"""
        pass
    
    def test_rate_limit_headers_in_response(self, gateway):
        """测试响应中的限流头信息"""
        pass
    
    def test_distributed_rate_limiting_consistency(self, gateway):
        """测试分布式限流一致性"""
        pass

class TestCircuitBreaker:
    """测试熔断器"""
    
    def test_circuit_breaker_opens_on_failures(self, gateway):
        """测试失败时熔断器打开"""
        pass
    
    def test_circuit_breaker_half_open_after_timeout(self, gateway):
        """测试超时后熔断器进入半开状态"""
        pass
    
    def test_circuit_breaker_closes_on_success(self, gateway):
        """测试成功后熔断器关闭"""
        pass
    
    def test_circuit_breaker_prevents_requests_when_open(self, gateway):
        """测试熔断器打开时阻止请求"""
        pass
    
    def test_circuit_breaker_failure_threshold_configurable(self, gateway):
        """测试熔断器失败阈值可配置"""
        pass

现在需要为每个测试类实现具体的测试逻辑，包括定义测试数据、设置测试环境、调用网关方法、验证结果和清理资源。
</think>

# Unified Memory v5 - api_gateway 模块单元测试

```python
"""
Unified Memory v5 - api_gateway 模块单元测试套件

测试范围：
1. 模块初始化和配置加载
2. API 路由注册与匹配
3. 请求/响应拦截器
4. 错误处理与异常传播
5. 超时与限流机制

运行方式：
    pytest tests/api_gateway/test_gateway.py -v
    pytest tests/api_gateway/test_gateway.py -v --cov=api_gateway
"""

import pytest
import asyncio
import time
import json
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call, PropertyMock
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from contextlib import asynccontextmanager
import hashlib
import re
import tempfile
import os
import yaml

# ============================================================
# 被测模块导入 (假设的模块结构)
# ============================================================

from api_gateway import (
    APIGateway,
    GatewayConfig,
    RouteConfig,
    Route,
    Request,
    Response,
    RouteMatch,
    Interceptor,
    RateLimitConfig,
    TimeoutConfig,
    CircuitBreakerConfig,
    GatewayError,
    RouteNotFoundError,
    RateLimitExceededError,
    TimeoutError,
    CircuitBreakerOpenError,
    MiddlewareChain,
    HealthCheck,
)


# ============================================================
# 共享 Fixtures
# ============================================================

@pytest.fixture
def valid_gateway_config() -> GatewayConfig:
    """提供有效的网关配置"""
    return GatewayConfig(
        host="127.0.0.1",
        port=8080,
        workers=4,
        timeout=TimeoutConfig(
            request_timeout=30.0,
            read_timeout=10.0,
            write_timeout=10.0,
            keepalive_timeout=60.0
        ),
        rate_limit=RateLimitConfig(
            enabled=True,
            requests_per_second=100,
            burst_size=200,
            strategy="sliding_window"
        ),
        circuit_breaker=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=5,
            success_threshold=2,
            timeout=30.0,
            half_open_max_calls=3
        ),
        logging_config={
            "level": "INFO",
            "format": "json",
            "output": "stdout"
        },
        enable_metrics=True,
        enable_tracing=True,
        debug=False
    )


@pytest.fixture
def minimal_gateway_config() -> GatewayConfig:
    """提供最小化网关配置"""
    return GatewayConfig(
        host="127.0.0.1",
        port=8080
    )


@pytest.fixture
def gateway(valid_gateway_config) -> APIGateway:
    """创建并返回网关实例"""
    gw = APIGateway(valid_gateway_config)
    yield gw
    # 清理
    try:
        gw.shutdown()
    except Exception:
        pass


@pytest.fixture
def running_gateway(valid_gateway_config) -> APIGateway:
    """创建并启动的网关实例"""
    gw = APIGateway(valid_gateway_config)
    gw.start()
    yield gw
    gw.shutdown()


@pytest.fixture
def mock_request() -> Request:
    """创建模拟请求"""
    return Request(
        method="GET",
        path="/api/v1/users/123",
        headers={
            "Content-Type": "application/json",
            "X-Request-ID": "test-request-001",
            "X-API-Key": "test-api-key"
        },
        query_params={"include": "profile,settings"},
        body=None,
        client_ip="192.168.1.100",
        timestamp=time.time()
    )


@pytest.fixture
def mock_response() -> Response:
    """创建模拟响应"""
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=json.dumps({"status": "success", "data": {"id": 123}}).encode()
    )


@pytest.fixture
def yaml_config_file(tmp_path) -> str:
    """创建临时 YAML 配置文件"""
    config_path = tmp_path / "gateway_config.yaml"
    config_content = {
        "gateway": {
            "host": "0.0.0.0",
            "port": 9000,
            "workers": 2,
            "timeout": {
                "request_timeout": 30,
                "read_timeout": 15,
                "write_timeout": 15
            },
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 50
            }
        }
    }
    config_path.write_text(yaml.dump(config_content))
    return str(config_path)


@pytest.fixture
def json_config_file(tmp_path) -> str:
    """创建临时 JSON 配置文件"""
    config_path = tmp_path / "gateway_config.json"
    config_content = {
        "host": "0.0.0.0",
        "port": 9001,
        "workers": 4,
        "timeout": {
            "request_timeout": 60,
            "read_timeout": 30
        }
    }
    config_path.write_text(json.dumps(config_content, indent=2))
    return str(config_path)


@pytest.fixture
def sample_handler() -> Callable:
    """创建示例处理器"""
    async def handler(request: Request) -> Response:
        return Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=json.dumps({"message": "handled"}).encode()
        )
    return handler


# ============================================================
# 辅助函数和工具
# ============================================================

def create_error_response(status_code: int, message: str, **kwargs) -> Response:
    """创建错误响应"""
    body = {
        "error": {
            "code": status_code,
            "message": message,
            **kwargs
        }
    }
    return Response(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        body=json.dumps(body).encode()
    )


def assert_response_structure(response: Response) -> None:
    """验证响应结构"""
    assert isinstance(response, Response)
    assert hasattr(response, 'status_code')
    assert hasattr(response, 'headers')
    assert hasattr(response, 'body')


def assert_error_response(response: Response, expected_status: int) -> None:
    """验证错误响应格式"""
    assert_response_structure(response)
    assert response.status_code == expected_status
    body = json.loads(response.body.decode())
    assert "error" in body
    assert "message" in body["error"]


# ============================================================
# 测试类实现
# ============================================================

# -------------------------------------------------------------------------
# 1. 模块初始化和配置加载测试
# -------------------------------------------------------------------------

class TestAPIGatewayInitialization:
    """API Gateway 模块初始化测试"""

    def test_gateway_initialization_with_valid_config(self, valid_gateway_config):
        """测试：使用有效配置初始化网关"""
        # Given: 有效的网关配置
        
        # When: 创建网关实例
        gateway = APIGateway(valid_gateway_config)
        
        # Then: 网关正确初始化
        assert gateway.config == valid_gateway_config
        assert gateway.is_initialized is True
        assert gateway.is_running is False
        assert len(gateway.routes) == 0
        assert len(gateway.interceptors) == 0

    def test_gateway_initialization_with_minimal_config(self, minimal_gateway_config):
        """测试：使用最小配置初始化网关"""
        # Given: 最小化配置（仅必需字段）
        
        # When: 创建网关实例
        gateway = APIGateway(minimal_gateway_config)
        
        # Then: 使用默认配置填充其他字段
        assert gateway.config.host == "127.0.0.1"
        assert gateway.config.port == 8080
        assert gateway.config.timeout.request_timeout == 30.0  # 默认值
        assert gateway.config.rate_limit.enabled is True  # 默认值

    def test_gateway_initialization_with_invalid_port_raises_error(self):
        """测试：使用无效端口初始化应抛出错误"""
        # Given: 无效端口配置
        config = GatewayConfig(host="127.0.0.1", port=-1)
        
        # When/Then: 应抛出配置验证错误
        with pytest.raises(GatewayError) as exc_info:
            APIGateway(config)
        
        assert "port" in str(exc_info.value).lower()
        assert "invalid" in str(exc_info.value).lower()

    def test_gateway_initialization_with_port_out_of_range_raises_error(self):
        """测试：端口超出范围应抛出错误"""
        # Given: 超出范围的端口
        config = GatewayConfig(host="127.0.0.1", port=70000)
        
        # When/Then: 应抛出配置验证错误
        with pytest.raises(GatewayError) as exc_info:
            APIGateway(config)
        
        assert "port" in str(exc_info.value).lower()

    def test_gateway_initialization_with_invalid_timeout_raises_error(self):
        """测试：无效超时值应抛出错误"""
        # Given: 负超时值配置
        config = GatewayConfig(
            host="127.0.0.1",
            port=8080,
            timeout=TimeoutConfig(request_timeout=-5.0)
        )
        
        # When/Then: 应抛出配置验证错误
        with pytest.raises(GatewayError) as exc_info:
            APIGateway(config)
        
        assert "timeout" in str(exc_info.value).lower()

    def test_gateway_initialization_with_zero_workers_uses_default(self):
        """测试：零工作进程数应使用默认值"""
        # Given: 零工作进程配置
        config = GatewayConfig(host="127.0.0.1", port=8080, workers=0)
        
        # When: 创建网关
        gateway = APIGateway(config)
        
        # Then: 使用默认工作进程数
        assert gateway.config.workers == 1  # 最小值

    def test_gateway_initialization_with_excessive_workers_raises_error(self):
        """测试：过多工作进程应抛出错误"""
        # Given: 超出限制的工作进程数
        config = GatewayConfig(host="127.0.0.1", port=8080, workers=1000)
        
        # When/Then: 应抛出配置验证错误
        with pytest.raises(GatewayError):
            APIGateway(config)

    def test_gateway_initialization_with_custom_middleware(self, valid_gateway_config):
        """测试：使用自定义中间件初始化"""
        # Given: 包含自定义中间件的配置
        async def custom_middleware(request, next_handler):
            request.headers["X-Custom"] = "added"
            return await next_handler(request)
        
        valid_gateway_config.middleware = [custom_middleware]
        
        # When: 创建网关
        gateway = APIGateway(valid_gateway_config)
        
        # Then: 中间件被正确注册
        assert len(gateway.middleware_chain) == 1

    def test_gateway_initialization_with_multiple_instances(self, valid_gateway_config):
        """测试：多个网关实例独立运行"""
        # Given: 同一配置的两个实例
        config1 = GatewayConfig(host="127.0.0.1", port=8081)
        config2 = GatewayConfig(host="127.0.0.1", port=8082)
        
        # When: 创建两个网关
        gateway1 = APIGateway(config1)
        gateway2 = APIGateway(config2)
        
        # Then: 实例相互独立
        assert gateway1 is not gateway2
        assert gateway1.config.port != gateway2.config.port

    def test_gateway_initialization_environment_override(self, monkeypatch, valid_gateway_config):
        """测试：环境变量覆盖配置"""
        # Given: 环境变量设置
        monkeypatch.setenv("GATEWAY_PORT", "9999")
        monkeypatch.setenv("GATEWAY_WORKERS", "8")
        
        # When: 创建网关
        gateway = APIGateway(valid_gateway_config)
        
        # Then: 环境变量覆盖配置
        assert gateway.config.port == 9999
        assert gateway.config.workers == 8

    def test_gateway_initialization_with_secrets_config(self, valid_gateway_config):
        """测试：密钥配置正确加载（不暴露）"""
        # Given: 包含敏感信息的配置
        valid_gateway_config.secrets = {
            "api_key": "secret-key-12345",
            "db_password": "super-secret"
        }
        
        # When: 创建网关
        gateway = APIGateway(valid_gateway_config)
        
        # Then: 密钥被存储但不暴露
        assert "api_key" in gateway.secrets
        assert gateway.secrets["api_key"] == "secret-key-12345"
        # 验证秘密不会出现在日志中（通过检查序列化）
        serialized = json.dumps(gateway.config.to_dict())
        assert "secret" not in serialized.lower()
        assert "12345" not in serialized


class TestConfigurationLoading:
    """配置加载功能测试"""

    def test_load_config_from_yaml_file(self, yaml_config_file):
        """测试：从 YAML 文件加载配置"""
        # When: 从文件加载配置
        config = GatewayConfig.from_file(yaml_config_file)
        
        # Then: 配置正确解析
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.workers == 2
        assert config.timeout.request_timeout == 30.0

    def test_load_config_from_json_file(self, json_config_file):
        """测试：从 JSON 文件加载配置"""
        # When: 从文件加载配置
        config = GatewayConfig.from_file(json_config_file)
        
        # Then: 配置正确解析
        assert config.host == "0.0.0.0"
        assert config.port == 9001
        assert config.workers == 4
        assert config.timeout.request_timeout == 60.0

    def test_load_config_from_dict(self):
        """测试：从字典加载配置"""
        # Given: 配置字典
        config_dict = {
            "host": "localhost",
            "port": 8888,
            "workers": 2,
            "timeout": {
                "request_timeout": 45,
                "read_timeout": 20
            },
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 200
            }
        }
        
        # When: 从字典加载
        config = GatewayConfig.from_dict(config_dict)
        
        # Then: 配置正确解析
        assert config.host == "localhost"
        assert config.port == 8888
        assert config.timeout.request_timeout == 45
        assert config.rate_limit.requests_per_second == 200

    def test_config_validation_schema_check(self):
        """测试：配置模式验证"""
        # Given: 无效配置（缺少必需字段）
        config_dict = {
            "host": "localhost"
            # 缺少 port
        }
        
        # When/Then: 应抛出验证错误
        with pytest.raises(GatewayError) as exc_info:
            GatewayConfig.from_dict(config_dict)
        
        assert "validation" in str(exc_info.value).lower()

    def test_config_with_env_variable_substitution(self, monkeypatch):
        """测试：环境变量替换"""
        # Given: 包含环境变量引用的配置
        monkeypatch.setenv("GATEWAY_PORT", "7777")
        
        config_dict = {
            "host": "localhost",
            "port": {"env": "GATEWAY_PORT"},
            "workers": 2
        }
        
        # When: 加载配置
        config = GatewayConfig.from_dict(config_dict, resolve_env=True)
        
        # Then: 环境变量被解析
        assert config.port == 7777

    def test_config_merge_with_defaults(self):
        """测试：配置与默认值合并"""
        # Given: 部分配置
        config_dict = {
            "host": "custom.host",
            "port": 1234
        }
        
        # When: 加载配置
        config = GatewayConfig.from_dict(config_dict)
        
        # Then: 未提供的字段使用默认值
        assert config.host == "custom.host"
        assert config.port == 1234
        assert config.timeout is not None  # 默认对象
        assert config.rate_limit.enabled is True  # 默认值

    def test_config_to_dict_serialization(self, valid_gateway_config):
        """测试：配置序列化"""
        # When: 序列化为字典
        config_dict = valid_gateway_config.to_dict()
        
        # Then: 正确序列化
        assert isinstance(config_dict, dict)
        assert config_dict["host"] == valid_gateway_config.host
        assert config_dict["port"] == valid_gateway_config.port
        assert "timeout" in config_dict
        assert "rate_limit" in config_dict

    def test_config_equality(self, valid_gateway_config):
        """测试：配置相等性比较"""
        # Given: 两个相同配置
        config1 = GatewayConfig.from_dict(valid_gateway_config.to_dict())
        config2 = GatewayConfig.from_dict(valid_gateway_config.to_dict())
        
        # Then: 配置相等
        assert config1 == config2

    def test_config_copy_independence(self, valid_gateway_config):
        """测试：配置副本独立性"""
        # Given: 配置副本
        config_copy = valid_gateway_config.copy()
        
        # When: 修改副本
        config_copy.port = 9999
        
        # Then: 原配置不受影响
        assert valid_gateway_config.port == 8080


# -------------------------------------------------------------------------
# 2. API 路由注册与匹配测试
# -------------------------------------------------------------------------

class TestRouteRegistration:
    """路由注册功能测试"""

    def test_register_simple_route(self, gateway, sample_handler):
        """测试：注册简单路由"""
        # Given: 网关和处理器
        
        # When: 注册路由
        route = gateway.register_route(
            path="/api/users",
            methods=["GET"],
            handler=sample_handler
        )
        
        # Then: 路由正确注册
        assert route.path == "/api/users"
        assert "GET" in route.methods
        assert len(gateway.routes) == 1
        assert route in gateway.routes

    def test_register_route_with_path_params(self, gateway, sample_handler):
        """测试：注册带路径参数的路由"""
        # Given: 包含路径参数的路由
        
        # When: 注册
        route = gateway.register_route(
            path="/api/users/{user_id}/posts/{post_id}",
            methods=["GET", "DELETE"],
            handler=sample_handler
        )
        
        # Then: 路径参数被解析
        assert len(route.path_params) == 2
        assert "user_id" in route.path_params
        assert "post_id" in route.path_params

    def test_register_route_with_query_params(self, gateway, sample_handler):
        """测试：注册带查询参数约束的路由"""
        # Given: 查询参数约束
        constraint = lambda req: req.query_params.get("format") == "json"
        
        # When: 注册带约束的路由
        route = gateway.register_route(
            path="/api/data",
            methods=["GET"],
            handler=sample_handler,
            constraints={"query": {"format": "json"}}
        )
        
        # Then: 约束被保存
        assert route.constraints is not None
        assert "format" in route.constraints.get("query", {})

    def test_register_route_with_headers(self, gateway, sample_handler):
        """测试：注册带请求头约束的路由"""
        # When: 注册带请求头的路由
        route = gateway.register_route(
            path="/api/premium",
            methods=["GET"],
            handler=sample_handler,
            constraints={"headers": {"X-API-Key": r".+"}}
        )
        
        # Then: 头部约束被保存
        assert "X-API-Key" in route.constraints["headers"]

    def test_register_duplicate_route_raises_error(self, gateway, sample_handler):
        """测试：注册重复路由应抛出错误"""
        # Given: 已注册的路由
        gateway.register_route(
            path="/api/users",
            methods=["GET"],
            handler=sample_handler
        )
        
        # When/Then: 再次注册应抛出错误
        with pytest.raises(GatewayError) as exc_info:
            gateway.register_route(
                path="/api/users",
                methods=["GET"],
                handler=sample_handler
            )
        
        assert "duplicate" in str(exc_info.value).lower() or "already" in str(exc_info.value).lower()

    def test_register_route_with_multiple_methods(self, gateway, sample_handler):
        """测试：路由支持多个 HTTP 方法"""
        # When: 注册多方法路由
        route = gateway.register_route(
            path="/api/resource",
            methods=["GET", "POST", "PUT", "DELETE"],
            handler=sample_handler
        )
        
        # Then: 所有方法被注册
        assert set(route.methods) == {"GET", "POST", "PUT", "DELETE"}

    def test_register_nested_routes(self, gateway, sample_handler):
        """测试：注册嵌套路由"""
        # When: 注册嵌套路由
        parent = gateway.register_route(
            path="/api/v1",
            methods=["GET"],
            handler=sample_handler
        )
        child = gateway.register_route(
            path="/api/v1/users",
            methods=["GET"],
            handler=sample_handler
        )
        
        # Then: 路由独立存在
        assert len(gateway.routes) == 2
        assert parent.path != child.path

    def test_register_route_with_middleware(self, gateway, sample_handler):
        """测试：注册带中间件的路由"""
        # Given: 路由级中间件
        async def route_middleware(request, next_handler):
            request.headers["X-Route-Middleware"] = "applied"
            return await next_handler(request)
        
        # When: 注册带中间件的路由
        route = gateway.register_route(
            path="/api/auth",
            methods=["POST"],
            handler=sample_handler,
            middleware=[route_middleware]
        )
        
        # Then: 中间件被关联到路由
        assert len(route.middleware) == 1
        assert route.middleware[0] == route_middleware

    def test_register_route_priority_ordering(self, gateway, sample_handler):
        """测试：路由按优先级排序"""
        # When: 注册多个路由（无显式优先级）
        route1 = gateway.register_route(
            path="/api/users",
            methods=["GET"],
            handler=sample_handler,
            priority=10
        )
        route2 = gateway.register_route(
            path="/api/{resource}",
            methods=["GET"],
            handler=sample_handler,
            priority=5
        )
        route3 = gateway.register_route(
            path="/api/*",
            methods=["GET"],
            handler=sample_handler,
            priority=1
        )
        
        # Then: 路由按优先级降序排列
        assert gateway.routes[0] == route1  # 最高优先级
        assert gateway.routes[1] == route2
        assert gateway.routes[2] == route3  # 最低优先级

    def test_unregister_route(self, gateway, sample_handler):
        """测试：注销路由"""
        # Given: 已注册的路由
        route = gateway.register_route(
            path="/api/temp",
            methods=["GET"],
            handler=sample_handler
        )
        assert len(gateway.routes) == 1
        
        # When: 注销路由
        result = gateway.unregister_route("/api/temp")
        
        # Then: 路由被移除
        assert result is True
        assert len(gateway.routes) == 0

    def test_unregister_nonexistent_route(self, gateway):
        """测试：注销不存在的路由返回 False"""
        # When/Then: 注销不存在的路由
        result = gateway.unregister_route("/nonexistent")
        
        assert result is False

    def test_register_route_with_timeout_override(self, gateway, sample_handler):
        """测试：路由特定超时覆盖"""
        # When: 注册带超时覆盖的路由
        route = gateway.register_route(
            path="/api/slow",
            methods=["GET"],
            handler=sample_handler,
            timeout=5.0  # 覆盖默认的 30 秒
        )
        
        # Then: 超时被设置
        assert route.timeout == 5.0


class TestRouteMatching:
    """路由匹配功能测试"""

    @pytest.fixture
    def gateway_with_routes(self, gateway, sample_handler):
        """创建带多个路由的网关"""
        async def users_handler(request):
            return Response(status_code=200, body=b'{"resource": "users"}')
        
        async def user_detail_handler(request):
            return Response(status_code=200, body=b'{"resource": "user_detail"}')
        
        async def posts_handler(request):
            return Response(status_code=200, body=b'{"resource": "posts"}')
        
        # 注册多个路由
        gateway.register_route("/api/users", ["GET"], users_handler)
        gateway.register_route("/api/users/{user_id}", ["GET"], user_detail_handler)
        gateway.register_route("/api/users/{user_id}/posts", ["GET"], posts_handler)
        gateway.register_route("/api/posts/{post_id}", ["GET"], posts_handler)
        
        return gateway

    def test_match_exact_path(self, gateway_with_routes, mock_request):
        """测试：精确路径匹配"""
        # Given: 精确路径请求
        mock_request.path = "/api/users"
        
        # When: 匹配路由
        match = gateway_with_routes.match_route(mock_request)
        
        # Then: 正确匹配
        assert match is not None
        assert match.route.path == "/api/users"
        assert match.params == {}

    def test_match_path_with_single_param(self, gateway_with_routes, mock_request):
        """测试：