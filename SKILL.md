# Unified Memory — SKILL.md

> Authoritative technical reference for the unified-memory skill.  
> For overview and quick start, see [README.md](./README.md).  
> 权威技术参考文档，详细使用说明请参考 [README.md](./README.md)。

---

## Metadata

| Field | Value |
|-------|-------|
| **Name** | `unified-memory` |
| **Version** | `4.1.0` (see [docs/CHANGELOG.md](./docs/CHANGELOG.md)) |
| **Framework** | OpenClaw Agent · Node.js ESM · MCP stdio |
| **Node** | `>=18.0.0` |
| **OpenClaw** | `>=2026.3.0` |
| **Transport** | `stdio` (MCP over node `src/index.js`) |

---

## v4.1 新功能 (借鉴 memory-tencentdb)

### 🎯 四层渐进式管线 (L0→L1→L2→L3)

```
L0 (对话录制) → transcript_first.js ✅
      ↓
L1 (记忆提取) → extract.js ✅
      ↓
L2 (场景归纳) → scene_block.js 🆕
      ↓
L3 (用户画像) → profile.js ✅
```

### 🆕 新增工具

| 工具 | 功能 |
|------|------|
| `memory_scene_induct` | 从记忆中归纳场景块 (L2) |
| `memory_scene_list` | 列出所有场景块 |
| `memory_scene_get` | 获取场景块详情 |
| `memory_scene_delete` | 删除场景块 |
| `memory_scene_search` | 搜索场景块 |
| `memory_scene_stats` | 获取场景统计 |
| `memory_pipeline_status` | 获取四层管线状态 |
| `memory_pipeline_trigger` | 手动触发管线阶段 |
| `memory_pipeline_config` | 更新管线配置 |

### 🔧 改进功能

1. **中文分词** — 集成 @node-rs/jieba，中文搜索效果更好
2. **自动调度** — Pipeline Scheduler 自动管理 L0→L1→L2→L3
3. **零配置** — 开箱即用默认值，无需手动配置
4. **Hook 集成** — `before_prompt_build` 自动召回，`agent_end` 自动捕获

---

## Installation

```bash
# Option 1: ClawHub (recommended)
clawhub install unified-memory

# Option 2: Manual
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install

# Verify
mcporter call unified-memory memory_health '{}'
```

---

## Triggers / 触发词

When any of these keywords or commands appear in a user message, this skill activates automatically:

| Type | Keywords / Commands |
|------|---------------------|
| **Keywords** (EN) | `memory`, `recall`, `forget`, `remember`, `知识库` |
| **Keywords** (中文) | `记忆`, `记住`, `记一下`, `我想知道` |
| **Commands** | `/memory` |

---

## Permissions / 权限

```json
{
  "filesystem": {
    "read":  ["~/.openclaw/workspace/memory/"],
    "write": ["~/.openclaw/workspace/memory/"]
  },
  "env": ["OLLAMA_HOST", "OLLAMA_EMBED_MODEL", "STORAGE_MODE"]
}
```

---

## Environment Variables / 环境变量

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `LLM_MODEL` | `qwen2.5:7b` | LLM model for generation tasks |
| `LLM_PROVIDER` | `ollama` | LLM provider |
| `VECTOR_ENGINE` | `lancedb` | Vector database backend |
| `STORAGE_MODE` | `json` | Storage backend: `json` or `sqlite` |
| `OPENCLAW_WORKSPACE_DIR` | `~/.openclaw/workspace` | Workspace directory |

<!-- zh -->
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API 地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `LLM_MODEL` | `qwen2.5:7b` | 生成任务用的大模型 |
| `LLM_PROVIDER` | `ollama` | 大模型 provider |
| `VECTOR_ENGINE` | `lancedb` | 向量数据库后端 |
| `STORAGE_MODE` | `json` | 存储后端：`json` 或 `sqlite` |
| `OPENCLAW_WORKSPACE_DIR` | `~/.openclaw/workspace` | 工作目录 |
-->

---

## v4.0 Tools (17 tools) / v4.0 工具 (17个)

> **v4.0 is the recommended path** for all new development. Built on SQLite-first StorageGateway with incremental indexes, multi-tenant team spaces, and distributed rate limiting.
> v4.0 新存储后端，基于 SQLite + 增量索引，推荐所有新开发使用。

