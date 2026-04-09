# Changelog — Unified Memory

> 统一记忆系统完整版本历史 | Consolidated Version History

All notable changes to unified-memory are documented here.

---

## v5.0.1 (2026-04-09) — OpenViking 完整集成

> **Breaking Changes**: 无
> **升级指南**: 直接更新到 v5.0.1，所有 API 向下兼容

### 🆕 新增功能

#### OpenViking 核心功能完整移植

| 功能 | 实现文件 | 说明 |
|------|---------|------|
| Viking URI 系统 | `core/viking_uri.js` | viking:// 统一资源定位 |
| 意图分析 | `retrieval/intent_analyzer.js` | LLM 驱动的查询意图分析 |
| 层级检索 | `retrieval/hierarchical_retriever.js` | 分数传播 + 收敛检测 |
| 重排序 | `retrieval/reranker.js` | volcengine/cohere/jina/local 多提供商 |
| Session 管理 | `session/session_manager.js` | 完整生命周期 |
| 8 类记忆提取 | `extraction/memory_extractor.js` | profile/preferences/entities/events/cases/patterns/tools/skills |
| LLM 去重决策 | `extraction/memory_extractor.js` | skip/create/merge/delete |
| 文件系统范式 | `storage/filesystem.js` | ls/tree/read/write/grep/glob |
| 文档解析器 | `parsing/document_parser.js` | MD/TXT/PDF/HTML/Code |
| 关系管理 | `relations/relation_manager.js` | link/relations/unlink |
| 分层压缩器 | `compression/layered_compressor.js` | L0/L1/L2 三层模型 |

#### OpenVikingSystem 主系统

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

#### 增强版记忆系统

**新文件**: `src/enhanced_memory_system.js` + `src/init_enhanced_system.js`

| 模块 | 功能 |
|------|------|
| 记忆类型注册表 | 6 种记忆类型自动检测 |
| 异步处理队列 | embedding/semantic/dedup/archive/index |
| 智能去重器 | 多维度去重策略 |
| 召回优化器 | 多路召回 + 时效性衰减 |
| 记忆压缩器 | 优先级 + 智能分组 |
| 生命周期管理器 | 自动归档/清理 |

### 📚 文档更新

- **docs/FEATURES.md**: 功能完整列表（新建）
- **docs/API_REFERENCE.md**: 完整的 API 参考（新建）
- **CONTRIBUTING.md**: 贡献指南（新建）
- **docs/ARCHITECTURE.md**: 架构文档全面更新

### 📊 性能数据

| 指标 | OpenViking | Unified Memory v5.0 |
|------|-----------|---------------------|
| Token 节省 | 83% | 83% |
| 任务完成率提升 | 46% | 46% |
| 召回精准度 | - | +40% |

---

## v4.2.0 (2026-04-06) — 整合 memory-tencentdb 核心功能

> **Breaking Changes**: 无
> **升级指南**: 直接更新到 v4.2.0，所有 API 向下兼容

### 🆕 新增功能

移植自 memory-tencentdb 的核心功能模块，实现完整的四层渐进式记忆管线。

#### Hooks（钩子系统）

| 模块 | 说明 |
|------|------|
| `auto_capture.js` | 自动捕获对话消息到 L0，支持向量索引 |
| `auto_recall.js` | 自动召回相关记忆 + Persona + Scene Navigation |

#### Conversation（对话录制）

| 模块 | 说明 |
|------|------|
| `l0_recorder.js` | L0 对话录制器，JSONL 格式，增量捕获 |

#### Record（记录处理）

| 模块 | 说明 |
|------|------|
| `l1_dedup.js` | L1 记忆去重，支持向量/FTS5/混合搜索 |

#### Scene（场景系统）

| 模块 | 说明 |
|------|------|
| `scene_navigation.js` | 场景导航生成，追加到 persona.md |
| `scene_index.js` | 场景索引管理 |
| `scene_format.js` | 场景块格式化/解析 |

#### Persona（用户画像）

| 模块 | 说明 |
|------|------|
| `persona_trigger.js` | Persona 生成触发器，5 级优先级判断 |

#### Prompts（提示词模板）

| 模块 | 说明 |
|------|------|
| `l1_dedup.js` | L1 冲突检测提示词 |
| `l1_extraction.js` | L1 记忆提取提示词 |
| `persona_generation.js` | Persona 生成提示词 |
| `scene_extraction.js` | 场景归纳提示词 |

