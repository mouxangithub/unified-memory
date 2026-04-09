# Unified Memory v5.0.1

> 🧠 **Unified Memory** — 四层渐进式 AI 记忆系统 (L0→L1→L2→L3) · Pure Node.js ESM

[![Version](https://img.shields.io/badge/version-5.0.1-blue.svg)](https://github.com/mouxangithub/unified-memory)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[English](./README.md) · [中文](./README_CN.md) · [Changelog](./CHANGELOG.md)**

---

## 项目简介

Unified Memory 是专为 OpenClaw Agent 设计的功能最丰富的记忆系统 MCP 服务器。基于 Supermemory.ai 架构分析，v5.0.1 集成了 OpenViking 风格的完整知识管理能力。

**核心能力**:
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
- 📊 **Benchmark** — recall@K / precision@K / MRR 召回率验证
- 🔌 **插件系统** — 5 种 Hook 可扩展架构
- 🏅 **OpenViking 集成** — Viking URI、意图分析、分层检索、会话管理

**零 Python 依赖** — 纯 Node.js ESM 实现

---

## 核心架构

### 四层渐进式管线 (L0→L1→L2→L3)

```
┌──────────────────────────────────────────────────────────────────┐
│                      Unified Memory v5.0.1                         │
│                   四层渐进式管线 (L0 → L1 → L2 → L3)              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   L0 (对话录制) ──────────────────────────────────────────────   │
│   │  transcript_first.js                                         │
│   │  • 捕获原始对话，完整保留上下文                               │
│   ▼                                                              │
│   L1 (记忆提取) ──────────────────────────────────────────────   │
│   │  extract.js                                                  │
│   │  • 从对话中提取关键信息、实体、关系、偏好                     │
│   ▼                                                              │
│   L2 (场景归纳) ──────────────────────────────────────────────   │
│   │  scene_block.js                                              │
│   │  • 按时间窗口聚类记忆，生成场景块                             │
│   │  • 提取场景主题、关键实体、行动项                             │
│   ▼                                                              │
│   L3 (用户画像) ──────────────────────────────────────────────   │
│   │  profile.js / persona_generator.js                            │
│   │  • 用户偏好、习惯、目标、动态画像                             │
│   ▼                                                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                      OpenViking 集成                              │
│  • Viking URI 命名空间                                           │
│  • 意图分析与类型化查询                                          │
│  • 分层压缩 (L0/L1/L2)                                          │
│  • 智能去重与生命周期管理                                         │
└──────────────────────────────────────────────────────────────────┘
```

### 系统分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    index.js (MCP Server)                    │
│              100+ registered tools / 注册工具                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Storage   │  │   Search    │  │    Intelligence     │ │
│  │    Layer    │  │    Layer    │  │      Layer          │ │
│  │             │  │             │  │                     │ │
│  │ · Memory    │  │ · BM25      │  │ · Cognitive Sched. │ │
│  │   Files     │  │ · Vector    │  │ · Memory Lanes     │ │
│  │ · LanceDB  │  │ · RRF       │  │ · Evidence Chain   │ │
│  │ · WAL       │  │ · Scope     │  │ · Auto Organize    │ │
│  │ · Tier      │  │   Filter    │  │ · Weibull Decay    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Plugin System (Pluggable Architecture)      │    │
│  │  beforeSearch / afterSearch / beforeWrite / afterWrite│    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 全部功能列表

### 存储与持久化

| 功能 | 说明 |
|------|------|
| WAL 协议 | 预写日志，崩溃恢复，checksum 校验 |
| Tier 分层 | HOT (7d) / WARM (30d) / COLD (365d) 自动迁移 |
| 证据链 | 来源追踪，confidence 评分，多类型来源 |
| 版本历史 | 每条记忆最多 50 个修订版本 |
| 云备份 | 云端同步与恢复 |

### 搜索与检索

| 功能 | 说明 |
|------|------|
| BM25 | 关键词全文搜索，重要性加权 |
| 向量搜索 | Ollama / OpenAI / Jina / SiliconFlow 多后端 |
| RRF 融合 | Reciprocal Rank Fusion, k=60 |
| 混合搜索 | BM25 + Vector 归一化分数融合 |
| MMR 重排 | Maximal Marginal Relevance 多样性优化 |
| QMD 搜索 | Query Memory Document 结构化查询 |
| 并发搜索 | 多查询并行执行 |
| 范围过滤 | AGENT / USER / TEAM / GLOBAL 隔离 |
| 中文分词 | @node-rs/jieba 原生集成 |

### 智能处理

| 功能 | 说明 |
|------|------|
| L0 对话录制 | JSONL 格式，增量捕获 |
| L1 记忆提取 | LLM 实体/关系/偏好提取，8种记忆类型 |
| L2 场景归纳 | 时间窗口聚类，生成场景块 |
| L3 用户画像 | 静态 + 动态双画像 |
| 矛盾检测 | 规则 + LLM 深度判断 |
| 临时过期 | 自动清理有过期时间的记忆 |
| 遗忘曲线 | Weibull 衰减 (shape=1.5, scale=30d) |
| 意图路由 | 智能路由到合适的处理器 |
| 噪声过滤 | 过滤无意义查询 |

### OpenViking 特性 (v5.0.1 新增)

| 功能 | 说明 |
|------|------|
| Viking URI | 统一资源定位命名空间 |
| 意图分析 | 多类型化查询生成 |
| 分层压缩 | L0抽象/L1概览/L2详情三层模型 |
| 智能去重 | 语义相似度检测与合并 |
| 生命周期管理 | 自动归档与清理 |
| 异步队列 | 批量任务后台处理 |

### 可观测性

| 功能 | 说明 |
|------|------|
| Web UI | 仪表板，统计图表，健康检查 |
| REST API | stats / memories / categories / search 接口 |
| Metrics | 详细使用指标和性能数据 |
| Token 预算 | 自动压缩与限制 |
| 追踪器 | 访问历史，修改追踪 |

---

## MCP 工具列表 (100+)

### 存储核心 (5个)

| 工具 | 说明 |
|------|------|
| `memory_store` | 存储记忆 |
| `memory_get` | 获取单条记忆 |
| `memory_list` | 分页列表 |
| `memory_delete` | 删除记忆 |
| `memory_search` | 混合搜索 |

### 搜索与检索 (7个)

| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 搜索 |
| `memory_vector` | 向量搜索 |
| `memory_scope` | 范围过滤 |
| `memory_concurrent_search` | 并发多范围 |
| `memory_dedup` | 结果去重 |
| `memory_noise` | 噪声过滤 |
| `memory_mmr` | MMR 重排 |

### L2 场景归纳 (6个)

| 工具 | 说明 |
|------|------|
| `memory_scene_induct` | 从记忆归纳场景块 |
| `memory_scene_list` | 列出场景块 |
| `memory_scene_get` | 获取场景块详情 |
| `memory_scene_delete` | 删除场景块 |
| `memory_scene_search` | 搜索场景块 |
| `memory_scene_stats` | 场景统计 |

### 管线调度 (3个)

| 工具 | 说明 |
|------|------|
| `memory_pipeline_status` | 管线状态 |
| `memory_pipeline_trigger` | 手动触发管线 |
| `memory_pipeline_config` | 管线配置 |

### 知识图谱 (6个)

| 工具 | 说明 |
|------|------|
| `memory_graph` | 知识图谱操作 |
| `memory_entity_types_list` | 列出实体类型 |
| `memory_entity_type_add` | 添加实体类型 |
| `memory_entity_get` | 获取实体 |
| `memory_entity_search` | 搜索实体 |
| `memory_relation_add` | 添加关系 |

### 插件系统 (4个)

| 工具 | 说明 |
|------|------|
| `memory_plugins_list` | 列出插件 |
| `memory_plugin_enable` | 启用插件 |
| `memory_plugin_disable` | 禁用插件 |
| `memory_plugin_register` | 注册插件 |

### Benchmark (1个)

| 工具 | 说明 |
|------|------|
| `memory_benchmark_recall` | 召回率基准测试 |

### 分析与管理 (30+个)

| 工具 | 说明 |
|------|------|
| `memory_stats` | 整体统计 |
| `memory_health` | 健康检查 |
| `memory_metrics` | 详细指标 |
| `memory_budget` | Token 预算 |
| `memory_tier` | 层级管理 |
| `memory_tier_stats` | 层级统计 |
| `memory_decay` | 衰减分数 |
| `memory_organize` | 自动整理 |
| `memory_full_organize` | 全量整理 |
| `memory_cache` | 缓存管理 |
| `memory_cognitive` | 认知分析 |
| `memory_scope` | 范围管理 |
| `memory_archive_old` | 归档旧记忆 |
| `memory_lanes` | 泳道管理 |
| `memory_dashboard` | Web 仪表盘 |
| `memory_wal` | WAL 操作 |
| `memory_extract` | 实体提取 |
| `memory_reflection` | 反思分析 |
| `memory_lessons` | 经验教训 |
| `memory_preference` | 偏好学习 |
| `memory_inference` | 逻辑推理 |
| `memory_adaptive` | 自适应 |
| `memory_compress_tier` | 压缩 |
| `memory_identity_*` | 身份档案 |

### 证据链 (6个)

| 工具 | 说明 |
|------|------|
| `memory_evidence_add` | 添加证据 |
| `memory_evidence_get` | 获取证据链 |
| `memory_evidence_find_by_type` | 按类型查找 |
| `memory_evidence_find_by_source` | 按来源查找 |
| `memory_evidence_stats` | 证据统计 |
| `memory_evidence_recall` | 证据召回 |

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

### 验证

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

# 混合搜索
mcporter call unified-memory memory_search '{
  "query": "用户偏好",
  "topK": 5
}'

# 统计
mcporter call unified-memory memory_stats '{}'

# 场景归纳
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER"
}'