All v4 tools: `mcporter call unified-memory <tool-name> '<json-args>'`

### v4.0 Phase 1: StorageGateway Foundation

| Tool | Description |
|------|-------------|
| `memory_v4_stats` | StorageGateway statistics (memory count, evidence, revisions, WAL) |
| `memory_v4_search` | Incremental BM25 search (no full rebuild on new documents) |
| `memory_v4_store` | WAL + incremental index in single SQLite transaction |
| `memory_v4_list` | B-tree scope-filtered memory listing |

### v4.0 Phase 2: Hybrid Search

| Tool | Description |
|------|-------------|
| `memory_v4_hybrid_search` | BM25 + Ollama vector RRF fusion with normalized scores |

### v4.0 Phase 3: Multi-Tenant Team Spaces

| Tool | Description |
|------|-------------|
| `memory_v4_create_team` | Create a team space |
| `memory_v4_list_teams` | List all teams |
| `memory_v4_get_team` | Get team config + memory count |
| `memory_v4_delete_team` | Delete team (memories preserved) |
| `memory_v4_team_store` | Store memory in team space (auto-creates team) |
| `memory_v4_team_search` | **Strict team isolation** — only team memories, never leaks to USER/GLOBAL scope |
| `memory_v4_team_search` | **Strict team isolation search** — only team memories, never leaks to USER/GLOBAL scope |

### v4.0 Phase 4: Distributed Rate Limiting

| Tool | Description |
|------|-------------|
| `memory_v4_rate_limit_status` | Check current rate limit (write/read/search) |

### v4.0 Phase 5: Evidence TTL + Revision Limits

| Tool | Description |
|------|-------------|
| `memory_v4_evidence_stats` | Evidence chain stats (TTL 90-day) |
| `memory_v4_trim_evidence` | Manually trigger TTL trim |
| `memory_v4_revision_stats` | Revision history stats (max 50/memory) |

### v4.0 Phase 6: WAL Operations

| Tool | Description |
|------|-------------|
| `memory_v4_wal_status` | WAL status (total/pending/committed) |
| `memory_v4_wal_export` | Export WAL as JSONL |
| `memory_v4_wal_truncate` | Remove non-committed WAL entries |

<!-- zh -->
### v4.0 Phase 1: StorageGateway 基础

| 工具 | 说明 |
|------|------|
| `memory_v4_stats` | 存储网关统计（记忆数、evidence、版本、WAL） |
| `memory_v4_search` | 增量 BM25 搜索（新文档无需全量重建） |
| `memory_v4_store` | WAL + 增量索引单 SQLite 事务 |
| `memory_v4_list` | B-tree 范围过滤列表 |

### v4.0 Phase 2: 混合搜索

| 工具 | 说明 |
|------|------|
| `memory_v4_hybrid_search` | BM25 + Ollama 向量 RRF 融合，归一化分数 |

### v4.0 Phase 3: 多租户团队空间

| 工具 | 说明 |
|------|------|
| `memory_v4_create_team` | 创建团队空间 |
| `memory_v4_list_teams` | 列出所有团队 |
| `memory_v4_get_team` | 获取团队配置 + 记忆数 |
| `memory_v4_delete_team` | 删除团队（记忆保留） |
| `memory_v4_team_store` | 在团队空间中存储记忆（自动创建团队） |
| `memory_v4_team_search` | **严格团队隔离搜索** — 仅搜团队内记忆，绝不泄露到 USER/GLOBAL |

### v4.0 Phase 4: 分布式限流

| 工具 | 说明 |
|------|------|
| `memory_v4_rate_limit_status` | 查看当前限流状态（写/读/搜索） |

### v4.0 Phase 5: Evidence TTL + 版本限制

| 工具 | 说明 |
|------|------|
| `memory_v4_evidence_stats` | Evidence 链统计（TTL 90天） |
| `memory_v4_trim_evidence` | 手动触发 TTL 清理 |
| `memory_v4_revision_stats` | 版本历史统计（最多50条/记忆） |

### v4.0 Phase 6: WAL 操作

