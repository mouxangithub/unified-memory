---
priority: critical
title: Unified Memory v4.1.0
---

<!-- Language Toggle / 语言切换 -->
[English](./README.md) · **[中文](./README_CN.md)**

<!-- Badge -->
[![Version](https://img.shields.io/badge/version-4.1.0-blue.svg)](https://github.com/mouxangithub/unified-memory)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

> 🧠 **Unified Memory** — 四层渐进式 AI 记忆系统 (L0→L1→L2→L3)

**作者**: 程序员小刘 ([@mouxangithub](https://github.com/mouxangithub))  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**安装**: `clawhub install unified-memory`  
**框架**: OpenClaw Agent | Node.js ESM | MCP stdio | 中文分词  
**版本**: 4.1.0 (2026-04-06)

---

## 目录

- [概述](#概述)
- [核心特性](#核心特性)
- [四层管线架构](#四层管线架构)
- [快速开始](#快速开始)
- [工具列表](#工具列表)
- [配置选项](#配置选项)
- [与 memory-tencentdb 对比](#与-memory-tencentdb-对比)
- [常见问题](#常见问题)

---

## 概述

Unified Memory 是专为 OpenClaw Agent 设计的功能最丰富的记忆系统 MCP 服务器。它提供：

- 🔄 **持久化上下文** — 每次对话建立在上一次会话基础上
- 🔍 **混合搜索** — BM25 + 向量 + RRF 融合
- 📈 **Weibull 衰减** — 模拟人类遗忘曲线
- 💾 **WAL 协议** — 崩溃恢复保障
- 🏷️ **四层 Scope 隔离** — AGENT / USER / TEAM / GLOBAL
- 📊 **知识图谱** — 实体关系提取与查询
- 🔗 **证据链** — 来源追踪与置信度评分
- 🏊 **泳道记忆** — 多Agent并行隔离
- 💰 **Token 预算** — 自动压缩与限制
- 🌐 **中文分词** — @node-rs/jieba 原生集成
- ⚡ **零配置默认值** — 开箱即用

**零 Python 依赖** — 纯 Node.js ESM 实现

---

## 核心特性

### 🌐 中文分词 (@node-rs/jieba)

内置中文分词引擎，无需配置即可获得更好的中文搜索效果：

```javascript
// 分词示例
"程序员小刘喜欢写代码" → ["程序员", "小刘", "喜欢", "写", "代码"]
```

### ⚡ 零配置默认值

无需手动配置，开箱即用：

```bash
# 安装后直接使用，无需任何配置
mcporter call unified-memory memory_health '{}'
```

### 🔗 Hook 集成

支持 `before_prompt_build` 和 `agent_end` 自动触发：

```javascript
// agent_end: 自动捕获对话
// before_prompt_build: 自动召回相关记忆
```

---

## 四层管线架构

Unified Memory v4.1 采用四层渐进式管线设计，灵感来自 memory-tencentdb：

```
┌──────────────────────────────────────────────────────────────────┐
│                      Unified Memory v4.1                         │
│                   四层渐进式管线 (L0 → L1 → L2 → L3)              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   L0 (对话录制) ──────────────────────────────────────────────   │
│   │                                                              │
│   │  transcript_first.js                                        │
│   │  • 捕获原始对话                                              │
│   │  • 完整保留上下文                                            │
│   ▼                                                              │
│   L1 (记忆提取) ──────────────────────────────────────────────   │
│   │                                                              │
│   │  extract.js                                                 │
│   │  • 从对话中提取关键信息                                      │
│   │  • 实体、关系、偏好识别                                       │
│   ▼                                                              │
│   L2 (场景归纳) ──────────────────────────────────────────────   │
│   │                                                              │
│   │  scene_block.js  🆕                                          │
│   │  • 按时间窗口聚类记忆                                        │
│   │  • 提取场景主题、关键实体、行动项                             │
│   │  • 生成 Markdown 格式场景块                                   │
│   ▼                                                              │
│   L3 (用户画像) ──────────────────────────────────────────────   │
│   │                                                              │
│   │  profile.js                                                 │
│   │  • 用户偏好、习惯、目标                                       │
│   │  • 个性化记忆组织                                             │
│   ▼                                                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                      自动调度管线 (Pipeline Scheduler)            │
│  • L0→L1: 每 N 轮对话后触发                                      │
│  • L1→L2: L1 完成后延迟触发                                      │
│  • L2→L3: 每 M 条新记忆触发                                       │
│  • Warm-up 模式: 1→2→4→8→...→N                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 管线文件说明

| 管线阶段 | 文件 | 功能 |
|---------|------|------|
| L0 | `transcript_first.js` | 对话录制，完整保留上下文 |
| L1 | `extract.js` | 从对话中提取关键信息 |
| L2 | `scene_block.js` 🆕 | 场景归纳，生成场景块 |
| L3 | `profile.js` | 用户画像构建 |
| 调度器 | `pipeline_scheduler.js` 🆕 | 自动调度管线执行 |

---

## 快速开始

### 安装

```bash
# 方式一：ClawHub (推荐)
clawhub install unified-memory
openclaw gateway restart

# 方式二：手动安装
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install
```

### 验证安装

```bash
mcporter call unified-memory memory_health '{}'
```

### 基本使用

```bash
# 1. 存储记忆
mcporter call unified-memory memory_store '{
  "text": "用户偏好简洁风格",
  "category": "preference",
  "importance": 0.8
}'

# 2. 搜索记忆（混合搜索）
mcporter call unified-memory memory_search '{
  "query": "用户偏好",
  "topK": 5
}'

# 3. 查看统计
mcporter call unified-memory memory_stats '{}'

# 4. 场景归纳 (L2)
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER"
}'

# 5. 查看场景块
mcporter call unified-memory memory_scene_list '{
  "scope": "USER",
  "limit": 10
}'

# 6. 查看管线状态
mcporter call unified-memory memory_pipeline_status '{}'

# 7. 手动触发管线
mcporter call unified-memory memory_pipeline_trigger '{
  "scope": "USER"
}'
```

---

## 工具列表

### 🆕 v4.1 新增工具

#### L2 场景归纳 (8个)

| 工具 | 说明 |
|------|------|
| `memory_scene_induct` | 从记忆中归纳场景块 |
| `memory_scene_list` | 列出所有场景块 |
| `memory_scene_get` | 获取场景块详情 |
| `memory_scene_delete` | 删除场景块 |
| `memory_scene_search` | 搜索场景块 |
| `memory_scene_stats` | 获取场景统计 |

#### 管线调度 (3个)

| 工具 | 说明 |
|------|------|
| `memory_pipeline_status` | 获取四层管线状态 |
| `memory_pipeline_trigger` | 手动触发管线阶段 |
| `memory_pipeline_config` | 更新管线配置 |

### 存储核心 (5个)

| 工具 | 说明 |
|------|------|
| `memory_store` | 存储记忆（category, importance, tags, scope） |
| `memory_get` | 按 ID 获取单条记忆 |
| `memory_list` | 分页列出记忆 |
| `memory_delete` | 删除记忆 |
| `memory_search` | 混合搜索：BM25 → Vector → RRF |

### WAL 协议 (6个)

| 工具 | 说明 |
|------|------|
| `memory_wal_write` | 写入 WAL 日志 |
| `memory_wal_replay` | 崩溃恢复重放 |
| `memory_wal_status` | 查询 WAL 状态 |
| `memory_wal_truncate` | 截断 WAL |
| `memory_wal_export` | 导出 WAL 备份 |
| `memory_wal_import` | 导入 WAL 备份 |

### 证据链 (15个)

| 工具 | 说明 |
|------|------|
| `memory_evidence_add` | 添加证据 |
| `memory_evidence_get` | 获取证据链 |
| `memory_evidence_find_by_type` | 按类型查找 |
| `memory_evidence_find_by_source` | 按来源查找 |
| `memory_evidence_stats` | 证据统计 |
| `memory_evidence_recall` | 证据驱动召回 |
| `memory_evidence_*` | 其他证据操作 |

### Transcript-First (11个)

| 工具 | 说明 |
|------|------|
| `memory_transcript_add` | 添加 transcript |
| `memory_transcript_get` | 获取 transcript |
| `memory_transcript_update` | 更新 transcript |
| `memory_transcript_delete` | 删除 transcript |
| `memory_transcript_list` | 列出 transcript |
| `memory_transcript_rebuild` | 从 transcript 重建记忆 |
| `memory_transcript_*` | 其他 transcript 操作 |

### 自动整理 (5个)

| 工具 | 说明 |
|------|------|
| `memory_organize` | 跨层级整理 |
| `memory_compress_tier` | 压缩指定层级 |
| `memory_archive_old` | 归档超过365天的记忆 |
| `memory_tier_stats` | 层级统计 |
| `memory_full_organize` | 全量整理 |

### 修订生命周期 (3个)

| 工具 | 说明 |
|------|------|
| `memory_revision_lifecycle_summary` | 生命周期阶段摘要 |
| `memory_revision_by_stage` | 按阶段获取修订 |
| `memory_revision_update_stage` | 更新修订阶段 |

### 泳道记忆 (8个)

| 工具 | 说明 |
|------|------|
| `memory_lane_create` | 创建泳道 |
| `memory_lane_switch` | 切换泳道 |
| `memory_lane_current` | 获取当前泳道 |
| `memory_lane_list` | 列出泳道 |
| `memory_lane_move` | 移动记忆到泳道 |
| `memory_lane_archive` | 归档泳道 |
| `memory_lane_merge` | 合并泳道 |
| `memory_lane_delete` | 删除泳道 |

### Token 预算 (8个)

| 工具 | 说明 |
|------|------|
| `memory_token_budget_status` | 获取预算状态 |
| `memory_token_budget_enforce` | 强制硬限制 |
| `memory_token_budget_allocate` | 分配 token |
| `memory_token_budget_record` | 记录使用量 |
| `memory_token_budget_compress` | 压缩记忆 |
| `memory_token_budget_history` | 获取使用历史 |
| `memory_token_budget_reset` | 重置计数器 |
| `memory_token_budget_config` | 配置预算 |

### 搜索与检索 (7个)

| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 搜索 |
| `memory_vector` | 向量相似度搜索 |
| `memory_scope` | Scope 过滤搜索 |
| `memory_concurrent_search` | 并发多范围搜索 |
| `memory_dedup` | 结果去重 |
| `memory_noise` | 过滤噪声 |
| `memory_mmr` | MMR 重排 |

### 分析与管理 (16个)

| 工具 | 说明 |
|------|------|
| `memory_trace` | 追踪访问模式 |
| `memory_metrics` | 系统指标 |
| `memory_decay` | Weibull 衰减管理 |
| `memory_extract` | 实体提取 |
| `memory_reflection` | 反思分析 |
| `memory_intent` | 意图路由 |
| `memory_wal` | WAL 状态 |
| `memory_adaptive` | 自适应管理 |
| `memory_autostore` | 自动存储配置 |
| `memory_auto_extract` | 自动实体提取 |
| `memory_health` | 健康检查 |
| `memory_insights` | 洞察报告 |
| `memory_predict` | 预测需求 |
| `memory_feedback` | 质量反馈 |
| `memory_stats` | 整体统计 |
| `memory_lesson` | 经验教训 |

### 云与系统 (12个)

| 工具 | 说明 |
|------|------|
| `memory_cloud_backup` | 云备份 |
| `memory_cloud_restore` | 云恢复 |
| `memory_export` | 导出 JSON |
| `memory_import` | 导入 JSON |
| `memory_clone` | 克隆数据库 |
| `memory_share` | 跨 Agent 共享 |
| `memory_intent` | 意图检测 |
| `memory_insights` | 洞察生成 |
| `memory_predict` | 预测记忆 |
| `memory_feedback` | 反馈处理 |
| `memory_health` | 健康监控 |
| `memory_stats` | 统计面板 |

---

## 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `LLM_MODEL` | `qwen2.5:7b` | LLM 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |
| `VECTOR_ENGINE` | `lancedb` | 向量引擎：`lancedb` / `ollama` / `none` |
| `LLM_PROVIDER` | `ollama` | LLM 提供者：`ollama` / `openai` / `none` |
| `STORAGE_MODE` | `json` | 存储模式：`json` / `sqlite` |
| `LANCEDB_API_KEY` | (无) | LanceDB Cloud API Key |

### 管线调度配置

```javascript
{
  enabled: true,
  everyNConversations: 5,        // 每 N 轮对话触发 L1
  enableWarmup: true,            // Warm-up 模式
  l1IdleTimeoutSeconds: 60,     // 用户停止对话后多久触发 L1
  l2DelayAfterL1Seconds: 90,    // L1 完成后延迟多久触发 L2
  l2MinIntervalSeconds: 300,    // 两次 L2 的最小间隔
  l2MaxIntervalSeconds: 1800,   // L2 最大轮询间隔
  sessionActiveWindowHours: 24,  // session 不活跃超时
  l3TriggerEveryN: 50,           // 每 N 条新记忆触发 L3
}
```

### Scope 隔离级别

| Scope | 写入权限 | 读取权限 |
|-------|---------|---------|
| `AGENT` | 仅当前 Agent | 仅当前 Agent |
| `USER` | 用户代理 | 用户 + TEAM + GLOBAL |
| `TEAM` | 团队成员 | 团队 + GLOBAL |
| `GLOBAL` | 任何 Agent | 所有 Agent |

---

## 与 memory-tencentdb 对比

| 特性 | Unified Memory v4.1 | memory-tencentdb |
|------|---------------------|------------------|
| **语言** | Node.js ESM | Node.js |
| **中文分词** | @node-rs/jieba ✅ | 未知 |
| **四层管线** | L0→L1→L2→L3 ✅ | ✅ |
| **自动调度** | Pipeline Scheduler ✅ | ✅ |
| **Hook 集成** | before_prompt_build, agent_end ✅ | 未知 |
| **零配置** | 默认值开箱即用 ✅ | 未知 |
| **Scope 隔离** | AGENT/USER/TEAM/GLOBAL ✅ | 未知 |
| **混合搜索** | BM25 + Vector + RRF ✅ | ✅ |
| **WAL 协议** | ✅ | ✅ |
| **Weibull 衰减** | ✅ | 未知 |
| **证据链** | ✅ | 未知 |
| **泳道记忆** | ✅ | 未知 |
| **Token 预算** | ✅ | 未知 |
| **知识图谱** | ✅ | 未知 |
| **v4 工具** | 152+ 工具 | 未知 |

**Unified Memory v4.1 优势**:
- 纯 Node.js，无 Python 依赖
- 原生中文分词支持
- 更丰富的工具生态 (152+ 工具)
- 完整的 Scope 隔离
- 零配置默认值

---

## 常见问题

### Q: 如何启用中文分词？

A: 已在 v4.1 中默认启用，无需配置。分词器会在搜索时自动处理中文文本。

### Q: 如何调整管线调度频率？

```bash
mcporter call unified-memory memory_pipeline_config '{
  "everyNConversations": 3,
  "enableWarmup": true
}'
```

### Q: 如何手动触发场景归纳？

```bash
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER",
  "minMemories": 3
}'
```

### Q: 如何查看管线状态？

```bash
mcporter call unified-memory memory_pipeline_status '{}'
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 本文档 |
| [SKILL.md](./SKILL.md) | 技术参考 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 架构文档 |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 变更日志 |
| [docs/competitive-analysis.md](./docs/competitive-analysis.md) | 竞品分析 |

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

*最后更新: 2026-04-06 | v4.1.0 | 四层管线 | 中文分词 | 零配置默认值*
