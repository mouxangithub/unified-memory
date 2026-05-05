"""
请求模型定义
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class CreateMemoryRequest(BaseModel):
    """创建记忆请求"""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="记忆内容",
        examples=["This is a memory about project planning"]
    )
    
    namespace: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="命名空间，用于组织和隔离记忆",
        examples=["default", "project-alpha", "user_123"]
    )
    
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="记忆元数据",
        examples=[{"type": "note", "tags": ["important"]}]
    )
    
    tags: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="记忆标签",
        examples=[["work", "priority"]]
    )
    
    embedding_model: Optional[str] = Field(
        default=None,
        description="向量嵌入模型",
        examples=["text-embedding-3-small"]
    )
    
    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        if v.startswith("-") or v.startswith("_"):
            raise ValueError("Namespace cannot start with - or _")
        return v.lower()


class UpdateMemoryRequest(BaseModel):
    """更新记忆请求"""
    
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100000,
        description="记忆内容"
    )
    
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="记忆元数据"
    )
    
    tags: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="记忆标签"
    )
    
    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


class SearchMemoryRequest(BaseModel):
    """搜索记忆请求"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="搜索查询语句"
    )
    
    namespace: Optional[str] = Field(
        default=None,
        max_length=128,
        description="限定命名空间"
    )
    
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="返回结果数量限制"
    )
    
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="是否返回元数据"
    )
    
    rerank: bool = Field(
        default=False,
        description="是否启用重排序"
    )