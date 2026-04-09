# Unified Memory — Technical Architecture

> 技术架构文档 | Technical Architecture Documentation
> **版本**: v4.4 / v5.0 | **更新**: 2026-04-09

---

## 1. System Overview

Unified Memory is a pure Node.js ESM memory system for OpenClaw agents, featuring:

- 🔄 **四层渐进式管线** — L0→L1→L2→L3 完整记忆生命周期
- 🔍 **混合搜索** — BM25 + Vector + RRF 融合
- 💾 **双存储后端** — LanceDB / SQLite 向量存储
- 📈 **Weibull 衰减** — 模拟人类遗忘曲线
- 💰 **WAL 协议** — 崩溃恢复保障
- 🏷️ **四层 Scope 隔离** — USER / TEAM / AGENT / GLOBAL
- 📊 **知识图谱** — 实体关系提取与查询
- 🔗 **证据链** — 来源追踪与置信度评分
- 🏊 **泳道记忆** — 多 Agent 并行隔离
- 🤖 **OpenViking 集成** — 意图分析 + 层级检索 + 分层压缩
- 🔌 **插件系统** — 5 种 Hook 可扩展架构
- ⚡ **Benchmark** — recall@K / precision@K / MRR 召回率验证

### 核心设计目标

1. **零外部依赖** — 无 Python，无外部数据库（除可选的 Ollama）
2. **混合搜索** — BM25 + Vector + RRF
3. **分层记忆** — HOT / WARM / COLD
4. **数据持久性** — WAL 协议
5. **可追溯性** — 证据链机制
6. **OpenViking 兼容** — 完整 Viking URI + 意图分析 + 分层压缩

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Unified Memory v4.4 / v5.0                   │
│                    100+ Tools · Pure Node.js ESM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     MCP Server (index.js)                      │  │
│  │              100+ registered tools · stdio transport           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │   Storage   │  │   Search    │  │       Intelligence      │   │
│  │    Layer    │  │    Layer    │  │         Layer           │   │
│  │              │  │              │  │                         │   │
│  │ · Memory    │  │ · BM25      │  │ · Cognitive Scheduler  │   │
│  │   Files     │  │ · Vector     │  │ · Memory Lanes        │   │
│  │ · LanceDB  │  │ · RRF        │  │ · Evidence Chain     │   │
│  │ · SQLite   │  │ · Scope      │  │ · Auto Organize      │   │
│  │ · WAL       │  │   Filter     │  │ · Weibull Decay     │   │
│  │ · Tier      │  │ · Intent     │  │ · Intent Analyzer    │   │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │            Plugin System (Pluggable Architecture)             │   │
│  │    beforeSearch / afterSearch / beforeWrite / afterWrite      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   OpenViking System (v5.0)                    │   │
│  │   Viking URI · Intent Analysis · Hierarchical Retrieval       │   │
│  │   Session Mgmt · 8-class Extraction · Layered Compression    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Four-Layer Pipeline (L0→L1→L2→L3)

### 3.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Four-Layer Progressive Pipeline                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  L0 (对话录制) ─────────────────────────────────────────────────   │
│  │  transcript_first.js + l0_recorder.js                            │
│  │  • 捕获原始对话，JSONL 格式存储                                   │
│  │  • 增量捕获，支持向量索引                                         │
│  ▼                                                                   │
│  L1 (记忆提取) ─────────────────────────────────────────────────   │
│  │  extract.js + memory_types/registry.js                           │
│  │  • 从对话中提取关键信息、实体、关系、偏好                         │
│  │  • 6 种记忆类型自动检测                                          │
│  │  • LLM 实体/关系/偏好提取                                        │
│  │  • 智能去重 (精确/语义/FTS/LLM)                                  │
│  ▼                                                                   │
│  L2 (场景归纳) ─────────────────────────────────────────────────   │
│  │  scene_block.js + scene_navigation.js                           │
│  │  • 按时间窗口聚类记忆，生成场景块                                 │
│  │  • 提取场景主题、关键实体、行动项                                 │
│  │  • 场景导航生成                                                  │
│  ▼                                                                   │
│  L3 (用户画像) ─────────────────────────────────────────────────   │
│  │  profile.js + persona_generator.js                              │
│  │  • 静态 + 动态双画像                                             │
│  │  • 用户偏好、习惯、目标                                           │
│  │  • 5 级优先级触发机制                                            │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                        Hook Auto-Scheduling                           │
│  • before_prompt_build: 自动召回相关记忆                             │
│  • agent_end: 自动捕获对话到 L0                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Memory Type System

