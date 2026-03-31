# Unified Memory Architecture
<!-- zh -->
> 统一记忆系统技术架构 | Technical Architecture Documentation

---

## 1. System Overview
<!-- zh -->

Unified Memory is a pure Node.js ESM memory system for OpenClaw agents, featuring hybrid search, tiered storage, and intelligent management.

**Key Design Goals / 设计目标**:
1. Zero external dependencies (no Python, no external DB)
2. Hybrid search (BM25 + Vector + RRF)
3. Tiered memory (HOT / WARM / COLD)
4. Data durability (WAL protocol)
5. Evidence traceability (Evidence Chain)

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Memory v3.8.x                    │
│                    112 Tools · Pure Node.js ESM             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Storage   │  │   Search    │  │    Intelligence     │  │
│  │    Layer    │  │    Layer    │  │      Layer          │  │
│  │             │  │             │  │                     │  │
│  │ · Memory    │  │ · BM25      │  │ · Cognitive Sched.  │  │
│  │   Files     │  │ · Vector    │  │ · Memory Lanes      │  │
│  │ · LanceDB  │  │ · RRF       │  │ · Evidence Chain   │  │
│  │ · WAL       │  │ · Scope     │  │ · Auto Organize    │  │
│  │ · Tier      │  │   Filter    │  │ · Weibull Decay    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Plugin Interface (Pluggable)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

<!-- zh -->

## 2. Storage Layer / 存储层

### 2.1 Memory Files / 记忆文件

```
memory/
├── hot/      ← HOT tier (7 days, ≤10 memories)
├── warm/     ← WARM tier (30 days, ≤50 memories)
└── cold/     ← COLD tier (365 days, ≤1000 memories)
```

Each memory is a markdown file with YAML frontmatter:
```yaml
---
id: mem_abc123
scope: agent       # agent | user | team | global
category: fact     # fact | preference | habit | skill | goal | identity
importance: 0.8    # 0.0 - 1.0
tier: warm
created: 2026-03-30T10:00:00+08:00
lastAccessed: 2026-03-30T10:00:00+08:00
accessCount: 1
decayScore: 0.95
---
Memory content goes here...
```

### 2.2 LanceDB Vector Store / LanceDB 向量存储
<!-- zh -->

- **Embedded**: No external service required
- **Collection**: `memories` (scope-indexed via B-tree)
- **Embedding**: Ollama (nomic-embed-text) or OpenAI/Jina/SiliconFlow
- **Cache**: Vector cache with 100% complete rate target

```
LanceDB Schema:
┌────────────────────────────────────────┐
│ id          │ string (PK)               │
│ scope       │ string (indexed)          │
│ category    │ string                    │
│ embedding   │ base64 string (1536 dim) │
│ text        │ string                    │
│ importance  │ float                     │
│ created     │ timestamp                 │
└────────────────────────────────────────┘
```

### 2.3 WAL Protocol / WAL 预写日志
<!-- zh -->

Write-Ahead Log ensures data durability and crash recovery.

**File**: `data/wal/*.wal.jsonl`

```
WAL Entry Format:
{"op":"insert","collection":"memories","data":{...},"timestamp":"...","checksum":"..."}
{"op":"update","collection":"memories","id":"mem_123","data":{...},"timestamp":"...","checksum":"..."}
{"op":"delete","collection":"memories","id":"mem_456","timestamp":"...","checksum":"..."}
```

**Workflow / 工作流程**:
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │ ──▶ │     WAL      │ ──▶ │  Storage.js  │
│  Write Op    │     │  (append)    │     │  (commit)    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼ (on crash)
                     ┌──────────────┐
                     │   Replay     │ ──▶ Recover uncommitted ops
                     │   WAL        │
                     └──────────────┘
```

### 2.4 Tier Management / 分层管理
<!-- zh -->

Automatic migration between HOT → WARM → COLD based on age and importance.

| Tier | Max Age | Max Count | Compression | Location |
|------|---------|-----------|-------------|----------|
| HOT | 7 days | 10 | 50% | `memory/hot/` |
| WARM | 30 days | 50 | 30% | `memory/warm/` |
| COLD | 365 days | 1000 | 10% | `memory/cold/` |

---

## 3. Search Layer / 搜索层
<!-- zh -->

### 3.1 Hybrid Search Pipeline / 混合搜索管道

```
┌─────────────────────────────────────────────────────────────┐
│                    Hybrid Search Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Query: "user preference for dark mode"                     │
│                                                              │
│         ┌─────────────┐                                     │
│         │    BM25     │ ← Keyword matching                  │
│         │  (scored)   │   importance + accessCount          │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │   Vector    │ ← Semantic similarity                │
│         │  ( cosine ) │   LanceDB embedding                  │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │     RRF     │ ← Reciprocal Rank Fusion            │
│         │  (merged)   │   k=60, rank-based scoring           │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │   Scope     │ ← AGENT / USER / TEAM / GLOBAL      │
│         │   Filter    │   B-tree index filtering             │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │  Weibull    │ ← Decay based on:                   │
│         │   Decay     │   - Time since last access           │
│         │             │   - Access frequency                │
│         └──────┬──────┘   - Importance score                 │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │   Results   │ ← Top-K with evidence metadata       │
│         │  ( ranked ) │                                     │
│         └─────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 BM25 / BM25 全文索引
<!-- zh -->

