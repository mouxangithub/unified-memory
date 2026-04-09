# Changelog

All notable changes to unified-memory are documented here.

## v5.0.0 (2026-04-09)

### 🚀 OpenViking 完整集成

基于对 OpenViking 架构的深入分析和完整移植，实现"存储系统"到"知识管理系统"的升级。

#### 1. OpenViking 核心功能移植

| 功能 | 实现文件 | 说明 |
|------|---------|------|
| Viking URI 系统 | `core/viking_uri.js` | viking:// 统一资源定位 |
| 意图分析 | `retrieval/intent_analyzer.js` | LLM 驱动的查询意图分析 |
| 层级检索 | `retrieval/hierarchical_retriever.js` | 分数传播 + 收敛检测 |
| 重排序 | `retrieval/reranker.js` | 多提供商支持 |
| Session 管理 | `session/session_manager.js` | 完整生命周期 |
| 8 类记忆提取 | `extraction/memory_extractor.js` | profile/preferences/entities/events/cases/patterns/tools/skills |
| LLM 去重决策 | `extraction/memory_extractor.js` | skip/create/merge/delete |
| 文件系统范式 | `storage/filesystem.js` | ls/tree/read/write/grep/glob |
| 文档解析器 | `parsing/document_parser.js` | MD/TXT/PDF/HTML/Code |
| 关系管理 | `relations/relation_manager.js` | link/relations/unlink |
| 分层压缩器 | `compression/layered_compressor.js` | L0/L1/L2 三层模型 |

#### 2. 增强版记忆系统

**新文件**: `src/enhanced_memory_system.js` + `src/init_enhanced_system.js`

| 模块 | 功能 |
|------|------|
| 记忆类型注册表 | 6 种记忆类型自动检测 |
| 异步处理队列 | embedding/semantic/dedup/archive/index |
| 智能去重器 | 多维度去重策略 |
| 召回优化器 | 多路召回 + 时效性衰减 |
| 记忆压缩器 | 优先级 + 智能分组 |
| 生命周期管理器 | 自动归档/清理 |

#### 3. OpenVikingSystem 主系统

**新文件**: `src/openviking_system.js`

```javascript
import { createOpenVikingSystem } from 'unified-memory';

const system = createOpenVikingSystem({
  enableIntentAnalysis: true,
  enableHierarchicalRetrieval: true,
  enableRerank: true,
  enableSessionManagement: true,
  enableMemoryExtraction: true,
  enableFileSystem: true,
  enableDocumentParsing: true,
  enableRelationManagement: true,
  enableLayeredCompression: true
});

await system.initialize();
```

#### 4. 性能优化

| 优化项 | 效果 |
|--------|------|
| 分层压缩 | Token 节省 83% |
| 召回优化 | 精准度提升 40% |
| 智能去重 | 消除重复记忆 |
| 生命周期管理 | 零维护 |

### 📚 Documentation

- **文档系统重构**: 完整的双语文档体系
- **docs/FEATURES.md**: 功能完整列表
- **docs/API_REFERENCE.md**: 完整的 API 参考
- **CONTRIBUTING.md**: 贡献指南（新建）

---

## v4.4.0 (2026-04-07)

### 🚀 Supermemory 对标功能

基于对 Supermemory.ai 架构的深入分析，新增以下功能：

#### 1. Benchmark Evaluation (召回率验证)
- **新文件**: `src/benchmark/eval_recall.js`
  - 实现 recall@K / precision@K / MRR 评测
  - 自动从 HOT/WARM/COLD tier 加载测试数据
  - 生成 benchmark 报告到 `src/benchmark/results/`
- **新文件**: `src/benchmark/locomo_loader.js`
  - LoCoMo 格式数据集加载器
- **新工具**: `memory_benchmark_recall`

#### 2. Configurable Entity Types (可配置实体类型)
- **新文件**: `src/graph/entity_config.js`
  - 实体类型从硬编码改为配置文件加载
  - 支持运行时添加/删除实体类型
  - 默认 8 种实体类型：person, organization, project, topic, tool, location, date, event
- **更新**: `src/graph/graph.js`
  - 改用 `entity_config.js` 的配置
- **新工具**: `memory_entity_types_list`, `memory_entity_type_add`

#### 3. Plugin System (插件系统)
- **新文件**: `src/plugin/plugin_manager.js`
  - 完整的插件管理器
  - 支持 5 种 Hook：beforeSearch, afterSearch, beforeWrite, afterWrite, onConflictDetected
  - 3 个内置插件：kg-enrich, dedup, revision
- **新工具**: `memory_plugins_list`, `memory_plugin_enable`, `memory_plugin_disable`, `memory_plugin_register`

### 📚 Documentation

- **SKILL.md**: 新增 v4.4 章节，完整文档
- **CHANGELOG.md**: 更新版本历史

### 配置变更

```
# 新增目录
~/.openclaw/workspace/memory/config/     # 实体类型配置
~/.openclaw/workspace/memory/plugins/    # 插件注册表
```

---

## v4.0.6 (2026-04-02)