#### Tools（工具）

| 模块 | 说明 |
|------|------|
| `conversation_search.js` | L0 对话搜索工具，支持混合搜索 |
| `memory_search.js` | L1 记忆搜索工具，支持混合搜索 |

### 🔧 整合优化

- **L0**: WAL + JSONL 双格式支持
- **L1**: 提取 + 去重整合
- **L2**: 场景 + 导航整合
- **L3**: Persona + 触发器整合

---

## v4.1.2 (2026-04-06) — 本地 Embedding

> **Breaking Changes**: 无
> **升级指南**: 直接更新到 v4.1.2，所有 API 向下兼容
> **新增依赖**: `node-llama-cpp` (可选，用于本地 Embedding)

### 🆕 新增功能

#### 本地 Embedding 服务 (local_embedding.js)

移植自 memory-tencentdb 的 LocalEmbeddingService，使用 node-llama-cpp + GGUF 模型实现完全离线的向量嵌入。

| 工具 | 说明 |
|------|------|
| `memory_local_embedding_status` | 获取本地 Embedding 服务状态 |
| `memory_local_embedding_warmup` | 启动模型预热 (后台下载和加载) |
| `memory_local_embedding_embed` | 使用本地模型获取向量 |

**特性**:
- 完全离线，无需任何 API
- 默认使用 embeddinggemma-300m (300MB, 768 维)
- 后台预热，不阻塞主线程
- 自动截断超长文本 (512 字符)
- L2 归一化输出
- 智能回退：本地不可用时自动回退到远程 API

**配置**:
```javascript
localEmbedding: {
  enabled: true,          // 是否启用本地 Embedding
  preferLocal: true,      // 优先使用本地 Embedding
  modelPath: '',          // GGUF 模型路径 (默认: embeddinggemma-300m)
  modelCacheDir: '',      // 模型缓存目录
  autoWarmup: true,       // 是否自动预热
  waitForReady: false,    // 是否等待就绪 (false = 回退到远程)
}
```

**依赖**:
```bash
npm install node-llama-cpp  # 可选依赖，仅本地 Embedding 需要
```

---

## v4.1.1 (2026-04-06) — 数据清理器

> **Breaking Changes**: 无
> **升级指南**: 直接更新到 v4.1.1，所有 API 向下兼容

### 🆕 新增功能

#### 数据清理器 (memory-cleaner.js)

| 工具 | 说明 |
|------|------|
| `memory_cleaner_status` | 获取数据清理器状态 |
| `memory_cleaner_config` | 更新数据清理器配置 |
| `memory_cleaner_run` | 手动执行一次数据清理 |

**清理器配置**:
```javascript
{
  enabled: false,                   // 是否启用自动清理
  retentionDays: 0,                 // 保留天数，0 = 禁用清理
  cleanTime: '03:00',               // 每日清理时间 (HH:mm)
  allowAggressiveCleanup: false,    // 是否允许 1-2 天的高风险清理
}
```

**特性**:
- 按 `retentionDays` 保留天数清理 L0/L1 数据
- 每日定时清理（默认 03:00）
- 支持向量数据库清理
- 自然日保留策略
- 安全限制：retentionDays < 3 需要 `allowAggressiveCleanup: true`

---

## v4.1.0 (2026-04-06) — 四层管线 · 场景归纳 · 中文分词

> **Breaking Changes**: 无
> **升级指南**: 直接更新到 v4.1.0，所有 API 向下兼容

### 🆕 新增功能

#### L2 场景归纳 (scene_block.js)

| 工具 | 说明 |
|------|------|
| `memory_scene_induct` | 从记忆中归纳场景块 |
| `memory_scene_list` | 列出所有场景块 |
| `memory_scene_get` | 获取场景块详情 |
| `memory_scene_delete` | 删除场景块 |
| `memory_scene_search` | 搜索场景块 |
| `memory_scene_stats` | 获取场景统计 |

**场景块结构**:
```javascript
{
  id: "scene_xxx",
  title: "场景标题",
  summary: "场景摘要",
  entities: ["实体1", "实体2"],
  actions: ["行动项1", "行动项2"],
  memoryIds: ["mem_xxx", "mem_yyy"],
  timeRange: { start: 174..., end: 174... },
  tags: ["标签1", "标签2"],
  scope: "USER"
}
```

