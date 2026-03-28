# 🧠 Unified Memory v2.7

> AI Agent Memory System — Multi-layered, Persistent, Proactive

**Author**: 程序员小刘 (@mouxangithub)  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**Registry**: `clawhub install unified-memory`  
**Framework**: OpenClaw Agent | Node.js ESM | 76 MCP Tools | Web Dashboard v2.7

---

## 📖 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Option 1 — Clawhub (Recommended)](#option-1--clawhub-recommended)
  - [Option 2 — Curl Installer](#option-2--curl-installer)
  - [Option 3 — Manual](#option-3--manual)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Phase 3 New Tools](#phase-3-new-tools)
- [Development](#development)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| 🔄 **Persistent Context** | No more re-explaining every session |
| 🔍 **Hybrid Search** | BM25 + Vector + RRF (100% local, Ollama-powered) |
| 💬 **Auto-Store** | Hooks mode, no manual calls needed |
| 🏷️ **Scope Isolation** | AGENT / USER / TEAM / GLOBAL — enforced at LanceDB query level |
| 📈 **Weibull Decay** | Human-like forgetting curve (shape=1.5, scale=30 days) |
| 🔗 **Git Versioning** | Git-backed memory snapshots and notes |
| ☁️ **Cloud Backup** | SuperMemory API + Custom REST dual sync |
| 📊 **Knowledge Graph** | Entity extraction and relationship mapping |
| 🏥 **Health Check** | Complete system health monitoring |

---

## Requirements

| Dependency | Version | Notes |
|------------|---------|-------|
| Node.js | ≥ 22 | ESM required |
| Ollama | ≥ 0.1.40 | Optional — falls back to BM25-only if missing |
| OpenClaw | ≥ 2026.3 | For skill system / Clawhub integration |

---

## Installation

### Option 1 — Clawhub (Recommended)
```bash
clawhub install unified-memory
openclaw gateway restart
```

### Option 2 — Curl Installer
```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### Option 3 — Manual
```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## Quick Start

```bash
# Verify installation
mcporter call unified-memory memory_health '{}'

# Store a memory
mcporter call unified-memory memory_store '{"text": "刘总喜欢简洁直接的沟通风格", "category": "preference", "scope": "USER"}'

# Search memories
mcporter call unified-memory memory_search '{"query": "刘总沟通风格", "scope": "USER"}'

# Check stats
mcporter call unified-memory memory_stats '{}'
```

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text-v1.5` | Embedding model |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | Memory storage path |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB path |

---

## Architecture

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 63 core tools (index.js)
    ├── Phase 3 additions:
    │   ├── plugin/         — OpenClaw Memory Plugin interface
    │   ├── search/         — QMD backend integration
    │   ├── integrations/   — Git + Cloud backup
    │   └── decay/          — Weibull decay model
    ├── BM25 + Vector + RRF hybrid search
    ├── LanceDB (embedded, zero-config)
    ├── WAL + tier management
    └── Knowledge graph + preference slots
```

---

## Phase 3 New Tools

### Plugin Interface (3)
`phase3_memory_search` · `phase3_memory_get` · `phase3_memory_write`

### Git Integration (7)
`memory_git_init` · `memory_git_sync` · `memory_git_history` · `memory_git_note` · `memory_git_pull` · `memory_git_push` · `memory_git_status`

### Cloud Backup (3)
`memory_cloud_sync` · `memory_cloud_push` · `memory_cloud_pull`

### Weibull Decay (2)
`memory_decay_stats` · `memory_decay_strength`

### QMD Backend (3)
`memory_qmd_query` · `memory_qmd_status` · `memory_qmd_search2`

---

## Scope Isolation

Scope filtering is enforced at **LanceDB query level** (not post-filter), so each scope sees only its own vectors:

| Scope | Access |
|-------|--------|
| `AGENT` | Single agent private |
| `USER` | Per-user, excludes AGENT |
| `TEAM` | Team-shared, excludes USER/AGENT |
| `GLOBAL` | Public to all |

```bash
# Search within USER scope only
mcporter call unified-memory memory_search '{"query": "project plans", "scope": "USER"}'
```

---

## Development

```bash
# Install deps (peer deps provided by host)
npm install --ignore-scripts

# Start MCP server (stdio)
node src/index.js

# Start REST API
node src/cli/index.js server --port 38421

# CLI help
node src/cli/index.js --help

# Run tests
node run-tests.cjs
```

---

## File Structure

| File | Description |
|------|-------------|
| `src/index.js` | MCP server (63 core tools) |
| `src/plugin/` | OpenClaw Memory Plugin interface |
| `src/search/` | QMD search backend |
| `src/integrations/` | Git + Cloud backup |
| `src/decay/` | Weibull decay model |
| `src/core/` | BM25, vector, fusion, tier, dedup, etc. |
| `src/cli/` | CLI tools |
| `src/webui/dashboard.js` | Web monitoring dashboard (v2.7) |
| `wal/` | Write-ahead log |
| `memories.json` | Memory persistence |

---

## Web UI Dashboard (v2.7)

A real-time monitoring dashboard for memory system health and statistics.

```bash
# Start dashboard
npm run dashboard

# Or with custom port
npm run dashboard:port -- --port=3850
```

**Access**: http://localhost:3849

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/stats` | GET | Memory statistics (categories, tiers, scopes, tags) |
| `/api/health` | GET | System health (Ollama, LanceDB, storage) |
| `/api/memories` | GET | All memories |
| `/api/export` | GET | Export memories as JSON file |
| `/api/manage` | POST | Management actions (cleanup) |

**Dashboard Features**:
- Real-time search stats (total, 7d growth, access counts)
- Memory distribution by category, scope, tier, importance, tags
- System health monitoring with color-coded status
- 14-day memory growth trend chart
- Cleanup old memories (30 days threshold)
- Auto-refresh every 5 seconds

---

## License

MIT

*Last updated: 2026-03-28 | v2.6.0*
