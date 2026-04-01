---
priority: critical
title: Unified Memory v4.0.0 — 中文文档
---

<!-- Language Toggle / 语言切换 -->
**[English](./README.md)** · [中文](./README_CN.md) · [日本語](./README_JA.md)

<!-- Documentation Navigation / 文档导航 -->
📚 **文档导航**: [概述](#概述) · [功能特性](#功能特性) · [架构](#架构) · [安装](#安装) · [API](#152-mcp-工具-按类别分类) · [快速入门](#快速入门) · [索引](#-完整文档索引)

---

> AI Agent 记忆系统 — 多层化、持久化、主动化

**作者**: 程序员小刘 (@mouxangithub)  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**安装**: `clawhub install unified-memory`  
**框架**: OpenClaw Agent | Node.js ESM | 152 MCP Tools | Web Dashboard v3.x  
**版本**: 3.8.4 (2026-03-30)

---

## 目录

- [概述](#概述)
- [功能特性](#功能特性)
- [架构](#架构)
- [安装](#安装)
- [配置](#配置)
- [152 MCP 工具](#152-mcp-工具-按类别分类)
- [快速入门](#快速入门)
- [Scope 隔离](#scope-隔离)
- [开发](#开发)
- [许可证](#许可证)
- [完整文档索引](#完整文档索引)

---

## 概述 (v4.0.0)

Unified Memory 是 OpenClaw Agent 领域功能最丰富的记忆系统 MCP 服务器。它提供持久化上下文、混合搜索（BM25 + 向量 + RRF 融合）、Weibull 衰减、WAL 崩溃恢复、证据链、Transcript-First 架构、泳道记忆、Token 预算强制执行以及深度的 Scope 隔离 —— 全部使用纯 Node.js ESM 实现，零 Python 依赖。

<!-- en -->
Unified Memory is the most feature-rich memory system MCP server for OpenClaw agents. It provides persistent context, hybrid search (BM25 + Vector + RRF), Weibull decay, WAL-based crash recovery, evidence chains, transcript-first architecture, lane memory, token budget enforcement, and deep scope isolation — all in pure Node.js ESM with zero Python dependencies.
-->

---

## 功能特性

### 核心记忆能力

#### 🔄 持久化上下文 | Persistent Context

每次对话都建立在上一次会话的基础上。Unified Memory 通过维护一个持续增长、可搜索的记忆库来消除重复解释上下文的需要，记忆在会话重启和压缩事件中持久保存。

<!-- en -->
Every conversation builds on previous sessions. Unified Memory eliminates the need to re-explain context by maintaining a continuously growing, searchable memory store that survives session restarts and compaction events.
-->

#### 🔍 混合搜索 | Hybrid Search

搜索管道结合三种检索策略以最大化召回率和精度：

1. **BM25** — 传统关键词稀疏检索（纯 Node.js，无外部依赖）
2. **Vector** — 通过 LanceDB 或 Ollama 的密集语义嵌入
3. **RRF (倒数排名融合)** — 以可配置权重融合 BM25 和向量结果

MMR（最大边际相关性）重排用于提升多样性。整个管道是可插拔的 —— 可根据基础设施选择使用 LanceDB、Ollama 或纯 BM25 模式。

<!-- en -->
The search pipeline combines three retrieval strategies for maximum recall and precision: BM25 for keyword search, Vector for dense semantic embeddings via LanceDB or Ollama, and RRF (Reciprocal Rank Fusion) to fuse results. MMR reranking is applied for diversity. The entire pipeline is pluggable.
-->

#### 📈 Weibull 衰减 | Weibull Decay

记忆使用 Weibull 分布（shape=1.5，scale=30天）随时间衰减，模拟人类遗忘曲线。重要性评分和访问频率调节衰减速率 —— 关键记忆持续更久，陈旧记忆逐渐消失。

<!-- en -->
Memories decay over time using a Weibull distribution (shape=1.5, scale=30 days) that models human forgetting curves. Importance scores and access frequency modulate the decay rate.
-->

#### 💾 WAL 协议 | WAL Protocol

预写日志（WAL）确保每个记忆操作在确认前都是持久的。崩溃时，WAL 自动重放以恢复所有已提交的数据，并进行校验和验证。

<!-- en -->
Write-Ahead Log (WAL) ensures every memory operation is durable before acknowledgment. On crash, the WAL is replayed automatically to recover all committed data with checksum validation.
-->

#### 🏷️ Scope 隔离 | Scope Isolation

四层隔离确保记忆访问始终恰当：

| Scope | 访问权限 |
|-------|---------|
| `AGENT` | 单 Agent 私有 |
| `USER` | 单用户，排除 AGENT |
| `TEAM` | 团队共享，排除 USER/AGENT |
| `GLOBAL` | 全局公开 |

<!-- en -->
Four-tier isolation: AGENT (single agent private), USER (per-user), TEAM (team-shared), GLOBAL (public to all).
-->

#### 📊 知识图谱 | Knowledge Graph

从对话中提取实体和关系映射，构建互联的知识网络。通过语义连接查询关系、查找相关实体和导航记忆。

<!-- en -->
Entity extraction and relationship mapping from conversations builds an interconnected knowledge network.
-->

#### 🔗 证据链 | Evidence Chain

每条记忆都携带来源元数据：来源（transcript/message/manual/inference）、置信度评分（0-1）和证据链追踪。召回可以按证据质量过滤，实现更可靠的记忆检索。

<!-- en -->
Every memory carries provenance metadata: source, confidence score (0-1), and evidence chain tracking. Recall can be filtered by evidence quality.
-->

#### 📝 Transcript-First 架构 | Transcript-First Architecture

Transcript 作为唯一的真实来源。记忆从 transcript 重建而非直接存储，确保证据链始终完整，记忆可以从原始对话数据重新生成。

<!-- en -->
Transcripts serve as the single source of truth. Memory is rebuilt from transcripts rather than stored directly.
-->

#### 🏊 泳道记忆 | Lane Memory

并行记忆泳道（primary/task/background/archive）允许不同对话线程的隔离。可以为长期运行的任务或项目特定上下文创建自定义泳道。

<!-- en -->
Parallel memory swim lanes allow isolation of different conversation threads. Custom lanes can be created for long-running tasks.
-->

#### 💰 Token 预算 | Token Budget

细粒度 Token 分配，包含硬限制（95%）、自动压缩（85%）和警告阈值（70%）。基于类型和优先级的分配防止任何单一记忆类别消耗整个预算。

<!-- en -->
Fine-grained token allocation with hard limits (95%), auto-compaction (85%), and warning thresholds (70%).
-->

#### 🔄 自动整理 | Auto Organization

自动层级迁移（HOT/WARM/COLD）、基于年龄和重要性的压缩、以及超过 365 天的记忆归档，保持记忆系统精简高效。

<!-- en -->
Automatic tier migration (HOT/WARM/COLD), compression based on age and importance, and archival of memories older than 365 days.
-->

#### 🔀 修订生命周期 | Revision Lifecycle

记忆经历生命周期阶段（draft → review → approved → archived），具有增强的冲突检测和并发编辑自动合并功能。

<!-- en -->
Memories progress through lifecycle stages (draft → review → approved → archived) with enhanced conflict detection.
-->

#### ⚡ 可插拔架构 | Pluggable Architecture

配置向量引擎和 LLM 提供者以匹配您的基础设施：

| 模式 | 向量引擎 | Embedding | LLM |
|------|---------|-----------|-----|
| 默认（推荐） | LanceDB | Ollama | Ollama |
| 轻量级 | none | none | none |
| 本地向量 | LanceDB | Ollama | none |
| 云托管 | LanceDB Cloud | LanceDB managed | Ollama/OpenAI |

---

## 架构

```
OpenClaw Agent
└── unified-memory (Node.js ESM MCP Server)
    ├── 28 核心工具（统一 action 参数入口）
    ├── 存储层：JSON + WAL（崩溃可恢复）
    ├── 向量层（可插拔）：
    │   ├── LanceDB（默认，零配置）
    │   ├── Ollama Embedding（可选）
    │   └── none（纯 BM25 模式）
    ├── LLM 层（可插拔）：
    │   ├── Ollama（默认，本地）
    │   └── none（基于规则回退）
    ├── 证据层：来源追踪 + 置信度评分
    ├── 层级管理：HOT / WARM / COLD
    ├── 泳道系统：并行泳道
    ├── Token 预算：硬限制 + 自动压缩
    └── Web UI：仪表板 + 健康监控
```

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

详细技术文档请参阅 [SKILL.md](./SKILL.md)。

---

## 安装

### 方式一 — Clawhub（推荐）

```bash
clawhub install unified-memory
openclaw gateway restart
```

### 方式二 — Curl 安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### 方式三 — 手动安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

### 验证安装

```bash
mcporter call unified-memory memory_health '{}'
```

---

## 配置

核心环境变量（详细说明见 [docs/CONFIG.md](docs/CONFIG.md)）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务器地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |
| `LANCEDB_API_KEY` | （无） | LanceDB Cloud API Key |
| `VECTOR_ENGINE` | `lancedb` | 向量引擎：`lancedb` / `ollama` / `none` |
| `LLM_PROVIDER` | `ollama` | LLM 提供者：`ollama` / `openai` / `none` |

---

## 152 MCP 工具（按类别分类）

### 存储核心（5 个工具）

| 工具 | 说明 |
|------|------|
| `memory_store` | 存储记忆，包含分类、重要性、标签、scope |
| `memory_get` | 通过 ID 获取单条记忆 |
| `memory_list` | 分页列出记忆 |
| `memory_delete` | 删除记忆 |
| `memory_search` | 混合搜索：BM25 → Vector → 重排 → MMR |

### WAL 协议（6 个工具）

| 工具 | 说明 |
|------|------|
| `memory_wal_write` | 写入 WAL 日志条目 |
| `memory_wal_replay` | 崩溃恢复重放 |
| `memory_wal_status` | 查询 WAL 状态 |
| `memory_wal_truncate` | 检查点后截断 WAL |
| `memory_wal_export` | 导出 WAL 作为备份 |
| `memory_wal_import` | 从备份导入 WAL |

### 证据链（15 个工具）

| 工具 | 说明 |
|------|------|
| `memory_evidence_add` | 为记忆添加证据 |
| `memory_evidence_get` | 获取记忆的证据链 |
| `memory_evidence_find_by_type` | 按类型查找证据 |
| `memory_evidence_find_by_source` | 按来源查找证据 |
| `memory_evidence_stats` | 证据统计 |
| `memory_evidence_recall` | 证据驱动的召回 |
| `memory_evidence_index` | 索引证据 |
| `memory_evidence_score` | 计算证据评分 |
| `memory_evidence_rank` | 按证据排名结果 |
| `memory_evidence_filter_by_type` | 按证据类型过滤 |
| `memory_evidence_filter_by_source` | 按证据来源过滤 |
| `memory_evidence_high_confidence` | 仅保留高置信度证据 |
| `memory_evidence_transcript_only` | 仅返回 transcript 证据 |
| `memory_evidence_summary` | 获取证据摘要 |
| `memory_evidence_statistics` | 详细证据统计 |

### Transcript-First（11 个工具）

| 工具 | 说明 |
|------|------|
| `memory_transcript_add` | 添加 transcript |
| `memory_transcript_get` | 通过 ID 获取 transcript |
| `memory_transcript_update` | 更新 transcript |
| `memory_transcript_delete` | 删除 transcript |
| `memory_transcript_list` | 列出所有 transcripts |
| `memory_transcript_find_by_source` | 按来源查找 transcripts |
| `memory_transcript_rebuild` | 从 transcripts 重建记忆 |
| `memory_transcript_summary` | 获取 transcript 摘要 |
| `memory_transcript_stats` | Transcript 统计 |
| `memory_transcript_verify` | 验证 transcript 完整性 |
| `memory_transcript_compact` | 压缩 transcript 存储 |

### 自动整理（5 个工具）

| 工具 | 说明 |
|------|------|
| `memory_organize` | 跨层级整理 |
| `memory_compress_tier` | 压缩特定层级 |
| `memory_archive_old` | 归档超过 365 天的记忆 |
| `memory_tier_stats` | 层级统计 |
| `memory_full_organize` | 全系统整理 |

### 修订生命周期（3 个工具）

| 工具 | 说明 |
|------|------|
| `memory_revision_lifecycle_summary` | 生命周期阶段摘要 |
| `memory_revision_by_stage` | 按生命周期阶段获取修订 |
| `memory_revision_update_stage` | 更新修订生命周期阶段 |

### 泳道记忆（8 个工具）

| 工具 | 说明 |
|------|------|
| `memory_lane_create` | 创建自定义泳道 |
| `memory_lane_switch` | 切换当前泳道 |
| `memory_lane_current` | 获取当前泳道 |
| `memory_lane_list` | 列出所有泳道 |
| `memory_lane_move` | 在泳道间移动记忆 |
| `memory_lane_archive` | 归档泳道 |
| `memory_lane_merge` | 合并泳道 |
| `memory_lane_delete` | 删除泳道 |

### Token 预算（8 个工具）

| 工具 | 说明 |
|------|------|
| `memory_token_budget_status` | 获取预算状态 |
| `memory_token_budget_enforce` | 强制执行硬限制 |
| `memory_token_budget_allocate` | 为类别分配 Token |
| `memory_token_budget_record` | 记录 Token 使用 |
| `memory_token_budget_compress` | 压缩记忆以适应预算 |
| `memory_token_budget_history` | 获取使用历史 |
| `memory_token_budget_reset` | 重置使用计数器 |
| `memory_token_budget_config` | 获取/更新预算配置 |

### 统一入口 — Action-Parameter 工具（10 个工具）

这些工具使用 `action` 参数进行多操作访问：

| 工具 | 操作 |
|------|------|
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

### 搜索与检索（7 个工具）

| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | 密集向量相似度搜索 |
| `memory_scope` | 按 scope 过滤的搜索 |
| `memory_concurrent_search` | 并行多 scope 搜索 |
| `memory_dedup` | 搜索结果去重 |
| `memory_noise` | 过滤噪音结果 |
| `memory_mmr` | 最大边际相关性重排 |

### 分析与管理（16 个工具）

| 工具 | 说明 |
|------|------|
| `memory_trace` | 追踪记忆访问模式 |
| `memory_metrics` | 系统指标 |
| `memory_decay` | Weibull 衰减管理 |
| `memory_extract` | 从文本提取实体 |
| `memory_reflection` | 记忆反思分析 |
| `memory_intent` | 意图路由 |
| `memory_wal` | WAL 状态与管理 |
| `memory_adaptive` | 自适应记忆管理 |
| `memory_autostore` | 自动存储配置 |
| `memory_auto_extract` | 自动实体提取 |
| `memory_health` | 系统健康检查 |
| `memory_insights` | 记忆洞察报告 |
| `memory_predict` | 预测记忆需求 |
| `memory_feedback` | 记忆质量反馈 |
| `memory_stats` | 总体统计 |
| `memory_lesson` | 经验教训管理 |

### 云与系统（12 个工具）

| 工具 | 说明 |
|------|------|
| `memory_cloud_backup` | 备份到云存储 |
| `memory_cloud_restore` | 从云备份恢复 |
| `memory_export` | 导出记忆为 JSON |
| `memory_import` | 从 JSON 导入记忆 |
| `memory_clone` | 克隆记忆数据库 |
| `memory_share` | 跨 Agent 共享记忆 |
| `memory_intent` | 意图检测 |
| `memory_insights` | 洞察生成 |
| `memory_predict` | 预测性记忆 |
| `memory_feedback` | 反馈处理 |
| `memory_health` | 健康监控 |
| `memory_stats` | 统计仪表板 |

> **注意**：确切工具数量可能因安装而异。运行 `mcporter list unified-memory` 查看您安装中可用的工具。

---

## 快速入门

```bash
# 1. 验证安装
mcporter call unified-memory memory_health '{}'

# 2. 存储一条记忆
mcporter call unified-memory memory_store '{
  "text": "Liu prefers concise communication",
  "category": "preference",
  "scope": "USER"
}'

# 3. 搜索记忆（混合 BM25 + Vector + RRF）
mcporter call unified-memory memory_search '{
  "query": "Liu communication style",
  "scope": "USER"
}'

# 4. 检查系统统计
mcporter call unified-memory memory_stats '{}'

# 5. 添加提醒
mcporter call unified-memory memory_reminder '{
  "action": "add",
  "content": "team meeting",
  "minutes": 30
}'

# 6. 查看知识图谱
mcporter call unified-memory memory_graph '{"action": "stats"}'

# 7. 检查 WAL 状态
mcporter call unified-memory memory_wal_status '{}'

# 8. 查看层级状态
mcporter call unified-memory memory_tier '{"action": "status"}'

# 9. 检查 Token 预算
mcporter call unified-memory memory_token_budget_status '{}'

# 10. 启动 Web 仪表板
node start-dashboard.js
```

---

## Scope 隔离

Scope 隔离确保记忆访问始终符合上下文：

| Scope | 谁可以写入 | 谁可以读取 |
|-------|-----------|-----------|
| `AGENT` | 仅所属 Agent | 仅所属 Agent |
| `USER` | 代表用户的任何 Agent | 用户 + TEAM + GLOBAL |
| `TEAM` | 团队中的任何 Agent | 团队 + GLOBAL |
| `GLOBAL` | 任何 Agent | 所有 Agent |

---

## 开发

```bash
# 安装依赖
npm install --ignore-scripts

# 启动 MCP 服务器（stdio 模式）
node src/index.js

# CLI 帮助
node src/cli/index.js --help

# 运行测试
node run-tests.cjs

# 启动 Web 仪表板
node start-dashboard.js

# 运行集成测试
node test-all.cjs

# 检查层级迁移
node src/test_tier.js
```

### 文件结构

```
unified-memory/
├── src/                            # 源代码
│   ├── index.js                    # MCP 服务器（28 个统一工具）
│   ├── storage.js                  # JSON + WAL 持久化
│   ├── wal.js                     # 预写日志
│   ├── evidence.js                # 证据链
│   ├── evidence_recall.js         # 证据驱动的召回
│   ├── organize.js                 # 自动整理
│   ├── transcript_first.js         # Transcript-First 架构
│   ├── revision_manager_enhanced.js # 修订生命周期
│   ├── lane_manager_enhanced.js   # 泳道记忆
│   ├── token_budget_enhanced.js    # Token 预算
│   ├── bm25.js                    # BM25 引擎
│   ├── vector_lancedb.js          # LanceDB 后端
│   ├── cognitive_scheduler.js     # 主动调度器
│   ├── session_state.js           # 热上下文
│   ├── decay.js                   # Weibull 衰减
│   ├── graph/                     # 知识图谱
│   ├── cli/                       # CLI 工具
│   └── webui/dashboard.html        # 仪表板 UI
├── docs/                          # 文档
│   ├── CONFIG.md                  # 配置指南
│   └── competitive-analysis.md    # 竞品分析
├── SKILL.md                       # 技术深度文档（英文）
├── README.md                      # 英文主文档
├── README_CN.md                   # 中文主文档
├── README.zh-CN.md                # 旧版中文自述
└── package.json                   # 包配置
```

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

## 📚 完整文档索引

> 🌍 **语言**: [English](./README.md) · **[中文](./README_CN.md)** · [日本語](./README_JA.md)

### 📖 主文档

| 文件 | 说明 |
|------|------|
| [README.md](./README.md) | 英汉双语主文档 — Bilingual main documentation |
| [README_CN.md](./README_CN.md) | **本文档** — 中文主文档 |
| [README.zh-CN.md](./README.zh-CN.md) | 旧版中文自述 |
| [SKILL.md](./SKILL.md) | 技术深度文档（英文） |

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

### 📋 docs/ — 通用文档

| 文件 | 说明 |
|------|------|
| [docs/index.md](./docs/index.md) | **文档中心** — 总索引页 |
| [docs/CONFIG.md](./docs/CONFIG.md) | 详细配置指南 |
| [docs/competitive-analysis.md](./docs/competitive-analysis.md) | 竞品分析 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 架构详解 |
| [docs/v4.0-ARCHITECTURE.md](./docs/v4.0-ARCHITECTURE.md) | v4.0 架构 |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 完整更新日志 |
| [docs/v3.8.0-release-notes.md](./docs/v3.8.0-release-notes.md) | v3.8.0 更新日志 |
| [docs/v3.8.1-release-notes.md](./docs/v3.8.1-release-notes.md) | v3.8.1 更新日志 |
| [docs/v3.8.2-release-notes.md](./docs/v3.8.2-release-notes.md) | v3.8.2 更新日志 |
| [docs/v3.8.3-release-notes.md](./docs/v3.8.3-release-notes.md) | v3.8.3 更新日志 |
| [docs/v3.8.4-release-notes.md](./docs/v3.8.4-release-notes.md) | v3.8.4 更新日志 |

### 🚀 快速访问

- [README_QUICK_START.md](./README_QUICK_START.md) — 快速入门指南
- [docs/index.md](./docs/index.md) — 📚 **全部文档索引** (总索引页)

---

*最后更新：2026-04-01 | v3.8.4 | 152 MCP Tools | Pure Node.js ESM*
