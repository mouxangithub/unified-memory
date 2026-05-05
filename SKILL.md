# Unified Memory v5 — Skill for OpenClaw

> 🧠 AI Agent 统一记忆系统 | 一句话安装 | MCP 协议

## 一句话安装配置命令（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install && \
OLLAMA_BASE_URL=http://localhost:11434 && \
LLM_PROVIDER=ollama && LLM_MODEL=minimax-m2.7:cloud && \
EMBED_PROVIDER=ollama && EMBED_MODEL=nomic-embed-text:latest && \
VECTOR_ENGINE=lancedb && node src/gbrain_mcp_server.js
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

## 环境变量配置

创建 `.env` 文件：

```bash
# ─── LLM 配置 ───
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434
LLM_MAX_TOKENS=8192
LLM_TEMPERATURE=0.7

# ─── Embedding 配置 ───
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434
EMBED_DIMENSION=768

# ─── Ollama 统一配置 ───
OLLAMA_BASE_URL=http://localhost:11434

# ─── 向量引擎 ───
VECTOR_ENGINE=lancedb
LANCEDB_DB_PATH=~/.unified-memory/lancedb

# ─── 存储 ───
DATA_DIR=~/.unified-memory/data
GRAPH_DB_PATH=~/.unified-memory/graph.json

# ─── MCP ───
MCP_PORT=38421
MCP_MODE=stdio

# ─── 日志 ───
LOG_LEVEL=info
```

详细配置：[docs/CONFIG.md](docs/CONFIG.md)

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
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "LLM_PROVIDER": "ollama",
    "LLM_MODEL": "minimax-m2.7:cloud",
    "EMBED_PROVIDER": "ollama",
    "EMBED_MODEL": "nomic-embed-text:latest",
    "VECTOR_ENGINE": "lancedb"
  }
}
```

### 3. 重启 OpenClaw

```bash
openclaw gateway restart
```

---

## 完整配置项列表

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| **LLM** | | |
| `LLM_PROVIDER` | 提供商 | ollama |
| `LLM_MODEL` | 模型名称 | minimax-m2.7:cloud |
| `LLM_BASE_URL` | API 地址 | http://localhost:11434 |
| `LLM_API_KEY` | API 密钥 | - |
| `LLM_MAX_TOKENS` | 最大输出 | 8192 |
| `LLM_TEMPERATURE` | 温度参数 | 0.7 |
| **Embedding** | | |
| `EMBED_PROVIDER` | 提供商 | ollama |
| `EMBED_MODEL` | 模型 | nomic-embed-text:latest |
| `EMBED_BASE_URL` | API 地址 | http://localhost:11434 |
| `EMBED_DIMENSION` | 向量维度 | 768 |
| **Ollama** | | |
| `OLLAMA_BASE_URL` | 服务地址 | http://localhost:11434 |
| `OLLAMA_HOST` | 主机别名 | http://localhost:11434 |
| **向量引擎** | | |
| `VECTOR_ENGINE` | 引擎类型 | lancedb |
| `VECTOR_DB_PATH` | 数据库路径 | ~/.unified-memory/ |
| `LANCEDB_DB_PATH` | LanceDB 路径 | ~/.unified-memory/lancedb |
| **存储** | | |
| `DATA_DIR` | 数据目录 | ~/.unified-memory/data |
| `GRAPH_DB_PATH` | 图谱路径 | ~/.unified-memory/graph.json |
| `BACKUP_DIR` | 备份目录 | ~/.unified-memory/backups |
| **MCP** | | |
| `MCP_PORT` | HTTP 端口 | 38421 |
| `MCP_MODE` | 模式 | stdio |
| `MCP_SERVER_NAME` | 服务器名 | gbrain-agent-brain |
| **性能** | | |
| `MAX_CONCURRENT` | 最大并发 | 10 |
| `CACHE_SIZE` | 缓存大小(MB) | 512 |
| `SEARCH_LIMIT` | 结果限制 | 20 |
| `IMPORTANCE_THRESHOLD` | 重要性阈值 | 0.1 |
| `MAX_AGE_DAYS` | 保留天数 | 30 |
| `LOG_LEVEL` | 日志级别 | info |

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
- ✅ **Hermes** - 安装 SKILL.md 到 `~/.hermes/skills/`
- ✅ **其他 MCP 客户端** - 通用 stdio 协议

### Hermes 安装

```bash
# 创建目录并安装
mkdir -p ~/.hermes/skills/memory/unified-memory
cp SKILL.md ~/.hermes/skills/memory/unified-memory/


# 验证
hermes skills list | grep unified
```

---

## 技术细节

| 项目 | 值 |
|------|-----|
| 协议 | MCP 1.0 (stdio) |
| 运行时 | Node.js 18+ |
| LLM | ollama, openai, minimax, siliconflow, custom |
| Embedding | ollama, openai, jina, siliconflow, custom |
| 向量引擎 | LanceDB, ChromaDB, FAISS, builtin |
| 存储 | JSON (开发), PostgreSQL (生产) |

---

## 源文件

- **MCP 服务器**: `src/gbrain_mcp_server.js`
- **核心模块**: `src/gbrain-integration.js`
- **图谱引擎**: `src/memory_graph.js`
- **实体检测**: `src/entity_detection.js`
- **配置管理**: `src/config.js`
- **Embedding**: `src/cache_semantic.js`

---

## 一键配置脚本

```bash
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
VECTOR_ENGINE=lancedb
DATA_DIR=~/.unified-memory/data
LOG_LEVEL=info
EOF
```

---

## 相关链接

- GitHub: https://github.com/mouxangithub/unified-memory
- 文档: [CONFIG.md](docs/CONFIG.md) | [ARCHITECTURE.md](docs/ARCHITECTURE.md) | [MCP_INTERFACE.md](docs/MCP_INTERFACE.md)