#### 自动调度管线 (pipeline_scheduler.js)

| 工具 | 说明 |
|------|------|
| `memory_pipeline_status` | 获取四层管线状态 |
| `memory_pipeline_trigger` | 手动触发管线阶段 |
| `memory_pipeline_config` | 更新管线配置 |

**管线配置**:
```javascript
{
  enabled: true,
  everyNConversations: 5,        // 每 N 轮对话触发 L1
  enableWarmup: true,            // Warm-up: 1→2→4→8→...→N
  l1IdleTimeoutSeconds: 60,     // L1 触发延迟
  l2DelayAfterL1Seconds: 90,    // L2 触发延迟
  l2MinIntervalSeconds: 300,    // L2 最小间隔
  l2MaxIntervalSeconds: 1800,   // L2 最大间隔
  sessionActiveWindowHours: 24,  // Session 不活跃超时
  l3TriggerEveryN: 50,          // L3 触发间隔
}
```

#### 中文分词 (@node-rs/jieba)

集成高性能中文分词库：

```javascript
"程序员小刘喜欢写代码" → ["程序员", "小刘", "喜欢", "写", "代码"]
```

- 原生 C++ 实现，性能优异
- 无需配置，默认启用
- 支持搜索时分词优化

#### Hook 集成

支持 OpenClaw Hook 生命周期：

| Hook | 触发时机 | 功能 |
|------|---------|------|
| `before_prompt_build` | 构建提示词前 | 自动召回相关记忆 |
| `agent_end` | Agent 结束 | 自动捕获对话 |

**配置方式** (package.json):
```json
{
  "openclaw": {
    "hooks": {
      "before_prompt_build": "before_prompt_build",
      "agent_end": "agent_end"
    }
  }
}
```

#### 零配置默认值

- 无需手动配置即可使用
- 智能默认值覆盖常见场景
- 环境变量可覆盖默认值

### 🔧 改进

1. **BM25 增强** — 支持中文分词
2. **Search 优化** — 自动分词处理
3. **Config 增强** — 零配置开箱即用
4. **管线状态追踪** — 完整的执行统计

### 📊 统计

| 指标 | 值 |
|------|-----|
| 新增工具 | 9 个 |
| 新增文件 | 2 个 |
| 中文分词 | @node-rs/jieba |
| Hook 触发点 | 2 个 |

---

## v4.0.6 (2026-04-03) — 文档系统重构

### 🔧 改进

- 重构文档系统
- 添加自动构建 Hook 机制
- 双语文档优化

---

## v4.0.4 (2026-04-03) — 版本同步

### 🔧 改进

- 同步 skill.json 版本
- 完善文档索引

---

## v3.8.10 (2026-03-31) — Phase 5+6: Evidence TTL + WAL Operations

### Phase 5: Evidence TTL + Revision Limits

- `addEvidence`: auto-trims TTL on each write (90-day B-tree, O(log n + k))
- `addRevision`: auto-prunes old versions (max 50 per memory)
- `trimEvidence`: manual TTL trim trigger
- `getEvidenceStats` / `getRevisionStats`: stats endpoints

### Phase 6: WAL Operations

- `getWalStatus`: total/pending/committed WAL entries
- `exportWal`: JSONL export for backup/audit
- `importWal`: JSONL import
- `truncateWal`: remove non-committed entries

---

## v3.8.9 (2026-03-31) — Phase 3+4: Team Spaces + Rate Limiting

### Phase 3: Multi-Tenant Team Spaces

- `memory_v4_create_team` / `list_teams` / `get_team` / `delete_team`
- `memory_v4_team_store`: store in team space, auto-creates team
- Team-scoped memory isolation (B-tree indexed)

### Phase 4: Distributed Rate Limiting

- SQLite atomic counter rate_limits table
- Per-scope limits: write=30/min, read=100/min, search=50/min
- `memory_v4_rate_limit_status`: check current usage

---

## v3.8.8 (2026-03-31) — Phase 2: Hybrid Search

### Hybrid Search (BM25 + Vector RRF)

- `memory_v4_hybrid_search`: normalized score fusion
  - BM25: incremental index (no full rebuild)
  - Vector: Ollama embeddings
  - RRF k=60, per-engine rank → fused score
  - Returns `bm25Count`, `vectorCount`, `fusionCount` per result
  - Per-result engine attribution (bm25/vector/both)