# 管线状态
mcporter call unified-memory memory_pipeline_status '{}'

# 召回率 Benchmark
mcporter call unified-memory memory_benchmark_recall '{}'
```

---

## 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `LLM_MODEL` | `qwen2.5:7b` | LLM 模型 |
| `VECTOR_ENGINE` | `lancedb` | 向量引擎 |
| `STORAGE_MODE` | `json` | 存储模式 |
| `VECTOR_STORE_TYPE` | `lancedb` | 向量后端 (lancedb/sqlite) |

### 插件 Hook

| Hook | 触发时机 | 功能 |
|------|---------|------|
| `before_prompt_build` | 构建提示词前 | 自动召回相关记忆 |
| `agent_end` | Agent 结束 | 自动捕获对话到 L0 |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 本文档 |
| [README_CN.md](./README_CN.md) | 中文版 |
| [SKILL.md](./SKILL.md) | 技术参考 |
| [CHANGELOG.md](./CHANGELOG.md) | 版本历史 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 架构文档 |
| [docs/API.md](./docs/API.md) | API 参考 |
| [docs/competitive-analysis.md](./docs/competitive-analysis.md) | 竞品分析 |

---

## 许可证

MIT License

---

*最后更新: 2026-04-09 | v5.0.1 | OpenViking Integration | Viking URI | Layered Compression*
