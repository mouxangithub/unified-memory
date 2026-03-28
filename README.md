---

<div align="center">

# 🧠 Unified Memory v2.0

*AI Agent 专用记忆系统 - 多层级、持久化、主动式记忆*

> **🤖 本项目由小智 AI（OpenClaw）创建生成**  
> 作者：程序员小刘（@mouxangithub）  
> 基于 OpenClaw Agent 框架驱动，集成 BM25 + 向量混合搜索、RAG、主动召回等 86 个工具

[![GitHub stars](https://img.shields.io/github/stars/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green.svg)](https://nodejs.org/)

---

## 🌍 Documentation Index | 文档索引

| Language | README | Skill |
|----------|--------|-------|
| 🇨🇳 中文 | [README.md](README.md) ✅ | [SKILL.md](SKILL.md) |
| 🇺🇸 English | [README_EN.md](README_EN.md) | [SKILL_EN.md](SKILL_EN.md) |

> **SKILL.md 默认语言为中文**，如需英文版见 [SKILL_EN.md](SKILL_EN.md)

---

## 🌟 Core Features | 核心特性

| Feature | 说明 |
|---------|------|
| 🔄 **持久化上下文** | 不再每次重新理解，持久化上下文窗口 |
| 🔍 **混合搜索** | BM25 + 向量 + RRF 融合 (完全本地) |
| 💬 **自动存储** | Hooks 模式，无需手动调用 |
| 📊 **用户洞察** | 类别分布、工具使用分析 |
| 🧹 **智能遗忘** | 低价值记忆自动淘汰 |
| 🔗 **知识图谱** | 实体提取和关系可视化 |
| 🤝 **多Agent协作** | 多 Agent 记忆同步 |
| 🏥 **健康检查** | 完整的系统健康监控 |

---

## 🚀 Quick Start | 快速开始

### 方式一：OpenClaw 技能市场（一键安装）

```bash
# 查看技能信息
clawhub info unified-memory

# 一键安装
clawhub install unified-memory

# 重启 OpenClaw
openclaw gateway restart
```

### 方式二：curl 安装脚本（任意 AI Agent）

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### 方式三：手动安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install --ignore-scripts
node src/index.js
```

---

## 📋 前置要求 | Prerequisites

| Dependency | 版本 | 说明 |
|------------|------|------|
| Node.js | ≥ 22 | 推荐使用最新 LTS |
| Ollama | ≥ 0.1.40 | 本地向量搜索（可选，无则降级到 BM25） |
| OpenClaw | ≥ 2026.3 | Skill 系统接入（可选） |

```bash
# 安装 Ollama（可选）
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text   # 嵌入模型
```

---

## 🔌 接入任意 AI Agent | Integrate with Any AI Agent

> AI Agent 专用记忆系统 - 多层级、持久化、主动式记忆

[![GitHub stars](https://img.shields.io/github/stars/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green.svg)](https://nodejs.org/)

---

## 🚀 零门槛接入（推荐）

### 方式一：OpenClaw 技能市场（一键安装）

```bash
# 查看技能信息
clawhub info unified-memory

# 一键安装
clawhub install unified-memory

# 重启 OpenClaw
openclaw gateway restart
```

> OpenClaw 会自动：
> 1. 克隆/拉取最新代码到 `~/.openclaw/workspace/skills/unified-memory/`
> 2. 通过 mcporter 自动注册 86 个工具
> 3. 服务保持后台运行（keep-alive）

---

### 方式二：手动安装（任意 AI Agent）

```bash
# 1. 克隆技能
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 2. 一键安装依赖（自动解析 peerDependencies）
npm install --ignore-scripts

# 3. 验证运行
node src/index.js
# 输出: MCP Server connected via stdio (86 tools)

# 4. 注册到你的 Agent（见下方「接入任意 AI Agent」）
```

---

## 📋 前置要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Node.js | ≥ 22 | 推荐使用最新 LTS |
| Ollama | ≥ 0.1.40 | 本地向量数据库（可选，无 Ollama 时自动降级） |
| OpenClaw | ≥ 2026.3 | 用于 skill 系统接入（可选） |

**Ollama 安装（推荐）：**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 安装嵌入模型（仅用于向量搜索，BM25 搜索不需要）
ollama pull nomic-embed-text

# 可选：LLM 模型（用于重排序和摘要）
ollama pull deepseek-v3.2
```

> ⚠️ 如果没有 Ollama，技能会降级到纯 BM25 搜索模式（仍然可用，只是没有语义搜索能力）

---

## 🔌 接入任意 AI Agent（通用方案）

### 步骤 1：启动 MCP Server

```bash
# 常驻运行（推荐 systemd）
node /path/to/unified-memory/src/index.js

# 或使用 mcporter 托管（自动保持连接）
mcporter run /path/to/unified-memory/src/index.js
```

### 步骤 2：连接到你的 Agent

**OpenClaw（已集成）：**
```json
// ~/.mcporter/mcporter.json（自动生成，无需手动配置）
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/root/.openclaw/workspace/skills/unified-memory/src/index.js"],
      "env": {},
      "lifecycle": "keep-alive"
    }
  }
}
```

**Claude Desktop（原生 MCP）：**
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/absolute/path/to/unified-memory/src/index.js"]
    }
  }
}
```

**Cursor / Windsurf / Coinexx：**
```json
// .cursor/mcp.json 或对应配置
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/index.js"]
    }
  }
}
```

**直接 HTTP API（无 MCP）：**
```bash
# 启动 REST API
node src/cli/index.js server --port 38421

