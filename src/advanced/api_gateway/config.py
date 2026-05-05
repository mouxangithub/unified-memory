"""
配置管理模块
支持环境变量配置和环境分离
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Unified Memory v5 Gateway"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    API_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # JWT 配置
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # API Key 配置
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: list[str] = Field(default_factory=lambda: ["test-api-key-1", "test-api-key-2"])
    
    # 限流配置
    RATE_LIMIT_REQUESTS: int = 1000  # 每分钟请求数
    RATE_LIMIT_WINDOW: int = 60  # 时间窗口（秒）
    RATE_LIMIT_BUCKET_SIZE: int = 1000  # 令牌桶容量
    
    # 存储配置（可扩展为数据库连接）
    STORAGE_BACKEND: str = "memory"  # memory, redis, postgres
    STORAGE_TTL_DAYS: int = 90
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    LOG_FILE: Optional[str] = None
    
    # OpenAPI 配置
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class SettingsFactory:
    """配置工厂"""
    
    _settings: Optional[Settings] = None
    
    @classmethod
    def get_settings(cls) -> Settings:
        if cls._settings is None:
            env = os.getenv("ENV", "development")
            if env == "production":
                cls._settings = ProductionSettings()
            elif env == "development":
                cls._settings = DevelopmentSettings()
            else:
                cls._settings = Settings()
        return cls._settings
    
    @classmethod
    def reset(cls):
        """重置配置（用于测试）"""
        cls._settings = None


def get_settings() -> Settings:
    """获取配置的单例"""
    return SettingsFactory.get_settings()


# 全局配置实例
settings = get_settings()