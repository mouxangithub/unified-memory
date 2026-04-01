---priority: critical
title: Unified Memory v4.0.0
---

<!-- Language Toggle / 语言切换 -->
[English](./README.md) · **[中文](./README_CN.md)** · [日本語](./README_JA.md)

<!-- Documentation Navigation / 文档导航 -->
📚 **Docs**: [Overview](#overview) · [Features](#features) · [Architecture](#architecture) · [Installation](#installation) · [API](#152-mcp-tools-organized-by-category) · [Examples](#quick-start) · [Index](#-complete-documentation-index)

---

> AI Agent Memory System — Multi-layered, Persistent, Proactive

**Author**: 程序员小刘 (@mouxangithub)  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**Registry**: `clawhub install unified-memory`  
**Framework**: OpenClaw Agent | Node.js ESM | 152 MCP Tools | Web Dashboard v3.x  
**Version**: 3.8.4 (2026-03-30)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [152 MCP Tools](#152-mcp-tools-organized-by-category)
- [Quick Start](#quick-start)
- [Scope Isolation](#scope-isolation)
- [Development](#development)
- [License](#license)
- [Documentation Index](#documentation-index)

---

## Overview (v4.0.0)

Unified Memory is the most feature-rich memory system MCP server for OpenClaw agents. It provides persistent context, hybrid search (BM25 + Vector + RRF), Weibull decay, WAL-based crash recovery, evidence chains, transcript-first architecture, lane memory, token budget enforcement, and deep scope isolation — all in pure Node.js ESM with zero Python dependencies.

<!-- zh -->
Unified Memory 是 OpenClaw Agent 领域功能最丰富的记忆系统 MCP 服务器。它提供持久化上下文、混合搜索（BM25 + 向量 + RRF 融合）、Weibull 衰减、WAL 崩溃恢复、证据链、Transcript-First 架构、泳道记忆、Token 预算强制执行以及深度的 Scope 隔离 —— 全部使用纯 Node.js ESM 实现，零 Python 依赖。
-->

---

## Features

### Core Memory Capabilities

#### 🔄 Persistent Context | 持久化上下文

Every conversation builds on previous sessions. Unified Memory eliminates the need to re-explain context by maintaining a continuously growing, searchable memory store that survives session restarts and compaction events.

<!-- zh -->
每次对话都建立在上一次会话的基础上。Unified Memory 通过维护一个持续增长、可搜索的记忆库来消除重复解释上下文的需要，记忆在会话重启和压缩事件中持久保存。
-->

#### 🔍 Hybrid Search | 混合搜索

The search pipeline combines three retrieval strategies for maximum recall and precision:

1. **BM25** — Traditional keyword sparse retrieval (pure Node.js, no external dependencies)
2. **Vector** — Dense semantic embeddings via LanceDB or Ollama
3. **RRF (Reciprocal Rank Fusion)** — Fuses BM25 and vector results with configurable weighting

MMR (Maximal Marginal Relevance) reranking is applied for diversity. The entire pipeline is pluggable — use LanceDB, Ollama, or BM25-only depending on your infrastructure.

<!-- zh -->
搜索管道结合三种检索策略以最大化召回率和精度：

1. **BM25** — 传统关键词稀疏检索（纯 Node.js，无外部依赖）
2. **Vector** — 通过 LanceDB 或 Ollama 的密集语义嵌入
3. **RRF (倒数排名融合)** — 以可配置权重融合 BM25 和向量结果

MMR（最大边际相关性）重排用于提升多样性。整个管道是可插拔的 —— 可根据基础设施选择使用 LanceDB、Ollama 或纯 BM25 模式。
-->

#### 📈 Weibull Decay | Weibull 衰减

Memories decay over time using a Weibull distribution (shape=1.5, scale=30 days) that models human forgetting curves. Importance scores and access frequency modulate the decay rate — critical memories last longer, stale memories fade away.

<!-- zh -->
记忆使用 Weibull 分布（shape=1.5，scale=30天）随时间衰减，模拟人类遗忘曲线。重要性评分和访问频率调节衰减速率 —— 关键记忆持续更久，陈旧记忆逐渐消失。
-->

#### 💾 WAL Protocol | WAL 协议

Write-Ahead Log (WAL) ensures every memory operation is durable before acknowledgment. On crash, the WAL is replayed automatically to recover all committed data with checksum validation.

<!-- zh -->
预写日志（WAL）确保每个记忆操作在确认前都是持久的。崩溃时，WAL 自动重放以恢复所有已提交的数据，并进行校验和验证。
-->

#### 🏷️ Scope Isolation | Scope 隔离

Four-tier isolation ensures memory access is always appropriate:

| Scope | Access |
|-------|--------|
| `AGENT` | Single agent private |
| `USER` | Per-user, excludes AGENT |
| `TEAM` | Team-shared, excludes USER/AGENT |
| `GLOBAL` | Public to all |

<!-- zh -->
四层隔离确保记忆访问始终恰当：

| Scope | 访问权限 |
|-------|---------|
| `AGENT` | 单 Agent 私有 |
| `USER` | 单用户，排除 AGENT |
| `TEAM` | 团队共享，排除 USER/AGENT |
| `GLOBAL` | 全局公开 |
-->

#### 📊 Knowledge Graph | 知识图谱

Entity extraction and relationship mapping from conversations builds an interconnected knowledge network. Query relationships, find related entities, and navigate memory through semantic connections.

<!-- zh -->
从对话中提取实体和关系映射，构建互联的知识网络。通过语义连接查询关系、查找相关实体和导航记忆。
-->

#### 🔗 Evidence Chain | 证据链

Every memory carries provenance metadata: source (transcript/message/manual/inference), confidence score (0-1), and evidence chain tracking. Recall can be filtered by evidence quality, enabling more trustworthy memory retrieval.

<!-- zh -->
每条记忆都携带来源元数据：来源（transcript/message/manual/inference）、置信度评分（0-1）和证据链追踪。召回可以按证据质量过滤，实现更可靠的记忆检索。
-->

#### 📝 Transcript-First Architecture | Transcript-First 架构

Transcripts serve as the single source of truth. Memory is rebuilt from transcripts rather than stored directly, ensuring evidence chains are always intact and memories can be regenerated from raw conversation data.

<!-- zh -->
Transcript 作为唯一的真实来源。记忆从 transcript 重建而非直接存储，确保证据链始终完整，记忆可以从原始对话数据重新生成。
-->

#### 🏊 Lane Memory | 泳道记忆

Parallel memory swim lanes (primary/task/background/archive) allow isolation of different conversation threads. Custom lanes can be created for long-running tasks or project-specific contexts.

<!-- zh -->
并行记忆泳道（primary/task/background/archive）允许不同对话线程的隔离。可以为长期运行的任务或项目特定上下文创建自定义泳道。
-->

#### 💰 Token Budget | Token 预算

Fine-grained token allocation with hard limits (95%), auto-compaction (85%), and warning thresholds (70%). Type and priority-based allocation prevents any single memory category from consuming the entire budget.

<!-- zh -->
细粒度 Token 分配，包含硬限制（95%）、自动压缩（85%）和警告阈值（70%）。基于类型和优先级的分配防止任何单一记忆类别消耗整个预算。
-->

#### 🔄 Auto Organization | 自动整理

Automatic tier migration (HOT/WARM/COLD), compression based on age and importance, and archival of memories older than 365 days keep the memory system lean and efficient.

<!-- zh -->
自动层级迁移（HOT/WARM/COLD）、基于年龄和重要性的压缩、以及超过 365 天的记忆归档，保持记忆系统精简高效。
-->

#### 🔀 Revision Lifecycle | 修订生命周期

Memories progress through lifecycle stages (draft → review → approved → archived) with enhanced conflict detection and automatic merging for concurrent edits.

<!-- zh -->
记忆经历生命周期阶段（draft → review → approved → archived），具有增强的冲突检测和并发编辑自动合并功能。
-->

#### ⚡ Pluggable Architecture | 可插拔架构

Configure vector engines and LLM providers to match your infrastructure:

| Mode | Vector Engine | Embedding | LLM |
|------|-------------|-----------|-----|
| Default (Recommended) | LanceDB | Ollama | Ollama |
| Lightweight | none | none | none |
| Local Vector | LanceDB | Ollama | none |
| Cloud Managed | LanceDB Cloud | LanceDB managed | Ollama/OpenAI |

<!-- zh -->
配置向量引擎和 LLM 提供者以匹配您的基础设施：
-->

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
    ├── Evidence layer: source tracking + confidence scoring
    ├── Tier management: HOT / WARM / COLD
    ├── Lane system: parallel swim lanes
    ├── Token budget: hard limits + auto-compaction
    └── Web UI: dashboard + health monitoring
```

**Source Files** (`src/`):

| File | Purpose |
|------|---------|
| `index.js` | MCP server entry — 28 unified action-parameter tools |
| `storage.js` | JSON persistence + WAL integration |
| `wal.js` | Write-Ahead Log protocol |
| `evidence.js` | Evidence chain tracking |
| `bm25.js` | BM25 sparse retrieval engine |
| `vector_lancedb.js` | LanceDB vector backend |
| `decay.js` | Weibull decay scheduling |
| `graph/` | Knowledge graph entities + relations |
| `cognitive_scheduler.js` | Proactive recall scheduler |
| `session_state.js` | Hot context management |
| `organize.js` | Auto tier migration + compression |
| `transcript_first.js` | Transcript rebuild pipeline |
| `lane_manager_enhanced.js` | Lane memory system |
| `token_budget_enhanced.js` | Token budget enforcement |
| `evidence_recall.js` | Evidence-weighted retrieval |
| `revision_manager_enhanced.js` | Revision lifecycle management |
| `webui/dashboard.html` | Web dashboard UI |

For detailed technical documentation, see [SKILL.md](SKILL.md).

<!-- zh -->
**源文件**（`src/`）：

| 文件 | 功能 |
|------|------|
| `index.js` | MCP 服务器入口 — 28 个统一 action 参数工具 |
| `storage.js` | JSON 持久化 + WAL 集成 |
| `wal.js` | 预写日志协议 |
| `evidence.js` | 证据链追踪 |
| `bm25.js` | BM25 稀疏检索引擎 |
| `vector_lancedb.js` | LanceDB 向量后端 |
| `decay.js` | Weibull 衰减调度 |
| `graph/` | 知识图谱实体 + 关系 |
| `cognitive_scheduler.js` | 主动召回调度器 |
| `session_state.js` | 热上下文管理 |
| `organize.js` | 自动层级迁移 + 压缩 |
| `transcript_first.js` | Transcript 重建管道 |
| `lane_manager_enhanced.js` | 泳道记忆系统 |
| `token_budget_enhanced.js` | Token 预算强制执行 |
| `evidence_recall.js` | 证据加权检索 |
| `revision_manager_enhanced.js` | 修订生命周期管理 |
| `webui/dashboard.html` | Web 仪表板 UI |

详细技术文档请参阅 [SKILL.md](SKILL.md)。
-->

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

### Verify Installation

```bash
mcporter call unified-memory memory_health '{}'
```

---

## Configuration

Core environment variables (full guide in [docs/CONFIG.md](docs/CONFIG.md)):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | Memory storage path |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB path |
| `LANCEDB_API_KEY` | (none) | LanceDB Cloud API Key |
| `VECTOR_ENGINE` | `lancedb` | Vector engine: `lancedb` / `ollama` / `none` |
| `LLM_PROVIDER` | `ollama` | LLM provider: `ollama` / `openai` / `none` |

---

## 152 MCP Tools (Organized by Category)

### Storage Core (5 tools)

| Tool | Description |
|------|-------------|
| `memory_store` | Store a memory with category, importance, tags, scope |
| `memory_get` | Retrieve a single memory by ID |
| `memory_list` | Paginated memory listing |
| `memory_delete` | Delete a memory |
| `memory_search` | Hybrid search: BM25 → Vector → Rerank → MMR |

### WAL Protocol (6 tools)

| Tool | Description |
|------|-------------|
| `memory_wal_write` | Write a WAL log entry |
| `memory_wal_replay` | Crash recovery replay |
| `memory_wal_status` | Query WAL status |
| `memory_wal_truncate` | Truncate WAL after checkpoint |
| `memory_wal_export` | Export WAL as backup |
| `memory_wal_import` | Import WAL from backup |

### Evidence Chain (15 tools)

| Tool | Description |
|------|-------------|
| `memory_evidence_add` | Add evidence to a memory |
| `memory_evidence_get` | Get evidence chain for a memory |
| `memory_evidence_find_by_type` | Find evidence by type |
| `memory_evidence_find_by_source` | Find evidence by source |
| `memory_evidence_stats` | Evidence statistics |
| `memory_evidence_recall` | Evidence-driven recall |
| `memory_evidence_index` | Index evidence |
| `memory_evidence_score` | Calculate evidence score |
| `memory_evidence_rank` | Rank results by evidence |
| `memory_evidence_filter_by_type` | Filter by evidence type |
| `memory_evidence_filter_by_source` | Filter by evidence source |
| `memory_evidence_high_confidence` | Filter high-confidence evidence only |
| `memory_evidence_transcript_only` | Return transcript evidence only |
| `memory_evidence_summary` | Get evidence summary |
| `memory_evidence_statistics` | Detailed evidence statistics |

### Transcript-First (11 tools)

| Tool | Description |
|------|-------------|
| `memory_transcript_add` | Add a transcript |
| `memory_transcript_get` | Get transcript by ID |
| `memory_transcript_update` | Update a transcript |
| `memory_transcript_delete` | Delete a transcript |
| `memory_transcript_list` | List all transcripts |
| `memory_transcript_find_by_source` | Find transcripts by source |
| `memory_transcript_rebuild` | Rebuild memories from transcripts |
| `memory_transcript_summary` | Get transcript summary |
| `memory_transcript_stats` | Transcript statistics |
| `memory_transcript_verify` | Verify transcript integrity |
| `memory_transcript_compact` | Compact transcript storage |

### Auto Organization (5 tools)

| Tool | Description |
|------|-------------|
| `memory_organize` | Cross-tier organization |
| `memory_compress_tier` | Compress a specific tier |
| `memory_archive_old` | Archive memories older than 365 days |
| `memory_tier_stats` | Tier statistics |
| `memory_full_organize` | Full system organization |

### Revision Lifecycle (3 tools)

| Tool | Description |
|------|-------------|
| `memory_revision_lifecycle_summary` | Lifecycle stage summary |
| `memory_revision_by_stage` | Get revisions by lifecycle stage |
| `memory_revision_update_stage` | Update revision lifecycle stage |

### Lane Memory (8 tools)

| Tool | Description |
|------|-------------|
| `memory_lane_create` | Create a custom lane |
| `memory_lane_switch` | Switch current lane |
| `memory_lane_current` | Get current lane |
| `memory_lane_list` | List all lanes |
| `memory_lane_move` | Move memory between lanes |
| `memory_lane_archive` | Archive a lane |
| `memory_lane_merge` | Merge lanes |
| `memory_lane_delete` | Delete a lane |

### Token Budget (8 tools)

| Tool | Description |
|------|-------------|
| `memory_token_budget_status` | Get budget status |
| `memory_token_budget_enforce` | Enforce hard limit |
| `memory_token_budget_allocate` | Allocate tokens to category |
| `memory_token_budget_record` | Record token usage |
| `memory_token_budget_compress` | Compress memories to fit budget |
| `memory_token_budget_history` | Get usage history |
| `memory_token_budget_reset` | Reset usage counters |
| `memory_token_budget_config` | Get/update budget config |

### Unified Entry Points — Action-Parameter Tools (10 tools)

These tools use an `action` parameter for multi-operation access:

| Tool | Actions |
|------|---------|
| `memory_reminder` | `add` / `list` / `cancel` |
| `memory_preference` | `get` / `set` / `infer` / `explain` / `stats` / `slots` |
| `memory_version` | `list` / `diff` / `restore` |
| `memory_tier` | `status` / `migrate` / `compress` / `assign` / `partition` / `redistribute` |
| `memory_proactive` | `status` / `trigger` / `start` / `stop` |
| `memory_proactive_care` | `status` / `care` / `insights` |
| `memory_proactive_recall` | `status` / `recall` / `analyze` |
| `memory_qmd` | `search` / `get` / `vsearch` / `list` / `status` |
| `memory_engine` | `bm25` / `embed` / `search` / `mmr` / `rerank` |
| `memory_graph` | `entity` / `relation` / `query` / `stats` / `add` / `delete` |

### Search & Retrieval (7 tools)

| Tool | Description |
|------|-------------|
| `memory_bm25` | Pure BM25 keyword search |
| `memory_vector` | Dense vector similarity search |
| `memory_scope` | Scope-filtered search |
| `memory_concurrent_search` | Parallel multi-scope search |
| `memory_dedup` | Deduplicate search results |
| `memory_noise` | Filter noisy results |
| `memory_mmr` | Maximal Marginal Relevance rerank |

### Analysis & Management (16 tools)

| Tool | Description |
|------|-------------|
| `memory_trace` | Trace memory access patterns |
| `memory_metrics` | System metrics |
| `memory_decay` | Weibull decay management |
| `memory_extract` | Entity extraction from text |
| `memory_reflection` | Memory reflection analysis |
| `memory_intent` | Intent routing |
| `memory_wal` | WAL status and management |
| `memory_adaptive` | Adaptive memory management |
| `memory_autostore` | Auto-store configuration |
| `memory_auto_extract` | Auto entity extraction |
| `memory_health` | System health check |
| `memory_insights` | Memory insights report |
| `memory_predict` | Predict memory needs |
| `memory_feedback` | Memory quality feedback |
| `memory_stats` | Overall statistics |
| `memory_lesson` | Learned lessons management |

### Cloud & System (12 tools)

| Tool | Description |
|------|-------------|
| `memory_cloud_backup` | Backup to cloud storage |
| `memory_cloud_restore` | Restore from cloud backup |
| `memory_export` | Export memories to JSON |
| `memory_import` | Import memories from JSON |
| `memory_clone` | Clone memory database |
| `memory_share` | Share memories across agents |
| `memory_intent` | Intent detection |
| `memory_insights` | Insight generation |
| `memory_predict` | Predictive memory |
| `memory_feedback` | Feedback processing |
| `memory_health` | Health monitoring |
| `memory_stats` | Statistics dashboard |

> **Note**: Exact tool count may vary slightly by install. Run `mcporter list unified-memory` to see tools available in your installation.

---

## Quick Start

```bash
# 1. Verify installation
mcporter call unified-memory memory_health '{}'

# 2. Store a memory
mcporter call unified-memory memory_store '{
  "text": "Liu prefers concise communication",
  "category": "preference",
  "scope": "USER"
}'

# 3. Search memories (hybrid BM25 + Vector + RRF)
mcporter call unified-memory memory_search '{
  "query": "Liu communication style",
  "scope": "USER"
}'

# 4. Check system stats
mcporter call unified-memory memory_stats '{}'

# 5. Add a reminder
mcporter call unified-memory memory_reminder '{
  "action": "add",
  "content": "team meeting",
  "minutes": 30
}'

# 6. View knowledge graph
mcporter call unified-memory memory_graph '{"action": "stats"}'

# 7. Check WAL status
mcporter call unified-memory memory_wal_status '{}'

# 8. View tier status
mcporter call unified-memory memory_tier '{"action": "status"}'

# 9. Check token budget
mcporter call unified-memory memory_token_budget_status '{}'

# 10. Start web dashboard
node start-dashboard.js
```

---

## Scope Isolation

Scope isolation ensures memory access is always contextually appropriate:

```bash
# Search only USER-scoped memories
mcporter call unified-memory memory_search '{
  "query": "project plans",
  "scope": "USER"
}'

# Search only TEAM-scoped memories
mcporter call unified-memory memory_search '{
  "query": "team decisions",
  "scope": "TEAM"
}'

# Search only GLOBAL-scoped memories
mcporter call unified-memory memory_search '{
  "query": "company policies",
  "scope": "GLOBAL"
}'

# Agent-scoped is auto-applied when running as an agent
```

| Scope | Who Can Write | Who Can Read |
|-------|--------------|--------------|
| `AGENT` | Only the owning agent | Only the owning agent |
| `USER` | Any agent on behalf of the user | User + TEAM + GLOBAL |
| `TEAM` | Any agent in the team | Team + GLOBAL |
| `GLOBAL` | Any agent | All agents |

---

## Development

```bash
# Install dependencies
npm install --ignore-scripts

# Start MCP server (stdio mode)
node src/index.js

# CLI help
node src/cli/index.js --help

# Run tests
node run-tests.cjs

# Start web dashboard
node start-dashboard.js

# Run integration tests
node test-all.cjs

# Check tier migration
node src/test_tier.js
```

### File Structure

```
unified-memory/
├── src/
│   ├── index.js                    # MCP server (28 unified tools)
│   ├── storage.js                  # JSON + WAL persistence
│   ├── wal.js                      # Write-Ahead Log
│   ├── evidence.js                 # Evidence chain
│   ├── evidence_recall.js          # Evidence-driven recall
│   ├── organize.js                 # Auto organization
│   ├── transcript_first.js         # Transcript-First architecture
│   ├── revision_manager_enhanced.js # Revision lifecycle
│   ├── lane_manager_enhanced.js    # Lane memory
│   ├── token_budget_enhanced.js    # Token budget
│   ├── bm25.js                     # BM25 engine
│   ├── vector_lancedb.js           # LanceDB backend
│   ├── cognitive_scheduler.js      # Proactive scheduler
│   ├── session_state.js            # Hot context
│   ├── decay.js                    # Weibull decay
│   ├── graph/                      # Knowledge graph
│   ├── cli/                        # CLI tools
│   └── webui/dashboard.html        # Dashboard UI
├── docs/
│   ├── CONFIG.md                   # Configuration guide
│   └── competitive-analysis.md     # Competitive analysis
├── SKILL.md                        # Technical deep-dive
├── SKILL_CN.md                     # Chinese technical guide
├── README.md                       # This file
├── README_CN.md                    # Legacy Chinese README
├── README.zh-CN.md                 # Legacy zh-CN README
└── package.json                    # Package config
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📚 Complete Documentation Index

> 🌍 **Language**: [English](./README.md) · **[中文](./README_CN.md)** · [日本語](./README_JA.md)

### 📖 Main Documentation | 主文档

| File | Description |
|------|-------------|
| [README.md](./README.md) | **This file** — Bilingual main documentation (英汉双语主文档) |
| [README_CN.md](./README_CN.md) | 中文主文档 — Complete Chinese documentation |
| [README.zh-CN.md](./README.zh-CN.md) | Legacy Chinese README (旧版中文自述) |
| [SKILL.md](./SKILL.md) | Technical deep-dive (English) |

### 🗂️ docs/en/ — English Technical Docs

| File | Description |
|------|-------------|
| [docs/en/README.md](./docs/en/README.md) | Technical overview |
| [docs/en/HOOK_INTEGRATION.md](./docs/en/HOOK_INTEGRATION.md) | Hook integration guide |
| [docs/en/MCP_INTEGRATION.md](./docs/en/MCP_INTEGRATION.md) | MCP integration guide |
| [docs/en/INTEGRATION_COMPARISON.md](./docs/en/INTEGRATION_COMPARISON.md) | Integration comparison |

### 🗂️ docs/zh/ — 中文技术文档

| 文件 | 说明 |
|------|------|
| [docs/zh/README.md](./docs/zh/README.md) | 技术概述 |
| [docs/zh/HOOK_INTEGRATION.md](./docs/zh/HOOK_INTEGRATION.md) | Hook 集成指南 |
| [docs/zh/MCP_INTEGRATION.md](./docs/zh/MCP_INTEGRATION.md) | MCP 集成指南 |
| [docs/zh/INTEGRATION_COMPARISON.md](./docs/zh/INTEGRATION_COMPARISON.md) | 集成对比 |

### 📋 docs/ — General Documents | 通用文档

| File | Description |
|------|-------------|
| [docs/index.md](./docs/index.md) | **Documentation hub** — All docs index (总索引) |
| [docs/CONFIG.md](./docs/CONFIG.md) | Detailed configuration guide |
| [docs/competitive-analysis.md](./docs/competitive-analysis.md) | Feature comparison |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Architecture deep-dive |
| [docs/v4.0-ARCHITECTURE.md](./docs/v4.0-ARCHITECTURE.md) | v4.0 architecture |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | Full changelog |
| [docs/v3.8.0-release-notes.md](./docs/v3.8.0-release-notes.md) | v3.8.0 release notes |
| [docs/v3.8.1-release-notes.md](./docs/v3.8.1-release-notes.md) | v3.8.1 release notes |
| [docs/v3.8.2-release-notes.md](./docs/v3.8.2-release-notes.md) | v3.8.2 release notes |
| [docs/v3.8.3-release-notes.md](./docs/v3.8.3-release-notes.md) | v3.8.3 release notes |
| [docs/v3.8.4-release-notes.md](./docs/v3.8.4-release-notes.md) | v3.8.4 release notes |

### 🚀 Quick Access | 快速访问

- [README_QUICK_START.md](./README_QUICK_START.md) — Quick start guide (快速入门)
- [docs/index.md](./docs/index.md) — 📚 **All docs index** (总索引页)

---

*Last updated: 2026-04-01 | v3.8.4 | 152 MCP Tools | Pure Node.js ESM*