# 调用
curl -X POST http://localhost:38421/search \
  -H "Content-Type: application/json" \
  -d '{"query":"刘总偏好","topK":5}'
```

---

## 🛠️ 配置

### 环境变量

```bash
# 可选，自定义路径（默认 ~/.openclaw/workspace/memory/）
export UNIFIED_MEMORY_DIR=~/.unified-memory

# Ollama 地址（默认 http://localhost:11434）
export OLLAMA_HOST=http://192.168.2.155:11434

# 向量模型（默认 nomic-embed-text）
export OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

### 配置文件（推荐）

```json
// ~/.openclaw/workspace/memory/config.json
{
  "ollamaUrl": "http://192.168.2.155:11434",
  "embedModel": "nomic-embed-text:latest",
  "llmModel": "deepseek-v3.2",
  "storageDir": "~/.openclaw/workspace/memory",
  "logLevel": "info"
}
```

---

## 🧪 快速测试

```bash
# 测试记忆存储
node src/cli/index.js store "测试记忆" --category fact --importance 0.8

# 测试搜索
node src/cli/index.js search "测试"

# 测试 API
curl http://localhost:38421/search?q=测试

# 运行测试套件
node run-tests.cjs
```

---

## 📦 86 个 MCP 工具总览

### 核心存储（9个）
`memory_store` · `memory_list` · `memory_search` · `memory_delete` · `memory_update` · `memory_get` · `memory_stats` · `memory_health` · `memory_export`

### 搜索增强（6个）
`memory_bm25` · `memory_vector` · `memory_mmr` · `memory_rerank_llm` · `memory_adaptive` · `memory_concurrent_search`

### Episode 会话记忆（6个）
`memory_episode_start` · `memory_episode_end` · `memory_episode_list` · `memory_episode_recall` · `memory_episode_merge` · `memory_episode_delete`

### Procedural / Rule 记忆（4个）
`memory_procedure_list` · `memory_procedure_add` · `memory_procedure_find` · `memory_procedure_delete` · `memory_rule_list` · `memory_rule_add` · `memory_rule_check` · `memory_rule_delete`

### 生命周期管理（8个）
`memory_autostore` · `memory_decay` · `memory_tier` · `memory_dedup` · `memory_refresh` · `memory_refresh_stats` · `memory_reminder_*` · `memory_qmd_search`

### 可观测性（5个）
`memory_trace` · `memory_metrics` · `memory_wal` · `memory_templates` · `memory_scope`

### HTTP API（4个）
`memory_http_start` · `memory_http_stop` · `memory_http_status` · `memory_http_health`

### Rerank 重排（2个）
`memory_search_reranked` · `memory_rerank`

### Chunking（1个）
`memory_chunk_list`

### 知识图谱（4个）
`memory_graph_entity_*` · `memory_graph_relation_*` · `memory_graph_query` · `memory_graph_stats`

### 主动与预测（7个）
`memory_proactive_*` · `memory_predict_*` · `memory_recommend`

### 偏好槽位（5个）
`memory_preference_slots` · `memory_preference_get/set/infer/explain`

### 版本控制（3个）
`memory_version_list` · `memory_version_diff` · `memory_version_timeline`

### RAG / 问答（3个）
`memory_qa` · `memory_extract` · `memory_summary`

### 质量与学习（5个）
`memory_feedback` · `memory_noise` · `memory_reflection` · `memory_lessons` · `memory_intent`

---

## 📁 数据文件

| 文件 | 说明 | 默认路径 |
|------|------|---------|
| 记忆存储 | JSON 格式持久化 | `~/.openclaw/workspace/memory/memories.json` |
| 知识图谱 | 实体-关系数据 | `~/.openclaw/workspace/memory/knowledge_graph.json` |
| Episodes | 会话片段 | `~/.openclaw/workspace/memory/episodes.json` |
| WAL 日志 | 预写日志 | `~/.openclaw/workspace/memory/wal.jsonl` |
| 配置 | Ollama/路径配置 | `~/.openclaw/workspace/memory/config.json` |

---

## 🔧 开发

```bash
# 安装依赖
npm install

# 启动 MCP Server（stdio 模式）
node src/index.js

# 启动 REST API
node src/cli/index.js server --port 38421

# CLI 工具
node src/cli/index.js --help

# 运行测试
node run-tests.cjs
```

---

## 📄 License

MIT

---

*更新: 2026-03-28 | v2.4.0*