| 工具 | 说明 |
|------|------|
| `memory_v4_wal_status` | WAL 状态（总数/pending/committed） |
| `memory_v4_wal_export` | JSONL 导出 WAL |
| `memory_v4_wal_truncate` | 删除未提交的 WAL 条目 |
-->

---

## MCP Tools (79 tools) / MCP 工具 (79个)

> ⚠️ **Legacy v3 tools** — 79 tools from the v3.x series. For new development, use **v4.0 tools** above.
> v3 工具 — 遗留工具集。新开发请使用上方 v4.0 工具。

All tools are called via `mcporter call unified-memory <tool-name> <args>`.

所有工具通过 `mcporter call unified-memory <tool-name> <args>` 调用。

---

### 🔍 Search & Retrieval / 搜索与检索

| Tool | Description |
|------|-------------|
| `memory_search` | Hybrid BM25 + Vector search with scope filtering. Returns ranked results with highlights. |
| `memory_list` | List memories with optional pagination and scope filter. |
| `memory_concurrent_search` | Parallel multi-query search for faster coverage. |
| `memory_recommend` | Recommend relevant memories based on current context. |
| `memory_qmd` | QMD (Query Memory Document) structured search. |
| `memory_noise` | Filter noise — skip generic or meaningless queries. |
| `memory_intent` | Detect user intent and route to appropriate handler. |

<!-- zh -->
| 工具 | 说明 |
|------|------|
| `memory_search` | 混合搜索：BM25 + 向量检索，支持范围过滤，返回排序结果和摘要高亮。 |
| `memory_list` | 列出记忆，支持分页和范围过滤。 |
| `memory_concurrent_search` | 并发多查询搜索，更快覆盖。 |
| `memory_recommend` | 根据当前上下文推荐相关记忆。 |
| `memory_qmd` | QMD 结构化查询。 |
| `memory_noise` | 过滤无意义查询。 |
| `memory_intent` | 检测用户意图并路由到合适的处理器。 |
-->

---

### 💾 Storage & Persistence / 存储与持久化

| Tool | Description |
|------|-------------|
| `memory_store` | Store a new memory with text, category, importance, tags, scope. |
| `memory_delete` | Delete a memory by ID. |
| `memory_pin` | Pin a memory to prevent decay and deletion. |
| `memory_unpin` | Unpin a pinned memory. |
| `memory_pins` | List all pinned memories. |
| `memory_export` | Export memories in JSON, CSV, or Markdown format. |
| `memory_cloud_backup` | Backup all memories to cloud storage. |
| `memory_cloud_restore` | Restore memories from cloud backup. |
| `memory_sync` | Sync memories with external sources. |

<!-- zh -->
| 工具 | 说明 |
|------|------|
| `memory_store` | 存储新记忆，支持文本、分类、重要度、标签、范围。 |
| `memory_delete` | 按 ID 删除记忆。 |
| `memory_pin` | 置顶记忆，防止衰减和删除。 |
| `memory_unpin` | 取消置顶。 |
| `memory_pins` | 列出所有置顶记忆。 |
| `memory_export` | 导出记忆为 JSON/CSV/Markdown 格式。 |
| `memory_cloud_backup` | 备份到云存储。 |
| `memory_cloud_restore` | 从云备份恢复。 |
| `memory_sync` | 与外部数据源同步。 |
-->

---

### 🧠 Intelligence / 智能处理

| Tool | Description |
|------|-------------|
| `memory_extract` | Extract entities, relations, and facts from text using LLM. |
| `memory_reflection` | Reflect on past memories to identify patterns and insights. |
| `memory_lessons` | Generate and store lessons learned from experiences. |
| `memory_preference` | Learn and apply user preferences. |
| `memory_inference` | Infer new facts from existing memories (logical reasoning). |
| `memory_adaptive` | Adapt search and retrieval based on usage patterns. |
| `memory_compress_tier` | Compress low-importance memories to save tokens. |
| `memory_identity_extract` | Extract identity information from memories. |
| `memory_identity_get` | Get stored identity profiles. |
| `memory_identity_update` | Update identity profiles. |