| Type | Handler | Priority | Retention | Description |
|------|---------|----------|-----------|-------------|
| `facts` | facts.js | High | Permanent | Factual memories |
| `patterns` | patterns.js | Medium | 6 months | Behavioral patterns |
| `skills` | skills.js | High | 1 year | Technical skills |
| `cases` | cases.js | Medium | 6 months | Problem-solving cases |
| `events` | events.js | Low | 3 months | Events and decisions |
| `preferences` | preferences.js | High | Permanent | User preferences |

---

## 4. Storage Layer

### 4.1 Dual Backend Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Vector Store Factory                             │
│                     (store/vector_factory.js)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│       ┌─────────────────┐              ┌─────────────────┐         │
│       │    LanceDB      │              │     SQLite      │         │
│       │   (default)     │              │  (sqlite-vec)   │         │
│       │                 │              │                 │         │
│       │ · Embedded      │              │ · FTS5 + BM25   │         │
│       │ · No server     │              │ · Cosine sim.   │         │
│       │ · 1536 dim      │              │ · L0 + L1 layers│         │
│       └─────────────────┘              └─────────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tier Management

| Tier | Max Age | Max Count | Compression | Storage |
|------|---------|-----------|-------------|---------|
| **HOT** | 7 days | 10 | 50% | `memory/hot/` |
| **WARM** | 30 days | 50 | 30% | `memory/warm/` |
| **COLD** | 365 days | 1000 | 10% | `memory/cold/` |

### 4.3 WAL Protocol

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │ ──▶ │     WAL      │ ──▶ │   Storage    │
│  Write Op    │     │  (append)    │     │   (commit)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼ (on crash)
                     ┌──────────────┐
                     │   Replay     │ ──▶ Recover uncommitted ops
                     │     WAL      │
                     └──────────────┘
```

**WAL Entry Format**:
```json
{"op":"insert","collection":"memories","data":{...},"timestamp":"...","checksum":"..."}
{"op":"update","collection":"memories","id":"mem_123","data":{...},"timestamp":"...","checksum":"..."}
{"op":"delete","collection":"memories","id":"mem_456","timestamp":"...","checksum":"..."}
```

---

## 5. Search Layer

### 5.1 Hybrid Search Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Hybrid Search Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Query: "user preference for dark mode"                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  BM25 Scorer          Vector Search        Scope Filter     │   │
│  │  • Keyword match      • Cosine similarity  • B-tree index  │   │
│  │  • Importance boost   • Ollama embeddings  • O(log n)      │   │
│  │  • Access count       • Multi-provider                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              RRF Fusion (k=60)                               │   │
│  │  score = Σ 1 / (k + rank_d(document))                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Weibull Decay                                   │   │
│  │  strength = importance × e^(-(age/λ)^k) × (1 + accessBonus) │   │
│  │  shape=1.5, scale=30d, access reward +5% (cap +50%)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  MMR Re-ranking                              │   │
│  │  Maximal Marginal Relevance for diversity                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│                      Top-K Results ✅                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Intent Analysis (v5.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Intent Analysis Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Query: "帮我创建一个 RFC 文档"                                  │
│                                                                      │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           LLM Intent Analyzer                                │   │
│  │  → Generate 0-5 TypedQueries                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TypedQuery[]                                               │   │
│  │  • query="创建 RFC 文档", context_type=SKILL, priority=5    │   │
│  │  • query="RFC 文档模板", context_type=RESOURCE, priority=4  │   │
│  │  • query="用户的代码风格偏好", context_type=MEMORY, priority=3│   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Hierarchical Retrieval (v5.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Hierarchical Retrieval Pipeline                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 确定根目录（根据 context_type）                              │
│                            │                                         │
│                            ▼                                         │
│  Step 2: 全局向量搜索定位起始目录                                     │
│                            │                                         │
│                            ▼                                         │
│  Step 3: 合并起始点 + Rerank 评分                                    │
│                            │                                         │
│                            ▼                                         │
│  Step 4: 递归搜索（优先队列）                                        │
│          while dir_queue:                                             │
│            pop current_uri, parent_score                             │
│            search children                                           │
│            final_score = 0.5 × embedding + 0.5 × parent             │
│            if final_score > threshold:                               │
│              collect result                                          │
│              if not leaf: push to queue                              │
│                                                                      │
│                            │                                         │
│                            ▼                                         │
│  Step 5: 收敛检测（top-k 连续 3 轮不变停止）                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. OpenViking System (v5.0)

### 6.1 System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                   OpenVikingSystem (openviking_system.js)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Viking URI    │  │ Intent Analysis │  │ Hierarchical    │    │
│  │   (viking_uri)  │  │   (intent)      │  │ Retrieval       │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │    Session      │  │    Reranker     │  │  Memory         │    │
│  │   (session)     │  │   (reranker)    │  │  Extractor      │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  File System    │  │  Document       │  │    Relations    │    │
│  │   (fs)          │  │  Parser         │  │   (relations)   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Layered Compressor (layered_compressor)         │    │
│  │  L0: ~100 tokens │ L1: ~2k tokens │ L2: unlimited           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Viking URI Format

```
viking://
├── resources/              # 独立资源
│   └── {project}/
│       ├── .abstract.md
│       ├── .overview.md
│       └── {files...}
├── user/{user_id}/
│   ├── profile.md
│   └── memories/
│       ├── preferences/
│       ├── entities/
│       └── events/
├── agent/{agent_id}/
│   ├── skills/
│   └── memories/
│       ├── cases/
│       └── patterns/
└── session/{session_id}/
    ├── messages/
    ├── tools/
    └── history/