Classic keyword-based search with relevance scoring.

**Formula**: `score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))`

**Features**:
- Importance-weighted boost (+15% for high importance)
- Access count boost (+5% per access, capped at +50%)
- Full-text content + category + scope search

### 3.3 Vector Search / 向量搜索
<!-- zh -->

Semantic similarity search using embeddings.

**Supported Providers**:
| Provider | Model | Dimensions | Notes |
|----------|-------|------------|-------|
| Ollama | nomic-embed-text | 1536 | Local, recommended |
| OpenAI | text-embedding-3-small | 1536 | Requires API key |
| Jina | jina-embeddings-v3 | 1024 | Free tier available |
| SiliconFlow | Pro/Yg-16 | 2048 | API key required |

### 3.4 RRF (Reciprocal Rank Fusion) / 倒数排名融合
<!-- zh -->

Combines BM25 and Vector results using rank-based fusion.

```
RRF(score, d) = Σ 1 / (k + rank_d(document))
```

Where `k = 60` (standard damping factor).

---

## 4. Intelligence Layer / 智能层
<!-- zh -->

### 4.1 Cognitive Scheduler / 认知调度器
<!-- zh -->

Proactive memory exploration and recall scheduling.

- Periodic background recalls (configurable interval)
- Category-based recall strategies
- Importance-weighted selection
- Pattern-based memory triggering

### 4.2 Memory Lanes / 记忆车道
<!-- zh -->

Multi-lane parallel memory management for independent contexts.

```
┌─────────────────────────────────────────┐
│  Lane: project-alpha                    │
│  Lane: project-beta                     │
│  Lane: personal                         │
│  Lane: work                             │
│  Lane: default                           │
└─────────────────────────────────────────┘
```

Each lane maintains independent:
- Memory files
- Search scope
- Tier management

### 4.3 Evidence Chain / 证据链
<!-- zh -->

Traceable memory provenance and evolution tracking.

**Evidence Entry**:
```json
{
  "id": "ev_abc123",
  "memoryId": "mem_xyz789",
  "type": "transcript",
  "sourceId": "msg_456",
  "confidence": 0.95,
  "context": "User mentioned preference for dark mode",
  "timestamp": "2026-03-30T10:00:00+08:00"
}
```

**Evidence Types**:
| Type | Source |
|------|--------|
| transcript | Conversation transcript |
| message | Specific message ID |
| manual | Manually added |
| inference | AI inferred |
| git_note | Git note |
| revision | Memory revision |

### 4.4 Auto Organization / 自动整理
<!-- zh -->

Scheduled automatic memory management across tiers.

**Operations**:
1. **Organize**: Migrate memories to appropriate tiers
2. **Compress**: Summarize low-importance memories
3. **Archive**: Move very old memories (365+ days) to archive

**Triggered by**: `memory_full_organize` tool or scheduled cron

### 4.5 Weibull Decay / Weibull 衰减
<!-- zh -->

Memory strength decay based on Weibull distribution (forgetting curve).

**Parameters**:
- Shape (`k`): 1.5 (optimized)
- Scale (`λ`): 30 days
- Access reward: +5% per access (capped at +50%)

**Formula**: `strength = importance * e^(-(age/λ)^k) * (1 + accessBonus)`

### 4.6 Knowledge Graph / 知识图谱
<!-- zh -->

Entity and relationship tracking for connected memories.

**Node Types**: person, place, thing, concept, event
**Edge Types**: related_to, part_of, causes, implies, similar_to

---

## 5. Data Flow Diagram / 数据流图
<!-- zh -->

### 5.1 Write Flow / 写入流程

```
Client
  │
  │ memory_write(text, scope, category, importance)
  ▼
┌─────────────────────┐
│  WAL (append only)  │ ← checksum + timestamp
└──────────┬──────────┘
           │ on success
           ▼
┌─────────────────────┐
│  Storage.js         │
│  1. Write to file   │
│  2. Generate ID      │
│  3. Update metadata  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LanceDB             │
│  1. Get embedding    │
│  2. Insert vector    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Tier Manager        │
│  Classify: HOT/WARM │
│  Based on importance│
└──────────┬──────────┘
           │
           ▼
        Done ✅
```

### 5.2 Search Flow / 搜索流程

```
Client
  │
  │ memory_search(query, scope, category, limit)
  ▼
┌─────────────────────────────────────────┐
│  Query Processing                       │
│  1. Parse query                         │
│  2. Get embedding (vector provider)    │
│  3. Extract keywords (BM25)             │
└──────────┬──────────────────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌─────────┐
│  BM25   │  │ Vector  │
│ scorer  │  │ search  │
└────┬────┘  └────┬────┘
     │            │
     └─────┬──────┘
           ▼
┌─────────────────────┐
│  RRF Fusion         │
│  k=60, rank-based   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Scope Filter       │
│  B-tree index       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Weibull Decay      │
│  Time + Access adj  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Evidence Enrich    │
│  Attach evidence    │
│  chain to results   │
└──────────┬──────────┘
           │
           ▼
        Results ✅
```

