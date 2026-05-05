"""
API Gateway 单元测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api_gateway.config import Settings


class TestAPIGatewayConfig:
    """测试 API Gateway 配置"""
    
    def test_default_settings(self):
        settings = Settings()
        assert settings.APP_NAME == "Unified Memory v5 Gateway"
        assert settings.PORT == 8000
    
    def test_custom_settings(self):
        settings = Settings(APP_NAME="Test", PORT=9000)
        assert settings.APP_NAME == "Test"
        assert settings.PORT == 9000
    
    def test_rate_limit_config(self):
        settings = Settings()
        assert settings.RATE_LIMIT_REQUESTS == 1000
        assert settings.RATE_LIMIT_WINDOW == 60


class TestRateLimiter:
    """测试限流器"""
    
    def test_token_bucket_init(self):
        from api_gateway.middleware.rate_limit import TokenBucketRateLimiter
        limiter = TokenBucketRateLimiter(requests_per_minute=100, burst_size=10)
        assert limiter.capacity == 10
    
    def test_token_consume(self):
        from api_gateway.middleware.rate_limit import TokenBucketRateLimiter
        limiter = TokenBucketRateLimiter(requests_per_minute=60, burst_size=5)
        assert limiter.try_consume("user1") is True
    
    def test_token_exhausted(self):
        from api_gateway.middleware.rate_limit import TokenBucketRateLimiter
        limiter = TokenBucketRateLimiter(requests_per_minute=60, burst_size=1)
        limiter.try_consume("user1")
        assert limiter.try_consume("user1") is False


class TestAuthentication:
    """测试认证"""
    
    def test_jwt_token(self):
        from api_gateway.middleware.auth import create_access_token
        token = create_access_token({"sub": "user123"})
        assert token is not None
        assert len(token) > 0


class TestErrorHandling:
    """测试错误处理"""
    
    def test_error_codes(self):
        from api_gateway.exceptions import ErrorCode, ValidationError, NotFoundError
        assert 1000 <= ErrorCode.INTERNAL_ERROR.value < 1100
        assert 1100 <= ValidationError.code < 1200
        assert 1200 <= NotFoundError.code < 1300
