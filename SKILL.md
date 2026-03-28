---

<div align="center">

# 🧠 Unified Memory v2.5 (unified-memory)

> **🤖 Created by 小智 AI (OpenClaw)**  
> Author: 程序员小刘 (@mouxangithub)  
> Framework: OpenClaw Agent | Node.js ESM | 76 MCP Tools

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

## Feature Highlights | v2.5 新特性

| Feature | Description |
|---------|-------------|
| 🔄 **Scope Isolation** | LanceDB query-level scope filtering (AGENT/USER/TEAM/GLOBAL) |
| 🔍 **QMD Backend** | OpenClaw-native document search backend integration |
| ☁️ **Cloud Backup** | SuperMemory API + Custom REST dual-provider sync |
| 📈 **Weibull Decay** | Weibull-distributed forgetting curve (shape=1.5, scale=30 days) |
| 🔗 **Git Integration** | Git-backed versioned memory snapshots + git notes |
| 🏥 **Plugin Interface** | OpenClaw Memory Plugin spec-compliant (`memory_search`, `memory_get`, `memory_write`) |
| ⚡ **Phase 3 Complete** | All 76 tools registered, zero external DB dependency |

---

## Architecture

```
OpenClaw Agent
└── unified-memory (Node.js ESM)
    ├── MCP Server (63 core tools in index.js)
    ├── Plugin Interface (3 tools: memory_search/get/write)
    ├── QMD Search Backend (3 tools)
    ├── Git Integration (7 tools)
    ├── Cloud Backup (3 tools: SuperMemory + REST)
    ├── Weibull Decay (2 tools)
    ├── BM25 + Vector + RRF Hybrid Search
    ├── Weibull Time Decay (shape=1.5, scale=30d)
    ├── Multi-Scope Isolation (LanceDB query-level)
    ├── Write-Ahead Log (crash recovery)
    ├── HOT/WARM/COLD Tier Management
    ├── Knowledge Graph (entity extraction)
    ├── Intent Routing + Noise Filter
    ├── Preference Slots (structured user profiles)
    └── Self-Improving (reflection, dedup, lessons)
```

---

## Quick Start

```bash
# 1. Install via Clawhub (recommended)
clawhub install unified-memory

# 2. Verify
mcporter call unified-memory memory_health '{}'

# 3. Store first memory
mcporter call unified-memory memory_store '{"text": "Hello", "category": "general"}'

# 4. Search
mcporter call unified-memory memory_search '{"query": "hello"}'

# 5. Check stats
mcporter call unified-memory memory_stats '{}'
```

---

## 76 MCP Tools

### Core (9)
| Tool | Description |
|------|-------------|
| `memory_search` | Hybrid search: BM25 → Vector → Rerank → MMR → Decay → Scope → RRF |
| `memory_store` | Store memory (category/importance/tags/scope) |
| `memory_list` | List with pagination and filters |
| `memory_delete` | Delete memory |
| `memory_stats` | Statistics: count, category/importance distribution |
| `memory_health` | Health check: storage, vector engine, cache |
| `memory_insights` | User insights: category distribution, tool usage |
| `memory_export` | Export: JSON / Markdown / CSV |
| `memory_metrics` | System metrics monitoring |

### Search & Retrieval (6)
| Tool | Description |
|------|-------------|
| `memory_bm25` | Pure BM25 keyword search |
| `memory_vector` | Ollama vector semantic search (scope-aware) |
| `memory_mmr` | Maximal Marginal Relevance diversity selection |
| `memory_rerank_llm` | LLM Cross-Encoder reranking |
| `memory_adaptive` | Adaptive skip for non-retrieval queries |
| `memory_concurrent_search` | Parallel multi-query search |

### Plugin Interface — OpenClaw Spec (3) ⭐ NEW
| Tool | Description |
|------|-------------|
| `phase3_memory_search` | Plugin-spec search with scope isolation |
| `phase3_memory_get` | Plugin-spec memory retrieval |
| `phase3_memory_write` | Plugin-spec memory write |

### QMD Search Backend (3) ⭐ NEW
| Tool | Description |
|------|-------------|
| `memory_qmd_query` | Query QMD collection (workspace/daily-logs/projects) |
| `memory_qmd_status` | QMD index status and collections |
| `memory_qmd_search2` | QMD hybrid search with scope filtering |

### Git Integration (7) ⭐ NEW
| Tool | Description |
|------|-------------|
| `memory_git_init` | Initialize git repository for versioned memory |
| `memory_git_sync` | Sync all memories to git commit |
| `memory_git_history` | View memory commit history |
| `memory_git_note` | Add git note to a memory |
| `memory_git_pull` | Pull latest from remote |
| `memory_git_push` | Push to remote |
| `memory_git_status` | Git working tree status |

### Cloud Backup (3) ⭐ NEW
| Tool | Description |
|------|-------------|
| `memory_cloud_sync` | Sync memories to cloud (SuperMemory or Custom REST) |
| `memory_cloud_push` | Push memories to cloud |
| `memory_cloud_pull` | Pull memories from cloud |

