# 快速入门

> 5分钟内开始使用 Unified Memory。

## 🚀 安装（一键命令）

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

验证安装：
```bash
unified-memory --version
# 输出：v5.2.0
```

## 💡 您的第一个记忆

### 使用 CLI

```bash
# 添加记忆
unified-memory add "Remember to review quarterly reports" --tags work,reminder

# 搜索记忆
unified-memory search "quarterly reports"

# 列出所有记忆
unified-memory list

# 查看特定记忆
unified-memory get <memory-id>

# 删除记忆
unified-memory delete <memory-id>
```

### 使用 JavaScript/TypeScript

```javascript
const { addMemory, searchMemories, getAllMemories, getMemory, deleteMemory } = require('unified-memory');

async function main() {
  // 添加记忆
  const memoryId = await addMemory({
    text: "User prefers morning meetings",
    category: "preference",
    importance: 0.8,
    tags: ["meetings", "schedule"],
    metadata: { priority: "high" }
  });
  console.log(`Added memory: ${memoryId}`);

  // 搜索记忆
  const results = await searchMemories("meeting schedule");
  console.log("Search results:", results);

  // 获取所有记忆
  const allMemories = await getAllMemories();
  console.log(`Total memories: ${allMemories.length}`);

  // 获取特定记忆
  const memory = await getMemory(memoryId);
  console.log(memory);

  // 删除记忆
  await deleteMemory(memoryId);
  console.log("Deleted memory");
}

main().catch(console.error);
```

### 使用 MCP 工具

```javascript
// 通过 MCP 客户端（例如 OpenClaw）
const result = await mcp.call('unified-memory', 'memory_store', {
  text: "Important meeting tomorrow at 9 AM",
  category: "fact",
  importance: 0.9,
  tags: ["meeting", "important"]
});

const searchResult = await mcp.call('unified-memory', 'memory_search', {
  query: "meeting tomorrow",
  topK: 5,
  mode: "hybrid"
});
```

## 🔍 搜索示例

### 简单搜索
```javascript
const results = await searchMemories("quarterly reports");
```

### 混合搜索（BM25 + 向量）
```javascript
const results = await searchMemories("important deadlines", {
  mode: "hybrid",
  vectorWeight: 0.7,
  bm25Weight: 0.3,
  topK: 10
});
```

### 带过滤器的搜索
```javascript
const results = await searchMemories("project update", {
  filters: {
    category: "fact",
    tags: ["work"],
    importance: { min: 0.7 }
  }
});
```

## 🔄 原子事务

在存储多个相关记忆时保证数据一致性：

```javascript
const { beginTransaction, commitTransaction, rollbackTransaction, addMemory } = require('unified-memory');

async function storeTransaction() {
  const tx = await beginTransaction();
  
  try {
    await addMemory({
      text: "Project kickoff meeting",
      tags: ["project", "meeting"]
    }, { transaction: tx });
    
    await addMemory({
      text: "Project deadline is Dec 31",
      tags: ["project", "deadline"]
    }, { transaction: tx });
    
    await commitTransaction(tx);
    console.log("Transaction committed successfully");
  } catch (error) {
    await rollbackTransaction(tx);
    console.error("Transaction rolled back:", error);
  }
}
```

## 🏷️ 记忆类别

记忆被分类以便更好地组织：

| 类别 | 描述 |
|------|------|
| `preference` | 用户偏好和喜好 |
| `fact` | 事实信息 |
| `decision` | 做出的决定 |
| `entity` | 人、地点、事物 |
| `reflection` | 想法和反思 |

## 📊 查看统计

```bash
unified-memory stats
```

输出：
```
Total Memories: 150
Categories: 5
Tags: 42

By Tier:
  HOT: 45 (30%)
  WARM: 60 (40%)
  COLD: 45 (30%)

By Scope:
  USER: 120
  AGENT: 20
  TEAM: 10
```

## 🔌 插件快速入门

### 启用工作区同步

```bash
# 与 Workspace Memory 同步记忆
npm run sync:manual

# 安排自动同步
npm run sync
```

### 健康监控

```bash
# 检查系统健康
npm run monitor

# 启动监控仪表板
npm run monitor:dashboard
```

## 🧪 验证安装

```bash
# 运行验证测试
npm run verify

# 运行单元测试
npm run test:unit

# 测试原子写入
npm run test:atomic
```

## 🚨 常见问题

### "命令未找到"
```bash
# 重新安装
npm install -g unified-memory
# 或添加到 PATH
export PATH="$(npm root -g)/bin:$PATH"
```

### 向量存储错误
```bash
# 重新初始化向量存储
rm -rf ~/.unified-memory/vector.lance
unified-memory init
```

### Ollama 连接失败
```bash
# 启动 Ollama
ollama serve

# 拉取嵌入模型
ollama pull nomic-embed-text
```

## 📈 下一步

| 目标 | 指南 |
|------|------|
| 学习更多操作 | [基础使用指南](../guides/basic-usage.md) |
| 高级功能 | [高级使用](../guides/advanced-usage.md) |
| 构建插件 | [插件开发](../guides/plugins.md) |
| 理解内部原理 | [架构概述](../architecture/overview.md) |
| API 参考 | [API 参考](../api/overview.md) |

## 💬 需要帮助？

- [故障排除指南](../reference/troubleshooting.md)
- [FAQ](../reference/faq.md)
- [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
