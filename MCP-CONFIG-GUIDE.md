# Unified Memory MCP 配置指南

本指南介绍如何配置和使用 Unified Memory 的 MCP 服务器。

## 📋 目录

- [快速开始](#快速开始)
- [MCP 服务器配置](#mcp-服务器配置)
- [工具说明](#工具说明)
- [环境变量](#环境变量)
- [故障排除](#故障排除)

## 🚀 快速开始

### 1. 安装依赖

```bash
cd skills/unified-memory
pip install -r requirements.txt
# 或使用 uv（推荐）
uv sync
```

### 2. 配置 MCP

将以下配置添加到您的 `.cursor/mcp.json` 文件中：

```json
{
  "mcpServers": {
    "unified_memory": {
      "command": "python3",
      "args": [
        "/path/to/skills/unified-memory/mcp_server.py"
      ],
      "env": {
        "MEMORY_STORAGE_PATH": "/path/to/skills/unified-memory/memory/data"
      }
    }
  }
}
```

### 3. 重启 Cursor 或 Claude

配置更改后，重启您的客户端以加载新配置。

## 🛠️ MCP 服务器配置

### 基本配置

```json
{
  "mcpServers": {
    "unified_memory": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "env": {
        "MEMORY_STORAGE_PATH": "./memory/data"
      }
    }
  }
}
```

### 高级配置

```json
{
  "mcpServers": {
    "unified_memory": {
      "command": "uv",
      "args": [
        "--directory",
        "./skills/unified-memory",
        "run",
        "mcp_server.py"
      ],
      "env": {
        "MEMORY_STORAGE_PATH": "./memory/data",
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "./skills/unified-memory"
      }
    }
  }
}
```

### 多 MCP 服务器配置

```json
{
  "mcpServers": {
    "unified_memory": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "env": {"MEMORY_STORAGE_PATH": "./memory/data"}
    },
    "web_search": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {"FIRECRAWL_API_KEY": "your-key"}
    }
  }
}
```

## 📚 工具说明

### 1. memory_search

在统一记忆系统中搜索相关内容。

**参数**:
- `query` (string): 搜索查询内容
- `limit` (int, 默认: 10): 返回结果数量
- `threshold` (float, 默认: 0.5): 相似度阈值
- `search_type` (string, 默认: "hybrid"): 搜索类型

**示例**:
```python
# 搜索相关内容
result = await mcp.call_tool("memory_search", {
    "query": "如何使用统一记忆系统",
    "limit": 5,
    "threshold": 0.6
})
```

### 2. memory_store

存储内容到统一记忆系统。

**参数**:
- `content` (string): 要存储的内容
- `metadata` (object, 可选): 元数据
- `category` (string, 可选): 内容分类

**示例**:
```python
# 存储内容
result = await mcp.call_tool("memory_store", {
    "content": "统一记忆系统使用指南",
    "metadata": {"author": "admin", "version": "1.0"},
    "category": "documentation"
})
```

### 3. memory_health

检查统一记忆系统的健康状态。

**参数**:
- `check_type` (string, 默认: "basic"): 检查类型

**示例**:
```python
# 检查健康状态
result = await mcp.call_tool("memory_health", {
    "check_type": "full"
})
```

### 4. memory_stats

获取统一记忆系统的统计信息。

**参数**: 无

**示例**:
```python
# 获取统计信息
result = await mcp.call_tool("memory_stats")
```

### 5. memory_clear

清理统一记忆系统中的数据（谨慎使用）。

**参数**:
- `confirm` (bool, 默认: false): 确认执行清理
- `older_than_days` (int, 可选): 清理指定天数前的数据

**示例**:
```python
# 清理 30 天前的数据
result = await mcp.call_tool("memory_clear", {
    "confirm": True,
    "older_than_days": 30
})
```

## 🔧 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MEMORY_STORAGE_PATH` | 记忆存储路径 | `./memory/data` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `PYTHONPATH` | Python 路径 | `./skills/unified-memory` |

## 🔍 故障排除

### 问题 1: 无法连接 MCP 服务器

**解决方案**:
1. 检查 Python 是否安装
2. 验证 MCP 服务器文件路径
3. 检查环境变量配置

### 问题 2: 工具返回空结果

**解决方案**:
1. 检查记忆系统是否已初始化
2. 验证存储路径是否存在
3. 查看日志文件了解详细错误

### 问题 3: 性能问题

**解决方案**:
1. 检查存储大小和索引状态
2. 运行健康检查 `memory_health`
3. 考虑清理旧数据 `memory_clear`

### 问题 4: 权限问题

**解决方案**:
1. 确保有读写权限
2. 检查存储路径权限
3. 使用 `chmod` 修复权限

## 📊 验证配置

配置完成后，可以通过以下方式验证：

1. **检查 MCP 服务器状态**:
```bash
python3 mcp_server.py
```

2. **测试工具调用**:
```python
# 在 Python 中测试
import asyncio
from mcp_use import MCPClient, MCPAgent

async def test():
    client = MCPClient.from_dict({
        "mcpServers": {
            "unified_memory": {
                "command": "python3",
                "args": ["mcp_server.py"]
            }
        }
    })
    agent = MCPAgent(llm=llm, client=client)
    result = await agent.run("测试记忆搜索")
    print(result)

asyncio.run(test())
```

3. **在 Cursor/Claude 中测试**:
   - 重启客户端
   - 尝试调用记忆工具
   - 查看工具是否出现在工具列表中

## 📝 最佳实践

1. **定期备份**: 定期备份记忆数据
2. **监控性能**: 定期运行健康检查
3. **清理旧数据**: 定期清理不需要的数据
4. **日志记录**: 启用详细日志以便调试
5. **错误处理**: 始终处理工具调用的异常

## 🤝 支持

如有问题，请：
1. 查看日志文件
2. 运行健康检查
3. 检查配置文件
4. 参考 GitHub Issues

---

**版本**: v5.2.4  
**最后更新**: 2026-04-16  
**参考**: [AI Engineering Hub](https://github.com/patchy631/ai-engineering-hub)