# 🧠 Unified Memory v2.1 (unified-memory)

> **完全使用 Node.js ESM 重构** | 33 个 MCP 工具 | 147 个 JS 模块 | 零外部依赖

**项目路径**: `/root/.openclaw/workspace/skills/unified-memory/`

---

## 概述

Unified Memory 是一个为 AI Agent 设计的记忆系统，具备持久化、混合检索、智能遗忘和主动注入能力。通过 MCP 协议提供 33 个工具，支持 BM25 + 向量 + RRF 融合搜索、LLM 增强提取、Weibull 时间衰减、多级Scope隔离等特性。

**存储后端**: JSON 文件（`~/.openclaw/workspace/memory/memories.json`）+ Ollama 向量引擎（完全本地）

**无外部存储依赖**: 不依赖 memory-lancedb-pro 或任何外部服务

---

## 33 个 MCP 工具完整清单

### 核心工具（6个）
| 工具 | 说明 |
|------|------|
| `memory_search` | 混合搜索：BM25 → Vector → Rerank → MMR → Decay → Scope → RRF 融合 |
| `memory_store` | 存储新记忆，支持 category/importance/tags/scope |
| `memory_list` | 列出记忆，支持分页和过滤器 |
| `memory_delete` | 删除记忆 |
| `memory_stats` | 统计：记忆总数、分类分布、重要性分布 |
| `memory_health` | 健康检查：存储、向量引擎、缓存状态 |

### 检索增强（8个）
| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | Ollama 向量语义搜索 |
| `memory_mmr` | MMR（最大边际相关性）多样性选择 |
| `memory_rerank_llm` | LLM Cross-Encoder 重排序 |
| `memory_adaptive` | 自适应跳过非检索类查询（闲聊等） |
| `memory_noise` | 噪音过滤：shouldStore/qualityScore/learnNoisePattern |
| `memory_intent` | 查询意图分类（FACT/PREFERENCE/RECENT/PROJECT 等） |
| `memory_dedup` | Jaccard 相似度批量去重 |

### 写入链路（3个）
| 工具 | 说明 |
|------|------|
| `memory_extract` | LLM 8秒超时从文本提取记忆，Jaccard 去重 |
| `memory_wal` | Write-Ahead Log：故障恢复、批量写入 |
| `memory_tier` | 三层分级：HOT（7天）→ WARM（30天）→ COLD（90天）自动迁移 |

### 智能处理（5个）
| 工具 | 说明 |
|------|------|
| `memory_decay` | Weibull 时间衰减（7天保留89%，30天37%） |
| `memory_reflection` | 自我改进：extractLesson / recallLessons / lessonStats |
| `memory_scope` | 作用域隔离：AGENT / USER / TEAM / GLOBAL 四级 |
| `memory_insights` | 用户洞察：类别分布、工具使用分析、存储建议 |
| `memory_templates` | 记忆模板管理 |

### RAG 与问答（2个）
| 工具 | 说明 |
|------|------|
| `memory_qa` | RAG 智能问答，检索+生成 |
| `memory_qmd_search` | QMD 风格搜索（语境感知） |

### 主动与预测（4个）
| 工具 | 说明 |
|------|------|
| `memory_autostore` | 自动存储：注册 Hook，文本变化时自动写入 |
| `memory_concurrent_search` | 并发多路搜索 |
| `memory_predict` | 预测可能需要的记忆 |
| `memory_recommend` | 关联推荐 |

### 增强智能（5个）
| 工具 | 说明 |
|------|------|
| `memory_summary` | 记忆摘要生成 |
| `memory_inference` | 推理增强 |
| `memory_feedback` | 反馈学习（helpful/irrelevant/wrong/outdated） |
| `memory_export` | 导出：JSON / Markdown / CSV |
| `memory_lessons` | 经验沉淀：extract/recall/list/stats/delete |

### 配置与偏好
| 工具 | 说明 |
|------|------|
| `memory_preference_slots` | 用户偏好槽位（沟通风格/时区/语言/响应长度等） |

---

## 搜索算法流程

