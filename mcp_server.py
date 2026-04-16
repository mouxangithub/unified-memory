#!/usr/bin/env python3
"""
Unified Memory MCP Server
基于 AI Engineering Hub 最佳实践的标准化 MCP 服务器实现

参考: https://github.com/patchy631/ai-engineering-hub
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.api.memory_api import MemoryAPI
    from src.search.hybrid_search import HybridSearch
    from src.storage.memory_store import MemoryStore
    HAS_MEMORY_MODULES = True
except ImportError as e:
    print(f"警告: 无法导入内存模块: {e}")
    HAS_MEMORY_MODULES = False

# 创建 FastMCP 实例
mcp = FastMCP("unified_memory")

# 输入模型定义
class MemorySearchInput(BaseModel):
    """内存搜索输入参数"""
    query: str = Field(description="搜索查询内容")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="相似度阈值")
    search_type: str = Field(default="hybrid", description="搜索类型: hybrid, bm25, vector")

class MemoryStoreInput(BaseModel):
    """内存存储输入参数"""
    content: str = Field(description="要存储的内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="可选的元数据")
    category: Optional[str] = Field(default=None, description="内容分类")

class MemoryHealthInput(BaseModel):
    """内存健康检查输入参数"""
    check_type: str = Field(default="basic", description="检查类型: basic, full, storage")

# 初始化内存系统
def init_memory_system():
    """初始化内存系统"""
    if not HAS_MEMORY_MODULES:
        return None
    
    try:
        # 这里应该根据实际配置初始化
        storage_path = os.getenv("MEMORY_STORAGE_PATH", str(project_root / "memory" / "data"))
        memory_store = MemoryStore(storage_path=storage_path)
        hybrid_search = HybridSearch(memory_store)
        memory_api = MemoryAPI(memory_store, hybrid_search)
        return memory_api
    except Exception as e:
        print(f"初始化内存系统失败: {e}")
        return None

# 全局内存系统实例
memory_system = init_memory_system()

@mcp.tool()
async def memory_search(
    query: str, 
    limit: int = 10, 
    threshold: float = 0.5,
    search_type: str = "hybrid"
) -> str:
    """在统一记忆系统中搜索相关内容
    
    使用混合搜索（BM25 + 向量 + RRF）在记忆系统中查找相关内容。
    
    Args:
        query: 搜索查询内容
        limit: 返回结果数量 (默认: 10)
        threshold: 相似度阈值 (默认: 0.5)
        search_type: 搜索类型: hybrid, bm25, vector (默认: hybrid)
    
    Returns:
        格式化后的搜索结果，包含相关性和来源信息
    """
    if not memory_system:
        return "错误: 内存系统未初始化"
    
    try:
        # 调用内存系统搜索
        results = await memory_system.search(
            query=query,
            limit=limit,
            threshold=threshold,
            search_type=search_type
        )
        
        # 格式化结果
        if not results:
            return "未找到相关结果"
        
        output = [f"## 搜索结果 ({len(results)} 条)"]
        for i, result in enumerate(results, 1):
            output.append(f"\n### {i}. {result.get('title', '无标题')}")
            output.append(f"**内容**: {result.get('content', '')[:200]}...")
            output.append(f"**相关性**: {result.get('score', 0):.3f}")
            if 'metadata' in result:
                output.append(f"**元数据**: {result['metadata']}")
            if 'source' in result:
                output.append(f"**来源**: {result['source']}")
        
        return "\n".join(output)
    except Exception as e:
        return f"搜索失败: {str(e)}"

@mcp.tool()
async def memory_store(
    content: str, 
    metadata: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None
) -> str:
    """存储内容到统一记忆系统
    
    将内容存储到记忆系统中，支持原子事务和 WAL 协议。
    
    Args:
        content: 要存储的内容
        metadata: 可选的元数据（JSON 格式）
        category: 内容分类
    
    Returns:
        存储结果的确认信息，包括存储ID和状态
    """
    if not memory_system:
        return "错误: 内存系统未初始化"
    
    try:
        # 准备存储数据
        store_data = {
            "content": content,
            "metadata": metadata or {},
            "category": category
        }
        
        # 调用内存系统存储
        result = await memory_system.store(store_data)
        
        if result.get("success"):
            memory_id = result.get("memory_id", "未知")
            return f"✅ 存储成功\n**ID**: {memory_id}\n**时间**: {result.get('timestamp', '未知')}"
        else:
            return f"❌ 存储失败: {result.get('error', '未知错误')}"
    except Exception as e:
        return f"存储失败: {str(e)}"

@mcp.tool()
async def memory_health(
    check_type: str = "basic"
) -> str:
    """检查统一记忆系统的健康状态
    
    检查记忆系统的存储、搜索和整体健康状况。
    
    Args:
        check_type: 检查类型: basic, full, storage
    
    Returns:
        健康状态报告，包含各项指标和问题诊断
    """
    if not memory_system:
        return "错误: 内存系统未初始化"
    
    try:
        # 调用健康检查
        health_report = await memory_system.health_check(check_type)
        
        output = ["## 记忆系统健康检查报告"]
        
        # 基本状态
        status = health_report.get("status", "unknown")
        output.append(f"**状态**: {'✅ 健康' if status == 'healthy' else '⚠️ 警告' if status == 'warning' else '❌ 异常'}")
        
        # 存储状态
        storage = health_report.get("storage", {})
        output.append(f"\n### 存储状态")
        output.append(f"- 总条目数: {storage.get('total_items', 0)}")
        output.append(f"- 存储大小: {storage.get('size_mb', 0):.2f} MB")
        output.append(f"- 可用空间: {storage.get('free_space_mb', 0):.2f} MB")
        
        # 搜索状态
        search = health_report.get("search", {})
        output.append(f"\n### 搜索状态")
        output.append(f"- 索引数量: {search.get('index_count', 0)}")
        output.append(f"- 平均查询时间: {search.get('avg_query_time_ms', 0):.2f} ms")
        output.append(f"- 缓存命中率: {search.get('cache_hit_rate', 0):.2%}")
        
        # 性能指标
        performance = health_report.get("performance", {})
        output.append(f"\n### 性能指标")
        output.append(f"- 混合搜索速度: {performance.get('hybrid_search_speed', 0):.1f}x")
        output.append(f"- 存储压缩率: {performance.get('storage_reduction', 0):.1%}")
        
        # 问题诊断
        issues = health_report.get("issues", [])
        if issues:
            output.append(f"\n### 发现的问题")
            for issue in issues:
                output.append(f"- {issue}")
        
        return "\n".join(output)
    except Exception as e:
        return f"健康检查失败: {str(e)}"

@mcp.tool()
async def memory_stats() -> str:
    """获取统一记忆系统的统计信息
    
    返回记忆系统的使用统计和性能指标。
    
    Returns:
        统计信息报告，包含使用情况和性能数据
    """
    if not memory_system:
        return "错误: 内存系统未初始化"
    
    try:
        # 调用统计接口
        stats = await memory_system.get_stats()
        
        output = ["## 记忆系统统计信息"]
        
        # 使用统计
        usage = stats.get("usage", {})
        output.append(f"\n### 使用统计")
        output.append(f"- 总搜索次数: {usage.get('total_searches', 0)}")
        output.append(f"- 总存储次数: {usage.get('total_stores', 0)}")
        output.append(f"- 活跃用户数: {usage.get('active_users', 0)}")
        output.append(f"- 日均使用量: {usage.get('daily_usage', 0)}")
        
        # 性能统计
        performance = stats.get("performance", {})
        output.append(f"\n### 性能统计")
        output.append(f"- 平均搜索时间: {performance.get('avg_search_time_ms', 0):.2f} ms")
        output.append(f"- 平均存储时间: {performance.get('avg_store_time_ms', 0):.2f} ms")
        output.append(f"- 缓存命中率: {performance.get('cache_hit_rate', 0):.2%}")
        output.append(f"- 错误率: {performance.get('error_rate', 0):.2%}")
        
        # 存储统计
        storage = stats.get("storage", {})
        output.append(f"\n### 存储统计")
        output.append(f"- 总记忆条目: {storage.get('total_memories', 0)}")
        output.append(f"- 总存储大小: {storage.get('total_size_mb', 0):.2f} MB")
        output.append(f"- 去重节省: {storage.get('deduplication_savings_mb', 0):.2f} MB")
        output.append(f"- 压缩比率: {storage.get('compression_ratio', 0):.1%}")
        
        # 热门搜索
        top_searches = stats.get("top_searches", [])
        if top_searches:
            output.append(f"\n### 热门搜索")
            for i, search in enumerate(top_searches[:5], 1):
                output.append(f"{i}. {search.get('query', '未知')} ({search.get('count', 0)} 次)")
        
        return "\n".join(output)
    except Exception as e:
        return f"获取统计信息失败: {str(e)}"

@mcp.tool()
async def memory_clear(
    confirm: bool = False,
    older_than_days: Optional[int] = None
) -> str:
    """清理统一记忆系统中的数据
    
    谨慎使用！清理指定条件的数据。
    
    Args:
        confirm: 确认执行清理操作（必须为 True）
        older_than_days: 清理指定天数前的数据（可选）
    
    Returns:
        清理结果报告
    """
    if not memory_system:
        return "错误: 内存系统未初始化"
    
    if not confirm:
        return "⚠️ 请确认执行清理操作：设置 confirm=True"
    
    try:
        # 调用清理接口
        result = await memory_system.clear_data(older_than_days=older_than_days)
        
        output = ["## 记忆系统清理报告"]
        
        if result.get("success"):
            cleared = result.get("cleared_items", 0)
            freed_space = result.get("freed_space_mb", 0)
            
            output.append(f"✅ 清理完成")
            output.append(f"- 清理条目数: {cleared}")
            output.append(f"- 释放空间: {freed_space:.2f} MB")
            
            if older_than_days:
                output.append(f"- 清理条件: {older_than_days} 天前")
        else:
            output.append(f"❌ 清理失败")
            output.append(f"- 错误: {result.get('error', '未知错误')}")
        
        return "\n".join(output)
    except Exception as e:
        return f"清理失败: {str(e)}"

def main():
    """主函数：启动 MCP 服务器"""
    print("🚀 启动 Unified Memory MCP 服务器")
    print(f"版本: unified-memory v5.2.4")
    print(f"工具数量: 5")
    print(f"传输协议: stdio")
    print("-" * 50)
    
    if not HAS_MEMORY_MODULES:
        print("⚠️ 警告: 内存模块未找到，工具将返回模拟数据")
    
    # 运行 MCP 服务器
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()