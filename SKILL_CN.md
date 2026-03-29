---

<div align="center">

# 🧠 Unified Memory v3.x (unified-memory)

> **🤖 本项目由小智 AI（OpenClaw）创建生成**  
> 作者：程序员小刘（@mouxangithub）  
> 框架：OpenClaw Agent | Node.js ESM | 51 个 MCP 工具

**项目路径**: `/root/.openclaw/workspace/skills/unified-memory/`  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**安装**: `clawhub install unified-memory`

---

## 🌍 Documentation | 文档索引

| Language | README | Skill |
|----------|--------|-------|
| 🇨🇳 中文 ✅ | [README_CN.md](README_CN.md) | [SKILL_CN.md](SKILL_CN.md) |
| 🇺🇸 English | [README.md](README.md) | [SKILL.md](SKILL.md) |

---

## v3.x 核心变化

| 变化 | 说明 |
|------|------|
| ⚡ **工具整合** | 76 → 28 个工具（统一 action 参数入口） |
| 🔧 **可配置架构** | LanceDB / Ollama / none 三层均可独立配置 |
| 📄 **配置文档** | 新增 docs/CONFIG.md 详解四种配置模式 |
| 🏗️ **向量引擎可插拔** | lancedb（默认）/ ollama / none |
| 🤖 **LLM 可插拔** | ollama（默认）/ openai / none |
| ☁️ **LanceDB Cloud** | 支持云端托管 embedding，零本地 Ollama 依赖 |

---

## 架构

```
OpenClaw Agent
└── unified-memory (Node.js ESM)
    ├── MCP Server（28 个工具，统一 action 参数入口）
    ├── 存储层：JSON + WAL（崩溃可恢复）
    ├── 向量层（可插拔）：
    │   ├── LanceDB（默认，零配置）
    │   ├── Ollama Embedding（可选）
    │   └── none（纯 BM25 模式）
    ├── LLM 层（可插拔）：
    │   ├── Ollama（默认，本地）
    │   └── none（降级到规则模式）
    ├── 分层管理：HOT / WARM / COLD
    └── Scope 隔离：AGENT / USER / TEAM / GLOBAL
```

---

## 配置模式

| 模式 | 向量引擎 | Embedding | LLM | 适用场景 |
|------|---------|-----------|-----|---------|
| 默认（推荐）✅ | LanceDB | Ollama | Ollama | 完全本地离线 |
| 轻量模式 | none | none | none | 纯存储需求 |
| 本地向量 | LanceDB | Ollama | none | 有 embedding 但无 LLM |
| 云端托管 ☁️ | LanceDB Cloud | LanceDB managed | Ollama/OpenAI | 不想运维 Ollama |

详见 [docs/CONFIG.md](docs/CONFIG.md)

---

## 快速开始

```bash
# 1. 通过 Clawhub 安装（推荐）
clawhub install unified-memory

# 2. 验证安装
mcporter call unified-memory memory_health '{}'

# 3. 存储记忆
mcporter call unified-memory memory_store '{"text": "你好世界", "category": "general"}'

# 4. 搜索记忆
mcporter call unified-memory memory_search '{"query": "你好"}'

# 5. 查看统计
mcporter call unified-memory memory_stats '{}'
```

---

## 51 个 MCP 工具完整清单

### 存储核心（5个）
| 工具 | 说明 |
|------|------|
| `memory_store` | 存储记忆（category/importance/tags/scope） |
| `memory_get` | 获取单条记忆 |
| `memory_list` | 分页列出记忆 |
| `memory_delete` | 删除记忆 |
| `memory_search` | 混合搜索：BM25 → Vector → Rerank → MMR |

### 统一入口（10个，action 参数）
| 工具 | action 参数 |
|------|------------|
| `memory_reminder` | add / list / cancel |
| `memory_preference` | get / set / infer / explain / stats / slots |
| `memory_version` | list / diff / restore |
| `memory_tier` | status / migrate / compress |
| `memory_proactive` | status / trigger / start / stop |
| `memory_proactive_care` | - |
| `memory_proactive_recall` | - |
| `memory_qmd` | search / get / vsearch / list / status |
| `memory_engine` | bm25 / embed / search / mmr / rerank |
| `memory_graph` | entity / relation / query / stats / add / delete |

### 检索增强（4个）
| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | 向量语义搜索（Ollama Embedding） |
| `memory_scope` | Scope 规范化与过滤 |
| `memory_concurrent_search` | 并发多路搜索合并 |

### 分析管理（9个）
| 工具 | 说明 |
|------|------|
| `memory_trace` | 搜索追踪 |
| `memory_metrics` | 系统指标监控 |
| `memory_noise` | 噪音模式学习 |
| `memory_decay` | 衰减管理 |
| `memory_dedup` | 去重合并 |
| `memory_extract` | 结构化实体提取 |
| `memory_reflection` | 会话反思与洞察提取 |
| `memory_intent` | 意图分类 |
| `memory_wal` | 写前日志操作 |

### 云与系统（10个）
| 工具 | 说明 |
|------|------|
| `memory_cloud_backup` | 云端备份 |
| `memory_cloud_restore` | 云端恢复 |
| `memory_export` | 导出：JSON / Markdown / CSV |
| `memory_adaptive` | 自适应搜索策略 |
| `memory_autostore` | 自动存储模式开关 |
| `memory_auto_extract` | 自动实体提取开关 |
| `memory_health` | 健康检查 |
| `memory_insights` | 用户洞察分析 |
| `memory_predict` | 预测性召回 |
| `memory_feedback` | 用户反馈集成 |

---

## Scope 隔离

| 级别 | 说明 | 访问权限 |
|------|------|---------|
| `AGENT` | 单 Agent 私有记忆 | 仅该 Agent |
| `USER` | 单用户记忆 | 用户 scope 及以上 |
| `TEAM` | 团队共享记忆 | 团队 scope 及以上 |
| `GLOBAL` | 全局公开记忆 | 所有人 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.x | 2026-03-29 | 工具整合 76→28，可插拔架构，四种配置模式 |
| v2.5.0 | 2026-03-28 | Phase 3：plugin 接口、QMD 后端、Git、云备份、Weibull |
| v2.4.0 | 2026-03-27 | Phase 2：86工具、知识图谱、主动召回、推荐系统 |
| v2.1.0 | 2026-03-27 | 33工具、分层/WAL/噪音过滤、ESM 重构 |
| v2.0.0 | 2026-03-26 | Node.js ESM 重构，BM25+Vector+RRF |
| v1.x | 2026-03-25 | Python 原型 |

---

## 环境要求

- **Node.js**：≥ 22
- **Ollama**：≥ 0.1.40（可选；缺失时降级到纯 BM25）
- **OpenClaw**：≥ 2026.3（用于技能系统集成）

---

## 配置项

详见 [docs/CONFIG.md](docs/CONFIG.md)

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `VECTOR_ENGINE` | `lancedb` | 向量引擎：lancedb / ollama / none |
| `LLM_PROVIDER` | `ollama` | LLM 提供者：ollama / openai / none |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务器地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `LANCEDB_API_KEY` | （空） | LanceDB Cloud API Key（可选） |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |
