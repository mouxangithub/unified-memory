"""
响应模型定义
"""

from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    """基础响应"""
    
    code: int = Field(default=0, description="业务状态码，0表示成功")
    message: str = Field(default="Success", description="响应消息")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")


class MemoryResponse(BaseResponse):
    """记忆响应"""
    
    data: Optional["MemoryData"] = Field(default=None, description="记忆数据")


class MemoryData(BaseModel):
    """记忆数据"""
    
    id: str = Field(..., description="记忆唯一ID")
    content: str = Field(..., description="记忆内容")
    namespace: str = Field(..., description="命名空间")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="元数据")
    tags: Optional[list[str]] = Field(default=None, description="标签")
    version: int = Field(..., description="当前版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(default=None, description="创建者")
    
    model_config = {"from_attributes": True}


class MemoryListResponse(BaseResponse):
    """记忆列表响应"""
    
    data: Optional["MemoryListData"] = Field(default=None, description="记忆列表数据")


class MemoryListData(BaseModel):
    """记忆列表数据"""
    
    items: list[MemoryData] = Field(default_factory=list, description="记忆列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")


class MemoryVersionResponse(BaseResponse):
    """记忆版本响应"""
    
    data: Optional["MemoryVersionData"] = Field(default=None, description="版本数据")


class MemoryVersionData(BaseModel):
    """记忆版本数据"""
    
    memory_id: str = Field(..., description="记忆ID")
    current_version: int = Field(..., description="当前版本")
    versions: list["VersionItem"] = Field(default_factory=list, description="版本列表")


class VersionItem(BaseModel):
    """版本项"""
    
    version: int = Field(..., description="版本号")
    content: str = Field(..., description="该版本的内容")
    created_at: datetime = Field(..., description="版本创建时间")
    created_by: Optional[str] = Field(default=None, description="操作者")


class NamespaceStatsResponse(BaseResponse):
    """命名空间统计响应"""
    
    data: Optional["NamespaceStatsData"] = Field(default=None, description="统计数据")


class NamespaceStatsData(BaseModel):
    """命名空间统计数据"""
    
    namespace: str = Field(..., description="命名空间")
    total_memories: int = Field(..., description="记忆总数")
    total_versions: int = Field(..., description="版本总数")
    avg_version_per_memory: float = Field(..., description="平均每条记忆的版本数")
    storage_size_bytes: int = Field(..., description="存储大小（字节）")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    top_tags: list["TagCount"] = Field(default_factory=list, description="热门标签")


class TagCount(BaseModel):
    """标签统计"""
    
    tag: str = Field(..., description="标签名")
    count: int = Field(..., description="出现次数")


class SearchResultResponse(BaseResponse):
    """搜索结果响应"""
    
    data: Optional["SearchResultData"] = Field(default=None, description="搜索结果")


class SearchResultData(BaseModel):
    """搜索结果数据"""
    
    query: str = Field(..., description="搜索查询")
    total: int = Field(default=0, description="匹配总数")
    results: list["SearchResultItem"] = Field(default_factory=list, description="结果列表")
    search_time_ms: float = Field(..., description="搜索耗时（毫秒）")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    namespace: str = Field(..., description="命名空间")
    score: float = Field(..., description="相似度分数")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="元数据")
    highlights: Optional[list[str]] = Field(default=None, description="高亮片段")


class ErrorResponse(BaseModel):
    """错误响应"""
    
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(default=None, description="详细错误信息")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")


# 更新正向引用
MemoryResponse.model_rebuild()
MemoryListResponse.model_rebuild()
MemoryVersionResponse.model_rebuild()
NamespaceStatsResponse.model_rebuild()
SearchResultResponse.model_rebuild()