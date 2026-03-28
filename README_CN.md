# 🧠 Unified Memory v2.6

> AI Agent 专用记忆系统 — 多层级、持久化、主动式

**作者**：程序员小刘（@mouxangithub）  
**GitHub**：https://github.com/mouxangithub/unified-memory  
**安装**：`clawhub install unified-memory`  
**框架**：OpenClaw Agent | Node.js ESM | 76 个 MCP 工具

---

## 📖 目录

- [核心特性](#核心特性)
- [环境要求](#环境要求)
- [安装](#安装)
  - [选项 1 — Clawhub（推荐）](#选项-1--clawhub推荐)
  - [选项 2 — Curl 安装脚本](#选项-2--curl-安装脚本)
  - [选项 3 — 手动安装](#选项-3--手动安装)
- [快速开始](#快速开始)
- [配置](#配置)
- [架构](#架构)
- [第三阶段新工具](#第三阶段新工具)
- [开发](#开发)
- [许可证](#许可证)

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 **持久化上下文** | 不再每次重新理解，记忆持久化 |
| 🔍 **混合搜索** | BM25 + 向量 + RRF 融合（完全本地，Ollama 驱动） |
| 💬 **自动存储** | Hooks 模式，无需手动调用 |
| 🏷️ **Scope 隔离** | AGENT / USER / TEAM / GLOBAL — 在 LanceDB 查询层执行 |
| 📈 **Weibull 衰减** | 人类遗忘曲线（shape=1.5，scale=30天） |
| 🔗 **Git 版本化** | Git 备份记忆快照和 notes |
| ☁️ **云备份** | SuperMemory API + Custom REST 双模式同步 |
| 📊 **知识图谱** | 实体提取和关系映射 |
| 🏥 **健康检查** | 完整的系统健康监控 |

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Node.js | ≥ 22 | ESM 必需 |
| Ollama | ≥ 0.1.40 | 可选；缺失时降级到纯 BM25 |
| OpenClaw | ≥ 2026.3 | 用于技能系统 / Clawhub 集成 |

---

## 安装方式

### 方式一 — Clawhub（推荐）
```bash
clawhub install unified-memory
openclaw gateway restart
```

### 方式二 — Curl 安装脚本
```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### 方式三 — 手动安装
```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## 快速开始

```bash
# 验证安装
mcporter call unified-memory memory_health '{}'

# 存储一条记忆
mcporter call unified-memory memory_store '{"text": "刘总喜欢简洁直接的沟通风格", "category": "preference", "scope": "USER"}'

# 搜索记忆
mcporter call unified-memory memory_search '{"query": "刘总沟通风格", "scope": "USER"}'

# 查看统计
mcporter call unified-memory memory_stats '{}'
```

---

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务器地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text-v1.5` | Embedding 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |

---

## 架构

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 63 个核心工具（index.js）
    ├── Phase 3 新增：
    │   ├── plugin/         — OpenClaw Memory Plugin 接口
    │   ├── search/         — QMD 搜索后端
    │   ├── integrations/   — Git + 云备份
    │   └── decay/          — Weibull 衰减模型
    ├── BM25 + Vector + RRF 混合搜索
    ├── LanceDB（嵌入式，零配置）
    ├── WAL + 分层管理
    └── 知识图谱 + Preference Slots
```

---

## Phase 3 新增工具

### Plugin 接口（3个）
`phase3_memory_search` · `phase3_memory_get` · `phase3_memory_write`

### Git 集成（7个）
`memory_git_init` · `memory_git_sync` · `memory_git_history` · `memory_git_note` · `memory_git_pull` · `memory_git_push` · `memory_git_status`

### 云备份（3个）
`memory_cloud_sync` · `memory_cloud_push` · `memory_cloud_pull`

### Weibull 衰减（2个）
`memory_decay_stats` · `memory_decay_strength`

### QMD 后端（3个）
`memory_qmd_query` · `memory_qmd_status` · `memory_qmd_search2`

---

## Scope 隔离

Scope 过滤在 **LanceDB 查询层**执行（非结果后过滤），每个 scope 只看到自己的向量：

| Scope | 访问权限 |
|-------|---------|
| `AGENT` | 单 Agent 私有 |
| `USER` | 单用户，排除 AGENT |
| `TEAM` | 团队共享，排除 USER/AGENT |
| `GLOBAL` | 全局公开 |

```bash
# 仅在 USER scope 内搜索
mcporter call unified-memory memory_search '{"query": "项目计划", "scope": "USER"}'
```

---

## 开发

```bash
# 安装依赖（peer deps 由宿主机提供）
npm install --ignore-scripts

# 启动 MCP 服务器（stdio）
node src/index.js

# 启动 REST API
node src/cli/index.js server --port 38421

# CLI 帮助
node src/cli/index.js --help

# 运行测试
node run-tests.cjs
```

---

## 文件结构

| 文件/目录 | 说明 |
|---------|------|
| `src/index.js` | MCP 服务器（63 个核心工具） |
| `src/plugin/` | OpenClaw Memory Plugin 接口 |
| `src/search/` | QMD 搜索后端 |
| `src/integrations/` | Git + 云备份 |
| `src/decay/` | Weibull 衰减模型 |
| `src/core/` | BM25、vector、fusion、tier、dedup 等 |
| `src/cli/` | CLI 工具 |
| `wal/` | 写前日志 |
| `memories.json` | 记忆持久化 |

---

## License

MIT

*最后更新：2026-03-28 | v2.6.0*
