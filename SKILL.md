---

<div align="center">

# 🧠 Unified Memory v3.x (unified-memory)

> **🤖 Created by 小智 AI (OpenClaw)**  
> Author: 程序员小刘 (@mouxangithub)  
> Framework: OpenClaw Agent | Node.js ESM | 97 MCP Tools

**Project Path**: `/root/.openclaw/workspace/skills/unified-memory/`  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**Registry**: `clawhub install unified-memory`

---

## 🌍 Documentation | 文档索引

| Language | README | Skill |
|----------|--------|-------|
| 🇨🇳 中文 | [README_CN.md](README_CN.md) | [SKILL_CN.md](SKILL_CN.md) |
| 🇺🇸 English ✅ | [README.md](README.md) | [SKILL.md](SKILL.md) |

---

## Feature Highlights | v3.x 新特性

| Feature | Description |
|---------|-------------|
| 🔄 **Persistent Context** | Memory persists across sessions — no need to re-explain |
| 🔍 **Hybrid Search** | BM25 + Vector + RRF fusion (configurable LanceDB/Ollama/none) |
| 💬 **Auto-Store** | Hooks mode — no manual storage calls needed |
| 🏷️ **Scope Isolation** | AGENT / USER / TEAM / GLOBAL multi-tenant isolation |
| 📈 **Weibull Decay** | Human forgetting curve (shape=1.5, scale=30 days) |
| 🔗 **Git Versioning** | Git-backed memory snapshots + git notes |
| ☁️ **Cloud Backup** | Local Git + cloud backup dual-mode |
| 📊 **Knowledge Graph** | Entity extraction and relation mapping |
| 🏥 **Health Check** | Complete system health monitoring |
| ⚡ **Pluggable Architecture** | LanceDB / Ollama / none — configure as needed |

---

## Architecture

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 28 core tools (unified action-parameter interface)
    ├── Storage layer: JSON + WAL (crash-recoverable)
    ├── Vector layer (pluggable):
    │   ├── LanceDB (default, zero-config)
    │   ├── Ollama Embedding (optional)
    │   └── none (BM25-only mode)
    ├── LLM layer (pluggable):
    │   ├── Ollama (default, local)
    │   └── none (fallback to rule-based mode)
    └── Tier management: HOT / WARM / COLD
```

**Configuration Modes**:

| Mode | Vector Engine | Embedding | LLM |
|------|-------------|-----------|-----|
| Default (recommended) | LanceDB | Ollama | Ollama |
| Lightweight | none | none | none |
| Local Vector | LanceDB | Ollama | none |
| Cloud Managed | LanceDB Cloud | LanceDB managed | Ollama/OpenAI |

---

## Quick Start

```bash
# 1. Install via Clawhub (recommended)
clawhub install unified-memory

# 2. Verify installation
mcporter call unified-memory memory_health '{}'

# 3. Store first memory
mcporter call unified-memory memory_store '{"text": "Hello", "category": "general", "scope": "USER"}'

# 4. Search
mcporter call unified-memory memory_search '{"query": "hello", "scope": "USER"}'

# 5. Check stats
mcporter call unified-memory memory_stats '{}'
```

---

## 97 MCP Tools

### Storage Core (5)
| Tool | Description |
|------|-------------|
| `memory_store` | Store memory (category/importance/tags/scope) |
| `memory_get` | Retrieve a single memory |
| `memory_list` | Paginated memory listing |
| `memory_delete` | Delete a memory |
| `memory_search` | Hybrid search: BM25 → Vector → Rerank → MMR |

### Unified Entry — Action-Parameter Tools (8)
| Tool | Actions |
|------|---------|
| `memory_reminder` | add / list / cancel |
| `memory_preference` | get / set / infer / explain / stats / slots |
| `memory_version` | list / diff / restore |
| `memory_tier` | status / migrate / compress |
| `memory_proactive` | status / trigger / start / stop |
| `memory_proactive_care` | — |
| `memory_proactive_recall` | — |
| `memory_qmd` | search / get / vsearch / list / status |
| `memory_engine` | bm25 / embed / search / mmr / rerank |
| `memory_graph` | entity / relation / query / stats / add / delete |

### Search Enhancement (4)
`memory_bm25` · `memory_vector` · `memory_scope` · `memory_concurrent_search`

### Session & Transcript (2)
`memory_session` · `memory_transcript`

### Cognitive & Lanes (2)
`memory_cognitive` · `memory_lanes`

### Analysis & Management (9)
`memory_trace` · `memory_metrics` · `memory_noise` · `memory_decay` · `memory_dedup` · `memory_extract` · `memory_reflection` · `memory_intent` · `memory_wal`

### Cloud & System (6)
`memory_cloud_backup` · `memory_cloud_restore` · `memory_cloud_backup_api` · `memory_export` · `memory_adaptive` · `memory_autostore` · `memory_auto_extract` · `memory_health` · `memory_insights` · `memory_predict` · `memory_feedback`

### Budget & Revision (2)
`memory_budget` · `memory_revision`

### Git & Persistence (2)
`memory_git_notes` · `memory_git`

---

## Scope Levels

| Level | Access |
|-------|--------|
| `AGENT` | Single agent private |
| `USER` | Single user, excludes AGENT |
| `TEAM` | Team shared, excludes USER/AGENT |
| `GLOBAL` | Public to all |

---

## Storage Backend

- **Primary**: JSON file (`~/.openclaw/workspace/memory/memories.json`)
- **Vector**: Embedded LanceDB (`~/.unified-memory/vector.lance`)
- **Embedding**: Ollama (`nomic-embed-text`, 768-dim)
- **Write-Ahead Log**: WAL for crash recovery
- **No external DB required** — zero external database dependency

---

## Configuration

Full configuration guide: [docs/CONFIG.md](docs/CONFIG.md)

| Env Var | Default | Description |
|---------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | Memory storage path |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB path |
| `VECTOR_ENGINE` | `lancedb` | Vector engine: lancedb / ollama / none |
| `LLM_PROVIDER` | `ollama` | LLM provider: ollama / openai / none |

---

## Version History

| Version | Date | Highlights |
|---------|------|-----------|
| v3.7.0 | 2026-03-30 | 97 tools: +session_state, +transcript_manager, +git_notes, +revision_manager, +budget, +cognitive_scheduler, +lanes_manager, +cloud_backup_api |
| v3.6.1 | 2026-03-29 | 89 tools: 28 unified tools, pluggable architecture, CONFIG.md |
| v2.7.0 | 2026-03-28 | Web UI Dashboard, Identity memory type |
| v2.6.0 | 2026-03-28 | Phase 3: plugin interface, QMD backend, git, cloud |
| v2.4.0 | 2026-03-27 | 86 tools, episode/graph/proactive/recommend |
| v2.1.0 | 2026-03-27 | 33 tools, tier/wal/noise/intent, ESM rewrite |

---

## Installation

```bash
# Clawhub (recommended)
clawhub install unified-memory
openclaw gateway restart

# Curl installer
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash

# Manual
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## Development

```bash
# Install dependencies
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

## Engine Requirements

- **Node.js**: ≥ 22
- **Ollama**: ≥ 0.1.40 (optional; BM25 fallback if missing)
- **OpenClaw**: ≥ 2026.3 (for skill system integration)
