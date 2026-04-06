# Changelog — Unified Memory

> 统一记忆系统完整版本历史 | Consolidated Version History

All notable changes to unified-memory are documented here.

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