```

### 6.3 8-Class Memory Extraction

| Category | Owner | Description | Mergeable |
|----------|-------|-------------|-----------|
| `profile` | user | User identity/attributes | ✅ |
| `preferences` | user | User preferences | ✅ |
| `entities` | user | Entities (people/projects) | ✅ |
| `events` | user | Events/decisions | ❌ |
| `cases` | agent | Problem + solution | ❌ |
| `patterns` | agent | Reusable patterns | ✅ |
| `tools` | agent | Tool usage knowledge | ✅ |
| `skills` | agent | Skill execution knowledge | ✅ |

### 6.4 Layered Compression

| Layer | Token Limit | Purpose | Use Case |
|-------|-------------|---------|----------|
| **L0** | ~100 | Abstract | Fast filtering, vector search |
| **L1** | ~2k | Overview | Content navigation, reranking |
| **L2** | unlimited | Detail | On-demand full content |

---

## 7. Enhanced Memory System (v4.5)

### 7.1 Components

```
┌─────────────────────────────────────────────────────────────────────┐
│           Enhanced Memory System (enhanced_memory_system.js)         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Type Registry │  │  Memory Queue   │  │  Smart          │    │
│  │  (memory_types) │  │  (queue)        │  │  Deduplicator   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Recall          │  │   Memory        │  │   Lifecycle     │    │
│  │ Optimizer       │  │   Compressor    │  │   Manager       │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Smart Deduplication

| Strategy | Method | Threshold |
|----------|--------|-----------|
| **Exact** | Text equality | 100% |
| **Semantic** | Vector similarity | > 0.95 |
| **FTS** | Full-text similarity | > 0.85 |
| **LLM** | Deep contradiction detection | Variable |

---

## 8. Plugin System

### 8.1 Hook Interface

```
beforeSearch → [Actual Search] → afterSearch
                   ↓
beforeWrite → [Actual Write] → afterWrite
```

### 8.2 Built-in Plugins

| Plugin | Hook | Description |
|--------|------|-------------|
| `kg-enrich` | afterSearch | Knowledge graph enrichment |
| `dedup` | beforeWrite | Pre-write deduplication |
| `revision` | afterWrite | Version tracking |

---

## 9. Data Flow

### 9.1 Write Flow