### 5.3 Crash Recovery Flow / 崩溃恢复流程

```
Startup
  │
  ▼
┌─────────────────────┐
│  Check WAL status    │
│  Any uncommitted ops?│
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
    Yes         No
     │           │
     ▼           ▼
┌──────────┐  Done ✅
│ Replay   │
│ WAL      │
│ entries  │
└────┬─────┘
     │
     ▼
┌─────────────────────┐
│  For each WAL entry │
│  1. Verify checksum │
│  2. Apply operation │
│  3. Commit to store │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Truncate WAL       │
│  (mark as clean)    │
└──────────┬──────────┘
           │
           ▼
        Done ✅
```

---

## 6. Plugin Interface / 插件接口
<!-- zh -->

Unified Memory provides a pluggable architecture for extending functionality.

**Phase 3 Plugin Interface**:
```javascript
// memory_search plugin
async function phase3_memory_search({ query, scope, limit }) {
  // Custom search implementation
  return results;
}

// memory_write plugin
async function phase3_memory_write({ memory }) {
  // Custom write handling
  return { success: true };
}

// memory_get plugin
async function phase3_memory_get({ id }) {
  // Custom get handling
  return memory;
}
```

**Registered Plugins**:
- QMD Search Backend (`memory_qmd_*`)
- Git Integration (`memory_git_*`)
- Cloud Backup (`memory_cloud_*`)

---

## 7. Configuration / 配置
<!-- zh -->

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `nomic-embed-text` | Embedding model |
| `VECTOR_PROVIDER` | `ollama` | Vector provider |
| `ENABLE_WAL` | `true` | Enable WAL protocol |
| `WAL_INTERVAL_MS` | `5000` | WAL flush interval |
| `AUTO_ORGANIZE_INTERVAL` | `86400` | Auto-organize interval (24h) |
| `EVIDENCE_TRACKING` | `true` | Enable evidence chain |
| `HOT_MAX_AGE_DAYS` | `7` | HOT tier max age |
| `WARM_MAX_AGE_DAYS` | `30` | WARM tier max age |
| `COLD_MAX_AGE_DAYS` | `365` | COLD tier max age |

---

## 8. File Structure / 文件结构
<!-- zh -->

```
unified-memory/
├── src/
│   ├── index.js              ← Main entry, 112 tools
│   ├── storage.js            ← Core read/write/delete
│   ├── search.js            ← Hybrid search (BM25+Vector+RRF)
│   ├── tier.js              ← HOT/WARM/COLD management
│   ├── wal.js               ← WAL protocol
│   ├── evidence.js          ← Evidence chain
│   ├── organize.js          ← Auto organization
│   ├── transcript.js       ← Transcript logging
│   ├── git-notes.js         ← Git integration
│   ├── revision.js          ← Version management
│   ├── budget.js            ← Token budget
│   ├── cognitive.js         ← Cognitive scheduler
│   ├── lanes.js            ← Memory lanes
│   ├── cloud-backup.js      ← Cloud backup API
│   ├── weibull.js           ← Weibull decay
│   ├── knowledge-graph.js   ← Knowledge graph
│   ├── identity.js          ← Identity memory
│   ├── qmd.js              ← QMD search backend
│   ├── scope.js            ← Scope isolation
│   └── utils/
│       ├── config.js        ← Configuration
│       ├── embedding.js     ← Embedding providers
│       └── ...
├── memory/
│   ├── hot/
│   ├── warm/
│   └── cold/
├── data/
│   ├── vectors.lance/       ← LanceDB storage
│   ├── evidence.db          ← Evidence SQLite
│   └── wal/                  ← WAL files
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md       ← This document
│   ├── competitive-analysis.md
│   └── v3.8.0-release-notes.md
├── CHANGELOG.md
└── SKILL.md
```

---

## 9. Version History / 版本历史
<!-- zh -->

| Version | Date | Highlights |
|---------|------|-----------|
| v3.8.0 | 2026-03-30 | WAL Protocol, Evidence Chain, Auto Organization |
| v3.7.0 | 2026-03-29 | 97 tools, full feature set |
| v3.6.0 | 2026-03-29 | WAL cleanup, vector cache fixes |
| v3.5.0 | 2026-03-28 | Web UI + API Server, Chinese UI |
| v3.0.0 | 2026-03-27 | Pure Node.js ESM rewrite |
| v2.0.0 | 2026-03-26 | Full rewrite, Weibull decay, scope isolation |
| v1.x | 2026-03-25 | Python prototype |

See [CHANGELOG.md](../CHANGELOG.md) for full history.

---

*Last updated: 2026-03-31*
