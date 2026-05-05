# Unified Memory v5 — Skill for OpenClaw

> 🧠 AI Agent 统一记忆系统 | 一句话安装 | MCP 协议

## 一句话安装命令（发给 AI）

```
请帮我安装 Unified Memory v5：
1. git clone https://github.com/mouxangithub/unified-memory.git
2. cd unified-memory && npm install
3. 告诉我在 OpenClaw 中如何配置 MCP 连接
```

---

## 功能概述

| 功能 | 工具 | 说明 |
|------|------|------|
| 🧠 记忆存储 | `remember` | 自动实体检测+关联 |
| 🔍 语义搜索 | `search` | 混合搜索+过滤 |
| 📊 图谱查询 | `graph_stats` | 关联网络统计 |
| 🧹 记忆清理 | `cleanup` | 清理低价值记忆 |
| 💬 上下文 | `get_context` | 系统状态 |

---

## 快速配置

### 1. 安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
```

### 2. 配置 OpenClaw

在 `~/.openclaw/openclaw.json` 的 `mcp.servers` 中添加：

```json
"agent-brain": {
  "command": "node",
  "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"],
  "env": {
    "LOG_LEVEL": "info"
  }
}
```

### 3. 重启 OpenClaw

```bash
openclaw gateway restart
```

---

## 可用工具

### remember
存储记忆，自动进行实体检测和关联分析。

```
参数：text (必需), category, importance (0-1), entities, project, topics
返回：记忆ID + 检测到的实体 + 相似记忆数量
```

### search
语义搜索记忆，支持多维度过滤。

```
参数：query (必需), limit, entity, project, topic, relatedTo
返回：相关记忆列表 + 相似度分数
```

### get_context
获取记忆系统当前状态。

```
参数：无
返回：记忆数量、关联数量、搜索次数、运行时间
```

### graph_stats
获取记忆关联网络的详细统计。

```
参数：无
返回：节点数、边数、平均连接数、Top 实体
```

### cleanup
清理低重要性和过期的记忆。

```
参数：threshold (默认0.1), max_age_days (默认30)
返回：清理数量、保留数量
```

---

## MCP 接口兼容

- ✅ **OpenClaw** - 直接配置 `mcp.servers`
- ✅ **Claude Desktop** - 配置 `mcpServers`
- ✅ **Hermes** - 配置 `mcp.servers`
- ✅ **其他 MCP 客户端** - 通用 stdio 协议

## ⚙️ 配置

```bash
# .env 文件
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434

EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434
```

详细配置：[CONFIG.md](docs/CONFIG.md)

---

## 技术细节

| 项目 | 值 |
|------|-----|
| 协议 | MCP 1.0 (stdio) |
| 运行时 | Node.js 18+ |
| LLM | ollama/openai/minimax/kimi |
| Embedding | ollama/openai/cohere |
| 向量引擎 | LanceDB/ChromaDB/FAISS |
| 存储 | JSON (开发) / PostgreSQL (生产) |

---

## 源文件

- **MCP 服务器**: `src/gbrain_mcp_server.js`
- **核心模块**: `src/gbrain-integration.js`
- **图谱引擎**: `src/memory_graph.js`
- **实体检测**: `src/entity_detection.js`

---

## 相关链接

- GitHub: https://github.com/mouxangithub/unified-memory
- 文档: [ARCHITECTURE.md](docs/ARCHITECTURE.md) | [MCP_INTERFACE.md](docs/MCP_INTERFACE.md)