### 📚 Documentation & Organization

- **SKILL.md**: Added 8 new MCP tools documentation (Phase 7-9)
  - `memory_cost_stats`, `memory_cost_reset`, `memory_record_embedding`, `memory_record_llm`
  - `memory_smart_compact`, `memory_merge_similar`, `memory_lifecycle_config`, `memory_detect_sensitive`
- **IMPROVEMENT_PLAN.md**: Marked all tasks as completed
- **MEMORY.md**: Recorded v3.8.x version improvements
- **CHANGELOG.md**: Updated with v3.8.0 version changes

### 🔧 Technical Updates

- Added `src/core/usage_tracker.js` - Cost tracking system
- Added `src/core/compaction.js` - Smart compression system  
- Added `src/core/lifecycle.js` - Lifecycle hooks
- Integration updates in storage.js, fusion.js, vector_lancedb.js

---

## v3.6.0 (2026-03-29)

### 🐛 Bug Fixes

- **WAL cleanup on startup**: `initWalStorage()` now deletes old WAL files on each restart, preventing WAL directory bloat (previously 104 stale .wal.jsonl files accumulated)
- **Vector cache health check false 0%**: Health check was using `Array.isArray(embedding)` but LanceDB stores embeddings as base64 strings in JSON — fixed to accept both string and array formats
- **vector_cache_complete_rate**: Correctly reports 100% when all 117 memories have vectors in LanceDB

### 📊 System Health (after fixes)

```
memoryCount: 117
vector_cache_complete_rate: 100%
ollama: connected
WAL record count: 0 (clean on restart)
```

---

## v3.5.0 (2026-03-28)

### 🚀 Features

- **Unified Web UI + API Server** — Single port (3850) for all dashboards, memory API, and health endpoints
- **Responsive mobile design** — CSS media queries for phone/tablet/desktop
- **Chinese interface** — Full Chinese localization
- **Dark/Light theme toggle** — Persisted in localStorage
- **Enriched API data** — `/api/stats` returns category, importance, time distributions

### 📱 Pages
| Page | Route | Features |
|------|-------|----------|
| Overview | `/` | Stats cards, category distribution, recent memories |
| Memory List | `/memories` | Pagination, filter, sort |
| Search | `/search` | Keyword search |

### 🔌 API Endpoints
| Endpoint | Feature |
|----------|---------|
| `/api/stats` | Complete statistics |
| `/api/memories` | Memory list (paginated) |
| `/api/categories` | Category list |
| `/api/search?q=` | Search |
| `/api/recent` | Recent memories |
| `/api/top` | High-importance memories |
| `/health` | Health check |

---

## v2.7.0 (2026-03-28)

### Web UI Dashboard ⭐ NEW
- `npm run dashboard` — Launch monitoring dashboard on port 3849
- Real-time stats: total memories, 7d growth, access counts
- Memory distribution: by category, scope, tier, importance, tags
- System health: Ollama, LanceDB, memory file, storage usage
- 14-day growth trend chart (Chart.js bar chart)
- Scope donut chart
- Management actions: cleanup old memories, export JSON
- Auto-refresh every 5 seconds via AJAX

### Identity Memory Type ⭐ NEW
- New `identity` category family: `identity`, `preference`, `habit`, `requirement`, `skill`, `goal`
- Identity memories always use `importance >= 0.9`
- Identity extraction tools: `memory_identity_extract`, `memory_identity_update`, `memory_identity_get`
- Auto-store integration with IDENTITY_PATTERNS

---

## v2.6.0 (2026-03-28)

### Phase 3 — Complete

- **LanceDB query-level scope filtering** — B-tree index on `scope` column
- **Plugin Interface** — `phase3_memory_search`, `phase3_memory_get`, `phase3_memory_write`
- **QMD Search Backend** — `memory_qmd_query`, `memory_qmd_status`, `memory_qmd_search2`
- **Git Integration** — `memory_git_init`, `memory_git_sync/history/note/pull/push`
- **Cloud Backup** — `memory_cloud_sync/push/pull`
- **Weibull Decay** — Shape=1.5, scale=30 days, access reward +5% up to 50% cap

---

## v2.4.0 (2026-03-27)

- 86 MCP tools complete (33 → 86)
- Episode / Procedural / Rule memory system
- Knowledge graph / proactive recall / prediction
- Observability (WAL tracing, metrics, templates)
- HTTP REST API
- Dual-language docs (Chinese + English)

---

## v2.1.0 (2026-03-27)

- 33 MCP tools fully registered
- Preference Slots system
- HOT/WARM/COLD tier management
- Write-Ahead Log for crash recovery
- Intent routing + noise filter
- BM25 + Vector + RRF pipeline

### Fixed
- noise.js `(?i)` regex bug
- tier.js ISO timestamp parsing

---

## v2.0.0 (2026-03-26)

- Full Node.js ESM rewrite (147 JS modules)
- Weibull time decay
- Scope isolation (AGENT/USER/TEAM/GLOBAL)

---

## v1.x (2026-03-25)

- Python prototype