<!-- zh -->
| 工具 | 说明 |
|------|------|
| `memory_extract` | 用 LLM 从文本中提取实体、关系和事实。 |
| `memory_reflection` | 反思过去的记忆，识别模式和洞察。 |
| `memory_lessons` | 从经验中生成和存储教训。 |
| `memory_preference` | 学习和应用用户偏好。 |
| `memory_inference` | 从现有记忆推断新事实（逻辑推理）。 |
| `memory_adaptive` | 根据使用模式调整搜索和检索。 |
| `memory_compress_tier` | 压缩低重要度记忆以节省 token。 |
| `memory_identity_extract` | 从记忆中提取身份信息。 |
| `memory_identity_get` | 获取存储的身份档案。 |
| `memory_identity_update` | 更新身份档案。 |
-->

---

### 📊 Analysis & Management / 分析与管理

| Tool | Description |
|------|-------------|
| `memory_stats` | Get memory statistics: count, categories, tags, distribution. |
| `memory_health` | Health check: storage, vector DB, WAL integrity, Ollama status. |
| `memory_metrics` | Get detailed usage metrics and performance data. |
| `memory_budget` | Get token budget status and allocation. |
| `memory_tier` | Manage memory tiers (HOT/WARM/COLD) and view tier stats. |
| `memory_tier_stats` | Statistics for each tier. |
| `memory_decay` | Get decay scores for memories. |
| `memory_dedup` | Deduplicate memories by text similarity. |
| `memory_organize` | Organize memories by category, tag, or time. |
| `memory_full_organize` | Full reorganization of all memories. |
| `memory_cache` | Cache management for vector and BM25 indexes. |
| `memory_cognitive` | Cognitive analysis of memory patterns. |
| `memory_scope` | Manage scope assignments and filters. |
| `memory_archive_old` | Archive old memories automatically. |
| `memory_lanes` | Lane-based memory isolation for multi-agent scenarios. |
| `memory_dashboard` | Access the web dashboard data. |
| `memory_wal` | WAL (Write-Ahead Log) status and operations. |
| `memory_wal_status` | Get WAL integrity status. |
| `memory_wal_export` | Export WAL operations. |
| `memory_wal_import` | Import WAL operations. |
| `memory_wal_replay` | Replay WAL operations. |
| `memory_wal_truncate` | Truncate WAL. |
| `memory_wal_write` | Write a WAL entry directly. |
| `memory_engine` | Get/set storage engine configuration. |
| `memory_graph` | Knowledge graph operations. |
| `memory_summary` | Generate a summary of memories. |
| `memory_templates` | Use templates for structured memory storage. |
| `memory_qa` | Question answering over stored memories. |
| `memory_version` | Version history management for memories. |
| `memory_evidence_stats` | Evidence chain statistics. |
| `memory_evidence_add` | Add evidence to a memory's chain. |
| `memory_evidence_get` | Get evidence chain for a memory. |
| `memory_evidence_find_by_source` | Find evidence by source ID. |
| `memory_evidence_find_by_type` | Find evidence by type. |
| `memory_proactive` | Proactive memory management and suggestions. |
| `memory_proactive_care` | Proactive care: monitor and maintain important memories. |
| `memory_proactive_recall` | Proactive recall: remind user of relevant past memories. |
| `memory_reminder` | Set reminders based on memory content. |
| `memory_trace` | Trace memory access and modification history. |
| `memory_transcript` | Transcript management for context capture. |
| `memory_transcript_add` | Add a transcript entry. |
| `memory_transcript_compact` | Compact transcript data. |
| `memory_transcript_delete` | Delete transcript entries. |
| `memory_transcript_find_by_source` | Find transcript entries by source. |
| `memory_transcript_get` | Get transcript entry. |
| `memory_transcript_list` | List transcript entries. |
| `memory_transcript_rebuild` | Rebuild transcript index. |
| `memory_transcript_stats` | Transcript statistics. |
| `memory_transcript_summary` | Generate transcript summary. |
| `memory_transcript_update` | Update transcript entry. |
| `memory_transcript_verify` | Verify transcript integrity. |
| `memory_session` | Session memory management. |
| `memory_git_notes` | Git commit message memory. |
| `memory_gitnotes_backup` | Backup git notes. |
| `memory_gitnotes_restore` | Restore git notes. |
| `memory_cloud_backup_api` | Cloud backup API management. |

