# 🧠 Unified Memory v3.x

> AI Agent 专用记忆系统 — 多层级、持久化、主动式

**作者**：程序员小刘（@mouxangithub）  
**GitHub**：https://github.com/mouxangithub/unified-memory  
**安装**：`clawhub install unified-memory`  
**框架**：OpenClaw Agent | Node.js ESM | 28 个 MCP 工具 | Web 仪表板 v3.x

---

## 📖 目录

- [核心特性](#核心特性)
- [架构](#架构)
- [安装](#安装)
- [配置](#配置)
- [28 个 MCP 工具](#28-个-mcp-工具)
- [快速开始](#快速开始)
- [Scope 隔离](#scope-隔离)
- [开发](#开发)
- [License](#license)

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 **持久化上下文** | 不再每次重新理解，记忆持久化 |
| 🔍 **混合搜索** | BM25 + 向量 + RRF 融合（可选 LanceDB/Ollama/none） |
| 💬 **自动存储** | Hooks 模式，无需手动调用 |
| 🏷️ **Scope 隔离** | AGENT / USER / TEAM / GLOBAL |
| 📈 **Weibull 衰减** | 人类遗忘曲线（shape=1.5，scale=30天） |
| 🔗 **Git 版本化** | Git 备份记忆快照和 notes |
| ☁️ **云备份** | 本地 Git + 云端备份双模式 |
| 📊 **知识图谱** | 实体提取和关系映射 |
| 🏥 **健康检查** | 完整的系统健康监控 |
| ⚡ **可配置架构** | LanceDB / Ollama / none 按需组合 |

---

## 架构

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 28 个核心工具（统一 action 参数入口）
    ├── 存储层：JSON + WAL（崩溃可恢复）
    ├── 向量层（可插拔）：
    │   ├── LanceDB（默认，零配置）
    │   ├── Ollama Embedding（可选）
    │   └── none（纯 BM25 模式）
    ├── LLM 层（可插拔）：
    │   ├── Ollama（默认，本地）
    │   └── none（降级到规则模式）
    └── 分层管理：HOT / WARM / COLD
```

**配置模式**：

| 模式 | 向量引擎 | Embedding | LLM |
|------|---------|-----------|-----|
| 默认（推荐） | LanceDB | Ollama | Ollama |
| 轻量 | none | none | none |
| 本地向量 | LanceDB | Ollama | none |
| 云端托管 | LanceDB Cloud | LanceDB managed | Ollama/OpenAI |

---

## 安装

### 方式一 — Clawhub（推荐）
```bash
clawhub install unified-memory
openclaw gateway restart
```

### 方式二 — Curl 安装脚本（自动装 LanceDB）
```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### 方式三 — 手动安装
```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## 配置

详见 [docs/CONFIG.md](docs/CONFIG.md)，核心配置项：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务器地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |
| `LANCEDB_API_KEY` | （空） | LanceDB Cloud API Key（可选） |
| `VECTOR_ENGINE` | `lancedb` | 向量引擎：lancedb / ollama / none |
| `LLM_PROVIDER` | `ollama` | LLM 提供者：ollama / openai / none |

---

## 28 个 MCP 工具

### 存储核心（5）
| 工具 | 说明 |
|------|------|
| `store` | 存储记忆（category/importance/tags/scope） |
| `get` | 获取单条记忆 |
| `list` | 分页列出记忆 |
| `delete` | 删除记忆 |
| `search` | 混合搜索：BM25 → Vector → Rerank → MMR |

### 统一入口（8个，action 参数）
| 工具 | action 参数 |
|------|------------|
| `memory_reminder` | add / list / cancel |
| `memory_preference` | get / set / infer / explain / stats / slots |
| `memory_version` | list / diff / restore |
| `memory_tier` | status / migrate / compress |
| `memory_proactive` | status / trigger / start / stop |
| `memory_proactive_care` | - |
| `memory_proactive_recall` | - |
| `memory_qmd` | search / get / vsearch / list / status |
| `memory_engine` | bm25 / embed / search / mmr / rerank |
| `memory_graph` | entity / relation / query / stats / add / delete |

### 检索增强（4）
`memory_bm25` · `memory_vector` · `memory_scope` · `memory_concurrent_search`

### 分析管理（9）
`memory_trace` · `memory_metrics` · `memory_noise` · `memory_decay` · `memory_dedup` · `memory_extract` · `memory_reflection` · `memory_intent` · `memory_wal`

### 云与系统（6）
`memory_cloud_backup` · `memory_cloud_restore` · `memory_export` · `memory_adaptive` · `memory_autostore` · `memory_auto_extract` · `memory_health` · `memory_insights` · `memory_predict` · `memory_feedback`

---

## 快速开始

```bash
# 验证安装
mcporter call unified-memory memory_health '{}'

# 存储记忆
mcporter call unified-memory memory_store '{"text": "刘总喜欢简洁直接的沟通风格", "category": "preference", "scope": "USER"}'

# 搜索记忆
mcporter call unified-memory memory_search '{"query": "刘总沟通风格", "scope": "USER"}'

# 查看统计
mcporter call unified-memory memory_stats '{}'

# 添加提醒
mcporter call unified-memory memory_reminder '{"action": "add", "content": "开会", "minutes": 30}'

# 查看知识图谱
mcporter call unified-memory memory_graph '{"action": "stats"}'
```

---

## Scope 隔离

| Scope | 访问权限 |
|-------|---------|
| `AGENT` | 单 Agent 私有 |
| `USER` | 单用户，排除 AGENT |
| `TEAM` | 团队共享，排除 USER/AGENT |
| `GLOBAL` | 全局公开 |

```bash
mcporter call unified-memory memory_search '{"query": "项目计划", "scope": "USER"}'
```

---

## 开发

```bash
# 安装依赖
npm install --ignore-scripts

# 启动 MCP 服务器
node src/index.js

# CLI 帮助
node src/cli/index.js --help

# 运行测试
node run-tests.cjs

# Web 仪表板
node src/webui/dashboard.js
```

---

## 文件结构

```
src/
├── index.js          # MCP 服务器（28 个工具）
├── storage.js        # JSON 持久化 + WAL
├── vector_lancedb.js # LanceDB 向量后端
├── bm25.js           # BM25 搜索引擎
├── graph/            # 知识图谱
├── tools/            # 各类工具封装
└── webui/            # Web 仪表板
docs/
└── CONFIG.md         # 详细配置指南
```

---

## License

MIT

*最后更新：2026-03-29 | v3.x*