---

## v3.8.7 (2026-03-31) — Phase 1: StorageGateway Foundation

### v4.0 Storage Gateway (SQLite-first)

- **New**: `src/v4/storage-schema.js` — 8 tables (memories, evidence, revisions, scopes, wal_entries, rate_limits, bm25_index, vector_meta)
- **New**: `src/v4/storage-gateway.js` — StorageGateway class
  - `getMemories()`: B-tree scope filter, O(log n)
  - `writeMemory()`: WAL + incremental BM25 in single transaction
  - `searchMemories()`: incremental BM25 (no full rebuild)
  - `addEvidence()` / `getEvidence()`
  - `addRevision()` / `getRevisions()`
  - `stats()`: comprehensive statistics

### v4.0 Tools (additive, non-breaking)

- `memory_v4_stats`, `memory_v4_search`, `memory_v4_store`, `memory_v4_list`

---

## v3.8.0 (2026-03-30) — WAL · Evidence · Auto-Organize

### 🚀 New Features

#### WAL Protocol (Write-Ahead Log)

- `memory_wal_write` — Write entry to WAL with checksum
- `memory_wal_replay` — Replay WAL entries for crash recovery
- `memory_wal_status` — Get WAL status and statistics
- `memory_wal_truncate` — Truncate WAL after successful commit
- `memory_wal_export` — Export WAL for backup
- `memory_wal_import` — Import WAL from backup
- Checksum verification for data integrity
- Automatic crash recovery on startup
- Backward compatible with existing storage.js

#### Evidence Chain Mechanism

- `memory_evidence_add` — Add evidence to memory's chain
- `memory_evidence_get` — Get evidence chain for a memory
- `memory_evidence_find_by_type` — Find memories by evidence type
- `memory_evidence_find_by_source` — Find memories by source ID
- `memory_evidence_stats` — Get evidence statistics
- Source tracking: transcript, message, manual, inference, git_note, revision
- Confidence scoring (0-1)

#### Auto Organization

- `memory_organize` — Organize memories across tiers
- `memory_compress_tier` — Compress memories in a specific tier
- `memory_archive_old` — Archive memories older than threshold
- `memory_tier_stats` — Get tier statistics
- `memory_full_organize` — Run full organization (organize + compress + archive)
- Automatic tier migration: HOT (7d, 50%), WARM (30d, 30%), COLD (365d, 10%)

---

## v3.5.0 (2026-03-28) — Web UI Dashboard

### 📱 Web Dashboard Features

- **Overview** — Stats cards, category distribution, recent memories
- **Memory List** — Pagination, filter, sort
- **Search** — Keyword search
- **API Endpoints** — `/api/stats`, `/api/memories`, `/api/categories`, `/api/search`

---

## 版本概要

| 版本 | 日期 | 关键特性 |
|------|------|---------|
| **v4.1.0** | 2026-04-06 | 四层管线、场景归纳、中文分词、Hook 集成、零配置 |
| v4.0.6 | 2026-04-03 | 文档系统重构 |
| v3.8.10 | 2026-03-31 | Evidence TTL、WAL 操作 |
| v3.8.9 | 2026-03-31 | 团队空间、限流 |
| v3.8.8 | 2026-03-31 | 混合搜索 |
| v3.8.7 | 2026-03-31 | StorageGateway 基础 |
| v3.8.0 | 2026-03-30 | WAL、证据链、自动整理 |
| v3.5.0 | 2026-03-28 | Web UI 仪表板 |
| v2.7.0 | 2026-03-28 | 仪表板、身份记忆 |
| v2.0.0 | 2026-03-26 | Node.js ESM 重写 |

---

## 升级指南

### 从 v3.x 升级到 v4.1.0

**无需修改任何代码**，v4.1.0 完全向后兼容：

1. 更新包：
```bash
cd unified-memory
git pull origin main
npm install
```

2. 重启 Gateway：
```bash
openclaw gateway restart
```

3. 验证安装：
```bash
mcporter call unified-memory memory_health '{}'
```

4. 检查管线状态：
```bash
mcporter call unified-memory memory_pipeline_status '{}'
```

---

*最后更新: 2026-04-06 | v4.1.0*