```
用户查询
    │
    ▼
┌─────────────────────────┐
│  Adaptive Skip Check    │ ← 短消息/闲聊直接跳过
└────────────┬────────────┘
             │ 需要检索
             ▼
┌─────────────────────────┐
│    Intent Router        │ ← 判断查询类型
│  FACT/PREF/RECENT/PROJ  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    BM25 Search          │ ← 关键词精确匹配
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Vector Search         │ ← Ollama nomic-embed-text
│   (via embed_cache)     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   LLM Rerank            │ ← Cross-Encoder 重排
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   MMR Diversity         │ ← 最大边际相关性
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Weibull Decay         │ ← 时间衰减
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Scope Filter          │ ← AGENT/USER/TEAM/GLOBAL
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   RRF Fusion            │ ← rank-based 分值融合
│   score = Σ 1/(k+rank) │
└────────────┬────────────┘
             │
             ▼
        返回 Top-K 结果
```

---

## 目录结构（147 个 JS 文件）

```
src/
├── index.js              # MCP Server 入口（33工具注册）
├── manager.js            # 记忆管理器
├── memory.js             # 核心 Memory 类
├── unified_memory.js     # 统一记忆接口
├── search.js            # 主搜索流程编排
├── storage.js           # JSON 存储层
├── config.js            # 配置管理
├── types.js             # 类型定义
├── utils.js             # 工具函数
│
├── tools/               # 17个 MCP 工具实现
│   ├── autostore.js
│   ├── concurrent_search.js
│   ├── decay.js
│   ├── dedup.js
│   ├── export.js
│   ├── feedback_learner.js
│   ├── health.js
│   ├── inference.js
│   ├── insights.js
│   ├── predict.js
│   ├── qa.js
│   ├── qmd_search.js
│   ├── recommend.js
│   ├── rerank.js
│   ├── summary.js
│   ├── templates.js
│   └── auto_extractor.js
│
├── core/                # 25个核心引擎模块
│   ├── adaptive.js
│   ├── association.js
│   ├── cache.js
│   ├── context.js
│   ├── faiss_index.js
│   ├── hierarchy.js
│   ├── hyde.js
│   ├── incremental_learning.js
│   ├── io.js
│   ├── llm_extract.js
│   ├── persistent_context.js
│   ├── proactive_care.js
│   ├── proactive_recall.js
│   ├── reflection.js
│   ├── reminder.js
│   ├── search.js
│   ├── sensitive.js
│   ├── source.js
│   ├── standard_format.js
│   ├── streaming.js
│   ├── tokenizer.js
│   ├── trace.js
│   ├── usage.js
│   ├── v2_patch.js
│   └── vector_backends.js
│
├── quality/              # 10个质量体系模块
├── graph/                # 3个知识图谱模块
├── collab/               # 13个协作系统模块
├── backup/               # 2个备份同步模块
├── benchmark/             # 4个基准测试模块
├── multimodal/           # 2个多模态模块
├── api/                  # 6个 API 层模块
├── agents/               # 13个 Agent 模块
├── system/               # 15个系统模块
├── visualize/            # 3个可视化模块
└── webui/                # 2个 WebUI 模块
```

---

## 使用方式

### MCP（推荐）

```bash
# 通过 mcporter 调用
mcporter call unified-memory memory_search '{"query": "刘总偏好", "topK": 5}'
mcporter call unified-memory memory_store '{"content": "用户喜欢简洁回复", "category": "preference", "importance": 0.9}'
mcporter call unified-memory memory_stats '{}'
```

### 直接运行

```bash
cd /root/.openclaw/workspace/skills/unified-memory
node src/index.js
```

---

## 配置

环境变量或 `~/.openclaw/workspace/memory/config.json`:

```json
{
  "ollamaUrl": "http://localhost:11434",
  "embedModel": "nomic-embed-text:latest",
  "llmModel": "minimax-m2.7:cloud",
  "dataPath": "~/.openclaw/workspace/memory/memories.json"
}
```

---

## 版本

当前版本: **v2.1.0** (2026-03-27)

---

## License

MIT
