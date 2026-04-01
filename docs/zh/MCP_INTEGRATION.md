# MCP 集成指南

[English](./en/MCP_INTEGRATION.md) | [概述](./README.md) | 中文

## 概述

MCP（Model Context Protocol）集成提供对统一记忆系统的**显式、程序化访问**。当你想要精细控制存储、搜索或删除哪些记忆时，使用 MCP 工具。

## 可用的 MCP 工具

### memory_search

使用自然语言查询搜索相关记忆。

```json
{
  "tool": "memory_search",
  "parameters": {
    "query": "用户偏好的编程语言是什么？",
    "limit": 5,
    "similarityThreshold": 0.7
  }
}
```

**响应：**

```json
{
  "results": [
    {
      "id": "mem_abc123",
      "content": "用户大多数项目偏好 Python 和 TypeScript",
      "timestamp": "2026-03-25T14:30:00Z",
      "sessionId": "sess_xyz789",
      "importance": 0.85,
      "tags": ["偏好", "编程"]
    }
  ],
  "totalMatches": 3
}
```

### memory_write

显式存储新记忆。

```json
{
  "tool": "memory_write",
  "parameters": {
    "content": "用户主要使用 Go 开发后端 API",
    "tags": ["偏好", "工作"],
    "importance": 0.9
  }
}
```

### memory_update

通过 ID 更新现有记忆。

```json
{
  "tool": "memory_update",
  "parameters": {
    "id": "mem_abc123",
    "content": "用户偏好 Python、TypeScript，并且越来越多地使用 Go",
    "importance": 0.95
  }
}
```

### memory_delete

删除特定记忆。

```json
{
  "tool": "memory_delete",
  "parameters": {
    "id": "mem_abc123"
  }
}
```

### memory_list

列出所有记忆，支持可选过滤。

```json
{
  "tool": "memory_list",
  "parameters": {
    "limit": 50,
    "offset": 0,
    "tags": ["偏好"],
    "sortBy": "importance"
  }
}
```

### memory_stats

获取记忆存储的统计信息。

```json
{
  "tool": "memory_stats",
  "parameters": {}
}
```

**响应：**

```json
{
  "totalMemories": 342,
  "totalChunks": 1287,
  "oldestMemory": "2026-01-15T09:00:00Z",
  "newestMemory": "2026-04-01T12:00:00Z",
  "storageSizeBytes": 4821932,
  "tagCounts": {
    "preferences": 45,
    "projects": 120,
    "decisions": 89
  }
}
```

## 配置

### 在 OpenClaw 中启用 MCP

添加到你的 OpenClaw 配置：

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "disabled",
        "config": {
          "mcpEnabled": true,
          "mcpServerPort": 3000
        }
      }
    }
  }
}
```

### MCP 服务器设置

| 设置 | 默认值 | 描述 |
|------|--------|------|
| `mcpEnabled` | `true` | 启用 MCP 服务器 |
| `mcpServerPort` | `3000` | MCP 服务器端口 |
| `mcpServerHost` | `localhost` | 主机绑定 |
| `maxConnections` | `10` | 最大并发 MCP 连接数 |

## 使用示例

### 示例：记住用户偏好

```javascript
// 在对话中用户提到某个偏好后
await mcp.callTool("memory_write", {
  content: "用户偏好使用 camelCase 命名变量",
  tags: ["偏好", "代码风格"],
  importance: 0.8
});
```

### 示例：查找关于某个项目的所有记忆

```javascript
const results = await mcp.callTool("memory_search", {
  query: "关于后端 API 项目的记忆",
  limit: 20
});

console.log(`找到 ${results.totalMatches} 条记忆`);
results.results.forEach(m => console.log(`- ${m.content}`));
```

### 示例：清理旧记忆

```javascript
const stats = await mcp.callTool("memory_stats", {});

// 删除超过 90 天的记忆
const cutoff = new Date();
cutoff.setDate(cutoff.getDate() - 90);

const allMemories = await mcp.callTool("memory_list", {
  limit: 1000
});

for (const mem of allMemories.results) {
  if (new Date(mem.timestamp) < cutoff) {
    await mcp.callTool("memory_delete", { id: mem.id });
  }
}
```

### 示例：根据反馈更新重要性

```javascript
// 如果用户确认某条记忆有用，提高其重要性
const current = await mcp.callTool("memory_list", {
  limit: 1,
  sortBy: "importance",
  sortOrder: "desc"
});

if (current.results[0]) {
  await mcp.callTool("memory_update", {
    id: current.results[0].id,
    importance: Math.min(1.0, current.results[0].importance + 0.1)
  });
}
```

## MCP vs Hook：选择你的方式

详见 [集成对比](./INTEGRATION_COMPARISON.md) 获取详细的决策矩阵。

**在以下情况下使用 MCP：**
- 想要显式控制存储内容
- 需要程序化管理记忆
- 希望从外部工具查询记忆
- 想要批量操作记忆

**在以下情况下使用 Hooks：**
- 想要完全自动化的运行
- 不需要代码更改
- 追求最大 simplicity
