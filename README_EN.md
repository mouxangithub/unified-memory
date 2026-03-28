# 🧠 Unified Memory v2.0

> AI Agent Memory System — Multi-layered, Persistent, Proactive

---

<div align="center">

**🤖 This project was created by 小智 AI (OpenClaw)**  
Author: 刘选权 (ou_7b3a4352f86486ebdaf0de572093afb1)  
Powered by OpenClaw Agent framework, 86 MCP tools

[![GitHub stars](https://img.shields.io/github/stars/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green.svg)](https://nodejs.org/)

---

## 🌍 Documentation Index | 文档索引

| Language | README | Skill |
|----------|--------|-------|
| 🇨🇳 中文 | [README.md](README.md) | [SKILL.md](SKILL.md) |
| 🇺🇸 English | [README_EN.md](README_EN.md) ✅ | [SKILL_EN.md](SKILL_EN.md) ✅ |

---

## 🌟 Core Features

| Feature | Description |
|---------|-------------|
| 🔄 **Persistent Context** | No more re-explaining every session |
| 🔍 **Hybrid Search** | BM25 + Vector + RRF (100% local) |
| 💬 **Auto-Store** | Hooks mode, no manual calls needed |
| 📊 **User Insights** | Category distribution, tool usage analysis |
| 🧹 **Smart Forget** | Low-value memories auto-pruned |
| 🔗 **Knowledge Graph** | Entity extraction & relationship mapping |
| 🤝 **Multi-Agent** | Share memories across agents |
| 🏥 **Health Check** | Complete system health monitoring |

---

## 🚀 Quick Start

### Option 1: OpenClaw Skill Market (One-Click)

```bash
clawhub info unified-memory
clawhub install unified-memory
openclaw gateway restart
```

### Option 2: Curl Installer (Any AI Agent)

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### Option 3: Manual Install

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install --ignore-scripts
node src/index.js
```

---

## 📋 Prerequisites

| Dependency | Version | Notes |
|------------|---------|-------|
| Node.js | ≥ 22 | Latest LTS recommended |
| Ollama | ≥ 0.1.40 | Optional — auto-falls back to BM25-only if missing |
| OpenClaw | ≥ 2026.3 | For skill system integration (optional) |

```bash
# Install Ollama (optional)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text   # Embedding model for vector search
```

---

## 🔌 Integrate with Any AI Agent

### OpenClaw (Auto-Integrated)

```bash
openclaw gateway restart  # unified-memory auto-loads via mcporter
```

### Claude Desktop

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

### Cursor / Windsurf / Coinexx

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/index.js"]
    }
  }
}
```

### HTTP REST API (No MCP)

```bash
# Start REST server
node src/cli/index.js server --port 38421

# Search
curl -X POST http://localhost:38421/search \
  -H "Content-Type: application/json" \
  -d '{"query":"user preferences","topK":5}'

# List memories
curl http://localhost:38421/memory
```

---

## 🛠️ Configuration

```bash
# Environment variables (optional)
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

Or create `~/.openclaw/workspace/memory/config.json`:

```json
{
  "ollamaUrl": "http://192.168.2.155:11434",
  "embedModel": "nomic-embed-text:latest",
  "llmModel": "deepseek-v3.2",
  "storageDir": "~/.openclaw/workspace/memory"
}
```

---

## 🧪 Quick Test

```bash
# Store a memory
node src/cli/index.js store "Test memory" --category fact --importance 0.8

# Search
node src/cli/index.js search "test"

# Health check
curl http://localhost:38421/health

# Run tests
node run-tests.cjs
```

---

## 📦 86 MCP Tools Overview

### Core Storage (9)
`memory_store` · `memory_list` · `memory_search` · `memory_delete` · `memory_update` · `memory_get` · `memory_stats` · `memory_health` · `memory_export`

### Search (6)
`memory_bm25` · `memory_vector` · `memory_mmr` · `memory_rerank_llm` · `memory_adaptive` · `memory_concurrent_search`

### Episode Memory (6)
`memory_episode_start` · `memory_episode_end` · `memory_episode_list` · `memory_episode_recall` · `memory_episode_merge` · `memory_episode_delete`

### Procedural / Rule (8)
`memory_procedure_list/add/find/delete` · `memory_rule_list/add/check/delete`

### Lifecycle (8)
`memory_autostore` · `memory_decay` · `memory_tier` · `memory_dedup` · `memory_refresh` · `memory_reminder_*` · `memory_qmd_search`

### Observability (5)
`memory_trace` · `memory_metrics` · `memory_wal` · `memory_templates` · `memory_scope`

### HTTP API (4)
`memory_http_start/stop/status/health`

### Knowledge Graph (4)
`memory_graph_entity_*` · `memory_graph_relation_*` · `memory_graph_query` · `memory_graph_stats`

### Proactive & Prediction (7)
`memory_proactive_*` · `memory_predict_*` · `memory_recommend`

### Preference Slots (5)
`memory_preference_slots/get/set/infer/explain`

### RAG / QA (3)
`memory_qa` · `memory_extract` · `memory_summary`

### Quality & Learning (5)
`memory_feedback` · `memory_noise` · `memory_reflection` · `memory_lessons` · `memory_intent`

---

## 📁 Data Files

| File | Description | Default Path |
|------|-------------|--------------|
| Memories | JSON persistence | `~/.openclaw/workspace/memory/memories.json` |
| Knowledge Graph | Entity-relation data | `~/.openclaw/workspace/memory/knowledge_graph.json` |
| Episodes | Session fragments | `~/.openclaw/workspace/memory/episodes.json` |
| WAL Log | Write-ahead log | `~/.openclaw/workspace/memory/wal.jsonl` |
| Config | Ollama/path config | `~/.openclaw/workspace/memory/config.json` |

---

## 🔧 Development

```bash
# Install deps (only npm packages, peer deps provided by host)
npm install --ignore-scripts

# Start MCP Server (stdio)
node src/index.js

# Start REST API
node src/cli/index.js server --port 38421

# CLI help
node src/cli/index.js --help

# Run tests
node run-tests.cjs
```

---

## 📄 License

MIT

---

*Last updated: 2026-03-28 | v2.4.0*
