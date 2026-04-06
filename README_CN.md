---
优先级: critical
标题: Unified Memory v4.1.0
---

# 🧠 Unified Memory v4.1.2

> 四层渐进式 AI 记忆系统 (L0→L1→L2→L3)

**作者**: 程序员小刘 ([@mouxangithub](https://github.com/mouxangithub))  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**安装**: `clawhub install unified-memory`  
**版本**: 4.1.2 (2026-04-06)

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
- 🤖 **本地 Embedding** — node-llama-cpp + GGUF 完全离线
- 🧹 **数据清理器** — retentionDays 自动清理旧数据

**零 Python 依赖** — 纯 Node.js ESM 实现

---

## 核心特性

### 🌐 中文分词 (@node-rs/jieba)

内置中文分词引擎，无需配置即可获得更好的中文搜索效果。

### ⚡ 零配置默认值

无需手动配置，开箱即用。

### 🔗 Hook 集成

支持 `before_prompt_build` 和 `agent_end` 自动触发。

### 📦 四层渐进式管线

```
L0 (对话录制) → L1 (记忆提取) → L2 (场景归纳) → L3 (用户画像)
```

---

## 四层管线架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      Unified Memory v4.1                          │
│                   四层渐进式管线 (L0 → L1 → L2 → L3)              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   L0 (对话录制) ──────────────────────────────────────────────  │
│   │  transcript_first.js                                        │
│   │  • 捕获原始对话，完整保留上下文                              │
│   ▼                                                              │
│   L1 (记忆提取) ──────────────────────────────────────────────  │
│   │  extract.js                                                 │
│   │  • 从对话中提取关键信息                                      │
│   │  • 实体、关系、偏好识别                                      │
│   ▼                                                              │
│   L2 (场景归纳) ──────────────────────────────────────────────  │
│   │  scene_block.js 🆕                                           │
│   │  • 按时间窗口聚类记忆                                        │
│   │  • 提取场景主题、关键实体、行动项                             │
│   ▼                                                              │
│   L3 (用户画像) ──────────────────────────────────────────────  │
│   │  profile.js                                                 │
│   │  • 用户偏好、习惯、目标                                      │
│   ▼                                                              │
├──────────────────────────────────────────────────────────────────┤
│                      自动调度管线 (Pipeline Scheduler)            │
│  • L0→L1: 每 N 轮对话后触发                                      │
│  • L1→L2: L1 完成后延迟触发                                      │
│  • L2→L3: 每 M 条新记忆触发                                       │
└──────────────────────────────────────────────────────────────────┘
```

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
# 存储记忆
mcporter call unified-memory memory_store '{
  "text": "用户偏好简洁风格",
  "category": "preference",
  "importance": 0.8
}'

# 搜索记忆
mcporter call unified-memory memory_search '{
  "query": "用户偏好",
  "topK": 5
}'

# 场景归纳 (L2)
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER"
}'

# 查看管线状态
mcporter call unified-memory memory_pipeline_status '{}'
```

---

## 工具列表

### 🆕 v4.1.2 新增工具

#### 本地 Embedding (3个)

| 工具 | 说明 |
|------|------|
| `memory_local_embedding_status` | 获取本地 Embedding 服务状态 |
| `memory_local_embedding_warmup` | 启动模型预热 |
| `memory_local_embedding_embed` | 使用本地模型获取向量 |

#### 数据清理器 (3个)

| 工具 | 说明 |
|------|------|
| `memory_cleaner_status` | 获取数据清理器状态 |
| `memory_cleaner_config` | 更新数据清理器配置 |
| `memory_cleaner_run` | 手动执行数据清理 |

### 🆕 v4.1 新增工具

#### L2 场景归纳 (6个)

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
| `memory_store` | 存储记忆 |
| `memory_get` | 获取记忆 |
| `memory_list` | 列出记忆 |
| `memory_delete` | 删除记忆 |
| `memory_search` | 混合搜索 |

### WAL 协议 (6个)

| 工具 | 说明 |
|------|------|
| `memory_wal_status` | WAL 状态 |
| `memory_wal_write` | 写 WAL |
| `memory_wal_replay` | WAL 恢复 |
| `memory_wal_truncate` | 截断 WAL |
| `memory_wal_export` | 导出 WAL |
| `memory_wal_import` | 导入 WAL |

### 证据链 (15个)

| 工具 | 说明 |
|------|------|
| `memory_evidence_add` | 添加证据 |
| `memory_evidence_get` | 获取证据链 |
| `memory_evidence_find_by_type` | 按类型查找 |
| `memory_evidence_find_by_source` | 按来源查找 |
| `memory_evidence_stats` | 证据统计 |

### 其他工具

- **Transcript-First**: 11个工具
- **自动整理**: 5个工具
- **修订生命周期**: 3个工具
- **泳道记忆**: 8个工具
- **Token 预算**: 8个工具
- **搜索与检索**: 7个工具
- **分析与管理**: 16个工具
- **云与系统**: 12个工具

---

## 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |
| `VECTOR_ENGINE` | `lancedb` | 向量引擎 |
| `LLM_PROVIDER` | `ollama` | LLM 提供者 |

### Scope 隔离级别

| Scope | 写入权限 | 读取权限 |
|-------|---------|---------|
| `AGENT` | 仅当前 Agent | 仅当前 Agent |
| `USER` | 用户代理 | 用户 + TEAM + GLOBAL |
| `TEAM` | 团队成员 | 团队 + GLOBAL |
| `GLOBAL` | 任何 Agent | 所有 Agent |

---

## 与 memory-tencentdb 对比

| 特性 | Unified Memory v4.1.2 | memory-tencentdb |
|------|----------------------|------------------|
| **语言** | Node.js ESM | Node.js |
| **中文分词** | @node-rs/jieba ✅ | 未知 |
| **本地 Embedding** | node-llama-cpp + GGUF ✅ | 未知 |
| **数据清理器** | retentionDays 自动清理 ✅ | 未知 |
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
| **v4 工具** | 160+ 工具 | 未知 |

---

## 常见问题

### Q: 如何启用中文分词？

A: 已在 v4.1 中默认启用，无需配置。

### Q: 如何调整管线调度频率？

```bash
mcporter call unified-memory memory_pipeline_config '{
  "everyNConversations": 3
}'
```

### Q: 如何手动触发场景归纳？

```bash
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER"
}'
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 英文主文档 |
| [SKILL.md](./SKILL.md) | 技术参考 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 架构文档 |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 变更日志 |
| [docs/API.md](./docs/API.md) | API 文档 |

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

*最后更新: 2026-04-06 | v4.1.2 | 四层管线 | 本地 Embedding | 数据清理器 | 中文分词 | 零配置默认值*