<!-- zh -->
| 工具 | 说明 |
|------|------|
| `memory_stats` | 记忆统计：数量、分类、标签、分布。 |
| `memory_health` | 健康检查：存储、向量库、WAL 完整性、Ollama 状态。 |
| `memory_metrics` | 详细使用指标和性能数据。 |
| `memory_budget` | Token 预算状态和分配。 |
| `memory_tier` | 管理记忆层级（HOT/WARM/COLD）并查看层级统计。 |
| `memory_tier_stats` | 各层级统计。 |
| `memory_decay` | 获取记忆衰减分数。 |
| `memory_dedup` | 按文本相似度去重。 |
| `memory_organize` | 按分类/标签/时间整理记忆。 |
| `memory_full_organize` | 全量整理所有记忆。 |
| `memory_cache` | 向量和 BM25 索引缓存管理。 |
| `memory_cognitive` | 记忆模式认知分析。 |
| `memory_scope` | 范围分配和过滤管理。 |
| `memory_archive_old` | 自动归档旧记忆。 |
| `memory_lanes` | 多 Agent 场景的通道隔离。 |
| `memory_dashboard` | 访问 Web 仪表盘数据。 |
| `memory_wal_*` | WAL（预写日志）相关操作（状态/导出/导入/回放/截断/写入）。 |
| `memory_engine` | 获取/设置存储引擎配置。 |
| `memory_graph` | 知识图谱操作。 |
| `memory_summary` | 生成记忆摘要。 |
| `memory_templates` | 使用模板存储结构化记忆。 |
| `memory_qa` | 基于记忆的问答。 |
| `memory_version` | 记忆版本历史管理。 |
| `memory_evidence_*` | Evidence Chain 操作（统计/添加/获取/按源查找/按类型查找）。 |
| `memory_proactive_*` | 主动记忆管理（建议/关怀/提醒）。 |
| `memory_reminder` | 根据记忆内容设置提醒。 |
| `memory_trace` | 记忆访问和修改历史追踪。 |
| `memory_transcript_*` | Transcript（会话记录）完整操作集。 |
| `memory_session` | 会话记忆管理。 |
| `memory_git_notes*` | Git notes 备份和恢复。 |
| `memory_cloud_backup_api` | 云备份 API 管理。 |
-->

---

## Quick Usage Examples / 快速使用示例

```bash
# Health check
mcporter call unified-memory memory_health '{}'

# Store a memory
mcporter call unified-memory memory_store '{"text": "用户偏好简洁风格", "category": "preference", "importance": 0.8}'

# Search memories
mcporter call unified-memory memory_search '{"query": "用户偏好", "topK": 5}'

# List with pagination
mcporter call unified-memory memory_list '{"page": 1, "pageSize": 20}'

# Get statistics
mcporter call unified-memory memory_stats '{}'

# Delete
mcporter call unified-memory memory_delete '{"id": "mem_xxx"}'

# Export
mcporter call unified-memory memory_export '{"format": "json"}'

# Evidence chain
mcporter call unified-memory memory_evidence_add '{"memoryId": "mem_xxx", "type": "transcript", "sourceId": "msg_123"}'

# Version history
mcporter call unified-memory memory_version '{"memoryId": "mem_xxx"}'
```

<!-- zh -->
```bash
# 健康检查
mcporter call unified-memory memory_health '{}'

# 存储记忆
mcporter call unified-memory memory_store '{"text": "用户偏好简洁风格", "category": "preference", "importance": 0.8}'

# 搜索记忆
mcporter call unified-memory memory_search '{"query": "用户偏好", "topK": 5}'

# 分页列表
mcporter call unified-memory memory_list '{"page": 1, "pageSize": 20}'

# 统计
mcporter call unified-memory memory_stats '{}'

# 删除
mcporter call unified-memory memory_delete '{"id": "mem_xxx"}'

# 导出
mcporter call unified-memory memory_export '{"format": "json"}'

# Evidence 链
mcporter call unified-memory memory_evidence_add '{"memoryId": "mem_xxx", "type": "transcript", "sourceId": "msg_123"}'

# 版本历史
mcporter call unified-memory memory_version '{"memoryId": "mem_xxx"}'
```
-->