### Weibull Decay (2) ⭐ NEW
| Tool | Description |
|------|-------------|
| `memory_decay_stats` | Decay statistics per memory |
| `memory_decay_strength` | Adjust decay strength multiplier |

### Proactive & Prediction (6)
| Tool | Description |
|------|-------------|
| `memory_proactive_start` | Start proactive recall timer |
| `memory_proactive_stop` | Stop proactive recall |
| `memory_proactive_status` | Proactive recall status |
| `memory_proactive_recall` | Inject memories into context |
| `memory_proactive_trigger` | Manual trigger recall |
| `memory_proactive_care` | Proactive care trigger |

### Knowledge Graph (5)
| Tool | Description |
|------|-------------|
| `memory_graph_entity` | Entity extraction and management |
| `memory_graph_relation` | Entity relation management |
| `memory_graph_query` | Graph query (entity relationship path) |
| `memory_graph_stats` | Graph statistics |
| `memory_graph_add` | Add entity to graph |

### RAG & QA (3)
| Tool | Description |
|------|-------------|
| `memory_qa` | RAG question answering |
| `memory_qmd_get` | Get local file content via QMD |
| `memory_qmd_list` | List QMD indexed files |

### Self-Improving (8)
| Tool | Description |
|------|-------------|
| `memory_reflection` | Session reflection and insight extraction |
| `memory_noise` | Noise pattern learning |
| `memory_intent` | Intent classification |
| `memory_extract` | Structured entity extraction |
| `memory_dedup` | Deduplication merge |
| `memory_lessons` | Lesson system (learn from errors) |
| `memory_feedback` | User feedback integration |
| `memory_rollback` | WAL-based rollback |

### Preference & Inference (6)
| Tool | Description |
|------|-------------|
| `memory_preference_slots` | User preference slots (structured KV) |
| `memory_preference_get` | Get preference value with full metadata |
| `memory_preference_set` | Set preference value with source/confidence |
| `memory_preference_infer` | Infer preference from conversation |
| `memory_preference_explain` | Explain preference source |
| `memory_inference` | Inference engine |

### Versioning & Templates (4)
| Tool | Description |
|------|-------------|
| `memory_version_list` | Memory version history |
| `memory_version_diff` | Diff between two versions |
| `memory_version_timeline` | Version timeline visualization |
| `memory_templates` | Memory templates |

### Monitoring & Ops (5)
| Tool | Description |
|------|-------------|
| `memory_wal` | Write-Ahead Log operations |
| `memory_tier` | HOT/WARM/COLD tier management |
| `memory_decay` | Decay management |
| `memory_trace` | Search trace |
| `memory_reminder_*` | Reminder CRUD |

### QMD File Access (2)
| Tool | Description |
|------|-------------|
| `memory_qmd_vsearch` | QMD vector search |
| `memory_scope` | Scope normalization and filtering |

### Recommend & Summary (4)
| Tool | Description |
|------|-------------|
| `memory_recommend` | Recommend memories based on context |
| `memory_summary` | Generate memory summary |
| `memory_autostore` | Auto-store mode toggle |
| `memory_id` | Get memory ID |

---

## Scope Levels

| Level | Description | Access |
|-------|-------------|--------|
| `AGENT` | Per-agent private memory | Agent only |
| `USER` | Per-user memory | User scope and above |
| `TEAM` | Team-shared memory | Team scope and above |
| `GLOBAL` | Public to all | Everyone |

Scope filtering is enforced at **LanceDB query level** (not post-filter), ensuring true multi-tenant isolation.

---

## Storage Backend

- **Primary**: JSON file (`~/.openclaw/workspace/memory/memories.json`)
- **Vector**: Embedded LanceDB (`~/.unified-memory/vector.lance`)
- **Embedding**: Ollama (`nomic-embed-text-v1.5`, 768-dim)
- **No external DB required** — zero external database dependency

---

## Version History

| Version | Date | Highlights |
|---------|------|-----------|
| v2.5.0 | 2026-03-28 | Phase 3: plugin interface, QMD backend, git, cloud, Weibull |
| v2.4.0 | 2026-03-27 | Phase 2: 86 tools, episode/graph/proactive/recommend |
| v2.1.0 | 2026-03-27 | 33 tools, tier/wal/noise/intent, ESM rewrite |
| v2.0.0 | 2026-03-26 | Node.js ESM rewrite, BM25+Vector+RRF |
| v1.x | 2026-03-25 | Python prototype |

---

## Installation

```bash
# Clawhub (recommended)
clawhub install unified-memory

# Curl installer
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash

# Manual
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text-v1.5` | Embedding model |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | Memory storage path |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB path |

---

## Engine Requirements

- **Node.js**: ≥ 22
- **Ollama**: ≥ 0.1.40 (optional; BM25 fallback if missing)
- **OpenClaw**: ≥ 2026.3 (for skill system integration)
