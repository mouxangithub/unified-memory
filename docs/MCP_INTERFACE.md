# Unified Memory v5 — MCP 接口规范

## 概述

| 属性 | 值 |
|------|-----|
| 协议版本 | MCP 1.0 |
| 系统标识 | `gbrain-agent-brain` |
| 通讯模式 | stdio |
| 认证方式 | 无（本地使用） |

---

## 工具 (Tools)

### 1. `remember` — 存储记忆

**参数：**
```json
{
  "text": "string (必需)",          // 记忆内容
  "category": "string (可选)",      // 分类标签
  "importance": "number (可选)",    // 重要性 0-1
  "entities": "string[] (可选)",    // 实体列表
  "project": "string (可选)",       // 关联项目
  "topics": "string[] (可选)",     // 话题标签
  "relations": "object[] (可选)"    // 关联 [{targetId, type, weight}]
}
```

**输出：**
```
✅ 已记住并分析:
📝 内容: "..."
🆔 ID: mem_xxx
🏷️ 分类: xxx
⭐ 重要性: 0.5
🔍 检测到实体: N 个
🔗 找到相似记忆: N 条
📊 图谱统计: N 节点, N 边
```

---

### 2. `search` — 搜索记忆

**参数：**
```json
{
  "query": "string (必需)",         // 搜索查询
  "limit": "number (可选)",         // 结果数量，默认 10
  "entity": "string (可选)",        // 按实体过滤
  "project": "string (可选)",       // 按项目过滤
  "topic": "string (可选)",         // 按话题过滤
  "relatedTo": "string (可选)"      // 查找相关记忆
}
```

**输出：**
```
🔍 搜索 "xxx" 找到 N 条结果:

1. 记忆内容摘要...
   🏷️ category | 🆔 mem_xxx | 🔗 similar (70%)

📊 图谱: N 节点 | 🔍 本次搜索: N次
```

---

### 3. `get_context` — 获取上下文

**参数：** 无

**输出：**
```
🧠 GBrain 记忆大脑状态:

📊 统计:
   记忆数量: N
   关联数量: N
   搜索次数: N
   记忆次数: N
   运行时间: X秒

🔍 图谱功能:
   • 记忆关联网络 ✓
   • 实体检测 ✓
   • 类型化链接 ✓
   • 来源追溯 ✓
```

---

### 4. `cleanup` — 清理记忆

**参数：**
```json
{
  "threshold": "number (可选)",     // 重要性阈值，默认 0.1
  "max_age_days": "number (可选)"   // 最大保留天数，默认 30
}
```

**输出：**
```
🧹 清理完成:
清理数量: N 条
保留数量: N 条
阈值: 0.1
最大保留天数: 30
```

---

### 5. `graph_stats` — 图谱统计

**参数：** 无

**输出：**
```
📊 记忆关联网络统计:

节点数: N
边数: N
平均连接数: X.XX
孤立节点: N
实体类型: N

🔥 Top 实体:
   • entity1 (N)
   • entity2 (N)
```

---

## 资源 (Resources)

| URI | 名称 | 说明 |
|-----|------|------|
| `memory://recent` | recent_memories | 最近 20 条记忆 |
| `memory://entities` | entity_index | 所有实体索引 |
| `memory://graph` | graph_summary | 图谱统计摘要 |

---

## 快速配置

### OpenClaw

```json
{
  "mcp": {
    "servers": {
      "agent-brain": {
        "command": "node",
        "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"]
      }
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "gbrain-agent-brain": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"]
    }
  }
}
```

### Hermes

```yaml
# hermes.yaml
mcp:
  servers:
    - name: gbrain
      command: node
      args:
        - /path/to/unified-memory/src/gbrain_mcp_server.js
```
