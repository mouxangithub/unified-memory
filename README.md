# 🧠 Unified Memory v3.x

> AI Agent Memory System — Multi-layered, Persistent, Proactive

**Author**: 程序员小刘 (@mouxangithub)  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**Registry**: `clawhub install unified-memory`  
**Framework**: OpenClaw Agent | Node.js ESM | 51 MCP Tools | Web Dashboard v3.x

---

## 📖 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [51 MCP Tools](#28-mcp-tools)
- [Quick Start](#quick-start)
- [Scope Isolation](#scope-isolation)
- [Development](#development)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| 🔄 **Persistent Context** | No more re-explaining every session |
| 🔍 **Hybrid Search** | BM25 + Vector + RRF (configurable: LanceDB / Ollama / none) |
| 💬 **Auto-Store** | Hooks mode, no manual calls needed |
| 🏷️ **Scope Isolation** | AGENT / USER / TEAM / GLOBAL |
| 📈 **Weibull Decay** | Human-like forgetting curve (shape=1.5, scale=30 days) |
| 🔗 **Git Versioning** | Git-backed memory snapshots and notes |
| ☁️ **Cloud Backup** | Local Git + Cloud backup dual mode |
| 📊 **Knowledge Graph** | Entity extraction and relationship mapping |
| 🏥 **Health Check** | Complete system health monitoring |
| ⚡ **Pluggable Architecture** | LanceDB / Ollama / none — choose what you need |

---

## Architecture

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 28 core tools (unified action-parameter entry points)
    ├── Storage layer: JSON + WAL (crash-recoverable)
    ├── Vector layer (pluggable):
    │   ├── LanceDB (default, zero-config)
    │   ├── Ollama Embedding (optional)
    │   └── none (BM25-only mode)
    ├── LLM layer (pluggable):
    │   ├── Ollama (default, local)
    │   └── none (rule-based fallback)
    └── Tier management: HOT / WARM / COLD
```

**Configuration Modes**:

| Mode | Vector Engine | Embedding | LLM |
|------|-------------|-----------|-----|
| Default (Recommended) | LanceDB | Ollama | Ollama |
| Lightweight | none | none | none |
| Local Vector | LanceDB | Ollama | none |
| Cloud Managed | LanceDB Cloud | LanceDB managed | Ollama/OpenAI |

---

## Installation

### Option 1 — Clawhub (Recommended)
```bash
clawhub install unified-memory
openclaw gateway restart
```

### Option 2 — Curl Installer (auto-installs LanceDB)
```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### Option 3 — Manual
```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## Configuration

See [docs/CONFIG.md](docs/CONFIG.md) for full details. Core settings:

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | Memory storage path |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB path |
| `LANCEDB_API_KEY` | (none) | LanceDB Cloud API Key (optional) |
| `VECTOR_ENGINE` | `lancedb` | Vector engine: lancedb / ollama / none |
| `LLM_PROVIDER` | `ollama` | LLM provider: ollama / openai / none |

---

## 51 MCP Tools

### Storage Core (6)
| Tool | Description |
|------|-------------|
| `memory_store` | Store memory (category/importance/tags/scope) |
| `memory_get` | Get single memory |
| `memory_list` | Paginated memory list |
| `memory_delete` | Delete memory |
| `memory_search` | Hybrid search: BM25 → Vector → Rerank → MMR |
| `memory_import` | Import memories from JSON |

### Unified Entry Points (10, action parameter)
| Tool | Actions |
|------|---------|
| `memory_reminder` | add / list / cancel |
| `memory_preference` | get / set / infer / explain / stats / slots |
| `memory_version` | list / diff / restore |
| `memory_tier` | status / migrate / compress / assign / partition / redistribute |
| `memory_proactive` | status / trigger / start / stop |
| `memory_proactive_care` | status / care / insights |
| `memory_proactive_recall` | status / recall / analyze |
| `memory_qmd` | search / get / vsearch / list / status |
| `memory_engine` | bm25 / embed / search / mmr / rerank |
| `memory_graph` | entity / relation / query / stats / add / delete |

### Search & Retrieval (7)
`memory_bm25` · `memory_vector` · `memory_scope` · `memory_concurrent_search` · `memory_dedup` · `memory_noise` · `memory_mmr`

### Analysis & Management (16)
`memory_trace` · `memory_metrics` · `memory_decay` · `memory_extract` · `memory_reflection` · `memory_intent` · `memory_wal` · `memory_adaptive` · `memory_autostore` · `memory_auto_extract` · `memory_health` · `memory_insights` · `memory_predict` · `memory_feedback` · `memory_stats` · `memory_lesson`

### Cloud & System (12)
`memory_cloud_backup` · `memory_cloud_restore` · `memory_export` · `memory_import` · `memory_clone` · `memory_share` · `memory_scope` · `memory_intent` · `memory_insights` · `memory_health` · `memory_predict` · `memory_feedback`

*(Exact tool list may vary slightly by version — run `mcporter call unified-memory memory_health` to see tools for your install)*

---

## Quick Start

```bash
# Verify installation
mcporter call unified-memory memory_health '{}'

# Store a memory
mcporter call unified-memory memory_store '{"text": "Liu prefers concise communication", "category": "preference", "scope": "USER"}'

# Search memories
mcporter call unified-memory memory_search '{"query": "Liu communication style", "scope": "USER"}'

# Check stats
mcporter call unified-memory memory_stats '{}'

# Add a reminder
mcporter call unified-memory memory_reminder '{"action": "add", "content": "meeting", "minutes": 30}'

# View knowledge graph
mcporter call unified-memory memory_graph '{"action": "stats"}'
```

---

## Scope Isolation

| Scope | Access |
|-------|--------|
| `AGENT` | Single agent private |
| `USER` | Per-user, excludes AGENT |
| `TEAM` | Team-shared, excludes USER/AGENT |
| `GLOBAL` | Public to all |

```bash
mcporter call unified-memory memory_search '{"query": "project plans", "scope": "USER"}'
```

---

## Development

```bash
# Install deps
npm install --ignore-scripts

# Start MCP server
node src/index.js

# CLI help
node src/cli/index.js --help

# Run tests
node run-tests.cjs

# Web dashboard
node src/webui/dashboard.js
```

---

## File Structure

```
src/
├── index.js          # MCP server (28 tools)
├── storage.js        # JSON persistence + WAL
├── vector_lancedb.js # LanceDB vector backend
├── bm25.js           # BM25 search engine
├── graph/            # Knowledge graph
├── tools/            # Tool wrappers
└── webui/            # Web dashboard
docs/
└── CONFIG.md         # Detailed configuration guide
```

---

## License

MIT

*Last updated: 2026-03-29 | v3.x*