---

## Scope System / 范围系统

Memories are isolated by **scope**:

| Scope | Description |
|-------|-------------|
| `USER` | Private to the current user (default) |
| `TEAM` | Shared within a team |
| `AGENT` | Agent-specific memory |
| `GLOBAL` | Accessible to all agents and users |

Scope filtering is O(1) via in-memory Map index. See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for details.

<!-- zh -->
| 范围 | 说明 |
|------|------|
| `USER` | 当前用户私有（默认） |
| `TEAM` | 团队内共享 |
| `AGENT` | Agent 专用 |
| `GLOBAL` | 所有 Agent 和用户可访问 |

范围过滤通过内存 Map 索引实现 O(1) 查询，详见 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)。 |
-->

---

## Storage Backends / 存储后端

| Backend | Mode | Description |
|---------|------|-------------|
| `json` (default) | File-based | `memories.json` with write-behind buffering |
| `sqlite` | Database | SQLite via `storage_sqlite.js`, enabled by `STORAGE_MODE=sqlite` |

SQLite backend provides better concurrency and I/O performance for high-throughput scenarios.

<!-- zh -->
| 后端 | 模式 | 说明 |
|------|------|------|
| `json`（默认） | 文件 | `memories.json`，写缓冲优化 |
| `sqlite` | 数据库 | `STORAGE_MODE=sqlite` 启用，提供更好的并发和 I/O 性能 |
-->

---

## Architecture Overview / 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    index.js (MCP Server)            │
│              79 registered tools / 79个注册工具      │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌──────────┐
│storage │  │  BM25  │  │  Vector   │
│.js     │  │.js     │  │(LanceDB)  │
└────┬───┘  └────┬───┘  └─────┬────┘
     │            │            │
     ▼            ▼            ▼
┌─────────────────────────────────────────┐
│          Scope Index (Map O(1))         │
│    USER / TEAM / AGENT / GLOBAL        │
└─────────────────────────────────────────┘
```

Full architecture details: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

<!-- zh -->
完整架构详见 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)。
-->

---

## New Bilingual Documentation System / 新的双语文档系统

> ⚠️ **The new docs/ folder is the authoritative source for Hook + MCP integration guides.** The links below supersede older inline documentation.

### English / 英文文档

| Document | Description |
|----------|-------------|
| [docs/en/README.md](./docs/en/README.md) | Overview, quick start, architecture, FAQ |
| [docs/en/HOOK_INTEGRATION.md](./docs/en/HOOK_INTEGRATION.md) | Hook mechanism, before_prompt_build, agent_end, performance |
| [docs/en/MCP_INTEGRATION.md](./docs/en/MCP_INTEGRATION.md) | MCP tools, manual usage, configuration examples |
| [docs/en/INTEGRATION_COMPARISON.md](./docs/en/INTEGRATION_COMPARISON.md) | Hook+MCP vs MCP-only vs Hook-only comparison |

### 中文文档

| 文档 | 说明 |
|------|------|
| [docs/zh/README.md](./docs/zh/README.md) | 概述、快速开始、架构、常见问题 |
| [docs/zh/HOOK_INTEGRATION.md](./docs/zh/HOOK_INTEGRATION.md) | Hook 机制、before_prompt_build、agent_end、性能分析 |
| [docs/zh/MCP_INTEGRATION.md](./docs/zh/MCP_INTEGRATION.md) | MCP 工具、手动调用、配置示例 |
| [docs/zh/INTEGRATION_COMPARISON.md](./docs/zh/INTEGRATION_COMPARISON.md) | Hook+MCP vs 仅MCP vs 仅Hook 对比分析 |

---

## Related Documentation / 相关文档

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | Bilingual overview, features, quick start |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Technical architecture (bilingual) |
| [docs/competitive-analysis.md](./docs/competitive-analysis.md) | Competitive analysis |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | Version history and changelog |
| [SKILL_CN.md](./SKILL_CN.md) | Legacy Chinese SKILL (superseded by this file) |
| [HOOK.md](./HOOK.md) | Hook lifecycle and configuration reference |

---

## License

MIT License. See [README.md](./README.md#license).