```
Client
  │
  │ memory_store(text, scope, category, importance)
  ▼
┌─────────────────────────────────────────────────────────────┐
│  WAL (append only)                                         │
│  • Checksum + timestamp                                    │
│  • Single SQLite transaction                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Layer                                              │
│  • Write to file / SQLite                                  │
│  • Generate ID                                             │
│  • Update metadata                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Vector Store (LanceDB / SQLite)                            │
│  • Get embedding (Ollama / Local / OpenAI / Jina)         │
│  • Insert vector                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier Manager                                               │
│  • Classify: HOT / WARM / COLD                             │
│  • Based on importance and age                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                        Done ✅
```

### 9.2 Search Flow (with Intent Analysis)

```
Client
  │
  │ memory_search(query, scope, options)
  ▼
┌─────────────────────────────────────────────────────────────┐
│  Intent Analysis (v5.0)                                     │
│  • LLM analyze query intent                                  │
│  • Generate TypedQuery[]                                   │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  BM25    │  │  Vector  │  │  Hier.   │
        │  Search  │  │  Search  │  │ Retrieval│
        └────┬─────┘  └────┬─────┘  └────┬─────┘
              │            │             │
              └─────────────┼─────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  RRF Fusion (k=60) + Rerank                                │
│  • Normalized score fusion                                  │
│  • Provider: volcengine / cohere / jina / local            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layered Compression                                        │
│  • Load L0 for filtering                                    │
│  • Load L1 for context building                             │
│  • Load L2 on-demand for details                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                        Results ✅
```

### 9.3 Crash Recovery Flow

```
Startup
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  Check WAL status                                            │
│  Any uncommitted ops?                                        │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
             Yes                          No
              │                            │
              ▼                            ▼
        ┌──────────┐               Done ✅
        │  Replay  │
        │   WAL    │
        └────┬─────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  For each WAL entry                                          │
│  • Verify checksum                                          │
│  • Apply operation                                          │
│  • Commit to store                                          │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Truncate WAL (mark as clean)                               │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
         Done ✅
```

---

## 10. Configuration

### 10.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `LLM_MODEL` | `qwen2.5:7b` | LLM model for generation |
| `VECTOR_STORE_TYPE` | `lancedb` | Vector backend: `lancedb` / `sqlite` |
| `SQLITE_DB_PATH` | `./memory/memory.db` | SQLite database path |
| `STORAGE_MODE` | `json` | Storage backend: `json` / `sqlite` |
| `ENABLE_WAL` | `true` | Enable WAL protocol |
| `HOT_MAX_AGE_DAYS` | `7` | HOT tier max age |
| `WARM_MAX_AGE_DAYS` | `30` | WARM tier max age |
| `COLD_MAX_AGE_DAYS` | `365` | COLD tier max age |

### 10.2 OpenViking Configuration

```javascript
const system = createOpenVikingSystem({
  // Intent Analysis
  enableIntentAnalysis: true,
  intentAnalyzer: { maxQueries: 5, enableCache: true },

  // Hierarchical Retrieval
  enableHierarchicalRetrieval: true,
  hierarchicalRetriever: { scorePropagationAlpha: 0.5, maxConvergenceRounds: 3 },

  // Rerank
  enableRerank: true,
  reranker: { provider: 'volcengine', model: 'doubao-seed-rerank', topN: 20 },

  // Session Management
  enableSessionManagement: true,
  sessionManager: { maxMessagesBeforeArchive: 20, enableAutoArchive: true },

  // Memory Extraction
  enableMemoryExtraction: true,
  memoryExtractor: { similarityThreshold: 0.85, enableLLMDedup: true },

  // Layered Compression
  enableLayeredCompression: true,
  layeredCompressor: { l0TokenLimit: 100, l1TokenLimit: 2000 }
});
```

---

## 11. File Structure

```
unified-memory/
├── src/
│   ├── index.js                  ← MCP Server (100+ tools)
│   ├── openviking_system.js      ← OpenViking 主系统 (v5.0)
│   ├── enhanced_memory_system.js ← 增强版记忆系统 (v4.5)
│   ├── memory_pipeline.js         ← 四层管线调度
│   │
│   ├── storage/
│   │   ├── storage.js           ← 核心存储
│   │   ├── filesystem.js         ← 文件系统范式
│   │   └── vector_factory.js      ← 双后端向量工厂
│   │
│   ├── search/
│   │   ├── hybrid_search.js      ← 混合搜索
│   │   └── intent_analyzer.js    ← 意图分析 (v5.0)
│   │
│   ├── retrieval/
│   │   ├── hierarchical_retriever.js ← 层级检索 (v5.0)
│   │   └── reranker.js           ← 重排序 (v5.0)
│   │
│   ├── extraction/
│   │   └── memory_extractor.js   ← 8 类记忆提取 (v5.0)
│   │
│   ├── compression/
│   │   ├── layered_compressor.js ← 分层压缩 (v5.0)
│   │   └── memory_compressor.js  ← 记忆压缩
│   │
│   ├── session/
│   │   └── session_manager.js    ← Session 管理 (v5.0)
│   │
│   ├── relations/
│   │   └── relation_manager.js   ← 关系管理 (v5.0)
│   │
│   ├── parsing/
│   │   └── document_parser.js    ← 文档解析 (v5.0)
│   │
│   ├── memory_types/             ← 记忆类型系统
│   │   ├── registry.js
│   │   ├── facts.js
│   │   ├── patterns.js
│   │   ├── skills.js
│   │   ├── cases.js
│   │   ├── events.js
│   │   └── preferences.js
│   │
│   ├── queue/
│   │   └── memory_queue.js       ← 异步队列
│   │
│   ├── deduplication/
│   │   └── smart_deduplicator.js ← 智能去重
│   │
│   ├── recall/
│   │   └── memory_recall_optimizer.js ← 召回优化
│   │
│   ├── lifecycle/
│   │   └── memory_lifecycle_manager.js ← 生命周期管理
│   │
│   ├── core/
│   │   ├── viking_uri.js         ← Viking URI (v5.0)
│   │   ├── transcript_first.js   ← L0 对话录制
│   │   ├── extract.js            ← L1 记忆提取
│   │   └── ...
│   │
│   ├── graph/
│   │   ├── entity_config.js      ← 可配置实体类型 (v4.4)
│   │   └── ...
│   │
│   ├── plugin/
│   │   └── plugin_manager.js     ← 插件系统 (v4.4)
│   │
│   ├── benchmark/
│   │   └── eval_recall.js        ← Benchmark (v4.4)
│   │
│   └── [80+ more modules]
│
├── docs/
│   ├── API_REFERENCE.md          ← API 参考
│   ├── ARCHITECTURE.md           ← 架构文档
│   ├── FEATURES.md               ← 功能列表
│   ├── OPENVIKING_COMPARISON.md  ← OpenViking 对比
│   └── TOKEN_SAVING_COMPARISON.md ← Token 节省对比
│
├── CHANGELOG.md
├── SKILL.md
├── QUICKSTART.md
├── QUICKSTART_V5.md
├── CONTRIBUTING.md               ← 贡献指南
└── README.md
```

---

## 12. Version History

| Version | Date | Highlights |
|---------|------|-----------|
| **v5.0.0** | 2026-04-09 | OpenViking complete integration, Enhanced Memory System |
| **v4.4.0** | 2026-04-07 | Benchmark, Configurable Entity Types, Plugin System |
| **v4.1.0** | 2026-04-06 | Four-layer pipeline, Scene induction, Chinese tokenization |
| **v4.0.6** | 2026-04-03 | Documentation restructure |
| **v3.8.10** | 2026-03-31 | Evidence TTL, WAL Operations |
| **v3.8.9** | 2026-03-31 | Team Spaces, Rate Limiting |
| **v3.8.8** | 2026-03-31 | Hybrid Search (BM25 + Vector RRF) |
| **v3.8.7** | 2026-03-31 | StorageGateway Foundation |
| **v3.8.0** | 2026-03-30 | WAL Protocol, Evidence Chain, Auto-Organize |
| **v3.5.0** | 2026-03-28 | Web UI Dashboard |
| **v2.0.0** | 2026-03-26 | Node.js ESM Rewrite, Weibull Decay |

---

*最后更新: 2026-04-09 | v5.0.0*
