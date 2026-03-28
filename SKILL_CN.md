---

<div align="center">

# 🧠 Unified Memory v2.5 (unified-memory)

> **🤖 本项目由小智 AI（OpenClaw）创建生成**  
> 作者：程序员小刘（@mouxangithub）  
> 框架：OpenClaw Agent | Node.js ESM | 76 个 MCP 工具

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

## v2.5 新增功能

| 功能 | 说明 |
|------|------|
| 🔄 **Scope 隔离** | LanceDB 查询层 scope 过滤（AGENT/USER/TEAM/GLOBAL） |
| 🔍 **QMD 后端** | OpenClaw 原生文档搜索后端接入 |
| ☁️ **云备份** | SuperMemory API + Custom REST 双模式同步 |
| 📈 **Weibull 衰减** | Weibull 分布遗忘曲线（shape=1.5, scale=30天） |
| 🔗 **Git 集成** | Git 版本化记忆快照 + git notes |
| 🏥 **Plugin 接口** | OpenClaw Memory Plugin 规范（memory_search/get/write） |
| ⚡ **Phase 3 完成** | 全部 76 个工具注册，零外部数据库依赖 |

---

## 架构

```
OpenClaw Agent
└── unified-memory (Node.js ESM)
    ├── MCP Server（63 个核心工具，index.js）
    ├── Plugin 接口（3 个工具：memory_search/get/write）
    ├── QMD 搜索后端（3 个工具）
    ├── Git 集成（7 个工具）
    ├── 云备份（3 个工具：SuperMemory + REST）
    ├── Weibull 衰减（2 个工具）
    ├── BM25 + Vector + RRF 混合搜索
    ├── Weibull 时间衰减（shape=1.5，scale=30天）
    ├── 多级 Scope 隔离（LanceDB 查询层）
    ├── 写前日志 WAL（崩溃恢复）
    ├── 知识图谱（实体提取）
    ├── 意图路由 + 噪音过滤
    ├── Preference Slots（结构化用户画像）
    └── 自我改进（反思、去重、Lesson 系统）
```

---

## 快速开始

```bash
# 1. 通过 Clawhub 安装（推荐）
clawhub install unified-memory

# 2. 验证安装
mcporter call unified-memory memory_health '{}'

# 3. 存储第一条记忆
mcporter call unified-memory memory_store '{"text": "你好世界", "category": "general"}'

# 4. 搜索记忆
mcporter call unified-memory memory_search '{"query": "你好"}'

# 5. 查看统计
mcporter call unified-memory memory_stats '{}'
```

---

## 76 个 MCP 工具完整清单

### 核心工具（9个）
| 工具 | 说明 |
|------|------|
| `memory_search` | 混合搜索：BM25 → Vector → Rerank → MMR → Decay → Scope → RRF |
| `memory_store` | 存储记忆（category/importance/tags/scope） |
| `memory_list` | 分页列出记忆，支持过滤器 |
| `memory_delete` | 删除记忆 |
| `memory_stats` | 统计：总数、分类分布、重要性分布 |
| `memory_health` | 健康检查：存储、向量引擎、缓存 |
| `memory_insights` | 用户洞察：分类分布、工具使用分析 |
| `memory_export` | 导出：JSON / Markdown / CSV |
| `memory_metrics` | 系统指标监控 |

### 搜索与检索（6个）
| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | Ollama 向量语义搜索（支持 scope 过滤） |
| `memory_mmr` | MMR 多样性选择 |
| `memory_rerank_llm` | LLM Cross-Encoder 重排序 |
| `memory_adaptive` | 自适应跳过非检索类查询 |
| `memory_concurrent_search` | 并发多路搜索 |

### Plugin 接口 — OpenClaw 规范（3个）⭐ 新增
| 工具 | 说明 |
|------|------|
| `phase3_memory_search` | 规范搜索，支持 scope 隔离 |
| `phase3_memory_get` | 规范记忆读取 |
| `phase3_memory_write` | 规范记忆写入 |

### QMD 搜索后端（3个）⭐ 新增
| 工具 | 说明 |
|------|------|
| `memory_qmd_query` | 查询 QMD 集合（workspace/daily-logs/projects） |
| `memory_qmd_status` | QMD 索引状态和集合信息 |
| `memory_qmd_search2` | QMD 混合搜索，支持 scope 过滤 |

### Git 集成（7个）⭐ 新增
| 工具 | 说明 |
|------|------|
| `memory_git_init` | 初始化 Git 仓库用于版本化记忆 |
| `memory_git_sync` | 将所有记忆同步到 Git 提交 |
| `memory_git_history` | 查看记忆提交历史 |
| `memory_git_note` | 为记忆添加 Git note |
| `memory_git_pull` | 从远程拉取 |
| `memory_git_push` | 推送到远程 |
| `memory_git_status` | Git 工作区状态 |

### 云备份（3个）⭐ 新增
| 工具 | 说明 |
|------|------|
| `memory_cloud_sync` | 同步记忆到云端（SuperMemory 或 Custom REST） |
| `memory_cloud_push` | 推送记忆到云端 |
| `memory_cloud_pull` | 从云端拉取记忆 |

### Weibull 衰减（2个）⭐ 新增
| 工具 | 说明 |
|------|------|
| `memory_decay_stats` | 每条记忆的衰减统计 |
| `memory_decay_strength` | 调整衰减强度乘数 |

### 主动与预测（6个）
| 工具 | 说明 |
|------|------|
| `memory_proactive_start` | 启动主动召回定时器 |
| `memory_proactive_stop` | 停止主动召回 |
| `memory_proactive_status` | 主动召回状态 |
| `memory_proactive_recall` | 主动注入记忆到上下文 |
| `memory_proactive_trigger` | 手动触发召回 |
| `memory_proactive_care` | 主动关怀触发 |

### 知识图谱（5个）
| 工具 | 说明 |
|------|------|
| `memory_graph_entity` | 实体提取与管理 |
| `memory_graph_relation` | 实体关系管理 |
| `memory_graph_query` | 图查询（实体关联路径） |
| `memory_graph_stats` | 图统计信息 |
| `memory_graph_add` | 添加实体到图 |

### RAG 与问答（3个）
| 工具 | 说明 |
|------|------|
| `memory_qa` | RAG 智能问答 |
| `memory_qmd_get` | 通过 QMD 获取本地文件内容 |
| `memory_qmd_list` | 列出 QMD 索引的文件 |

### 自我改进（8个）
| 工具 | 说明 |
|------|------|
| `memory_reflection` | 会话反思与洞察提取 |
| `memory_noise` | 噪音模式学习 |
| `memory_intent` | 意图分类 |
| `memory_extract` | 结构化实体提取 |
| `memory_dedup` | 去重合并 |
| `memory_lessons` | Lesson 系统（从错误中学习） |
| `memory_feedback` | 用户反馈集成 |
| `memory_rollback` | WAL 回滚 |

### Preference 与推理（6个）
| 工具 | 说明 |
|------|------|
| `memory_preference_slots` | 用户偏好槽位（结构化 KV） |
| `memory_preference_get` | 获取偏好值，含完整元数据 |
| `memory_preference_set` | 设置偏好值，含来源和置信度 |
| `memory_preference_infer` | 从对话历史推断偏好 |
| `memory_preference_explain` | 偏好来源解释 |
| `memory_inference` | 推理引擎 |

### 版本与模板（4个）
| 工具 | 说明 |
|------|------|
| `memory_version_list` | 记忆版本历史列表 |
| `memory_version_diff` | 两个版本间的差异对比 |
| `memory_version_timeline` | 版本时间线可视化 |
| `memory_templates` | 记忆模板 |

### 监控与运维（5个）
| 工具 | 说明 |
|------|------|
| `memory_wal` | 写前日志操作 |
| `memory_tier` | HOT/WARM/COLD 分层管理 |
| `memory_decay` | 衰减管理 |
| `memory_trace` | 搜索追踪 |
| `memory_reminder_*` | 提醒 CRUD |

### QMD 文件访问（2个）
| 工具 | 说明 |
|------|------|
| `memory_qmd_vsearch` | QMD 向量搜索 |
| `memory_scope` | Scope 规范化与过滤 |

### 推荐与摘要（4个）
| 工具 | 说明 |
|------|------|
| `memory_recommend` | 基于上下文推荐记忆 |
| `memory_summary` | 生成记忆摘要 |
| `memory_autostore` | 自动存储模式开关 |
| `memory_id` | 获取记忆 ID |

---

## Scope 级别

| 级别 | 说明 | 访问权限 |
|------|------|---------|
| `AGENT` | 单 Agent 私有记忆 | 仅该 Agent |
| `USER` | 单用户记忆 | 用户 scope 及以上 |
| `TEAM` | 团队共享记忆 | 团队 scope 及以上 |
| `GLOBAL` | 全局公开记忆 | 所有人 |

Scope 过滤在 **LanceDB 查询层**执行（非结果后过滤），确保真正的多租户隔离。

---

## 存储后端

- **主存储**：JSON 文件（`~/.openclaw/workspace/memory/memories.json`）
- **向量存储**：嵌入式 LanceDB（`~/.unified-memory/vector.lance`）
- **Embedding**：Ollama（`nomic-embed-text-v1.5`，768维）
- **零外部依赖**：不需要任何外部数据库

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v2.5.0 | 2026-03-28 | Phase 3：plugin 接口、QMD 后端、Git、云备份、Weibull |
| v2.4.0 | 2026-03-27 | Phase 2：86工具、知识图谱、主动召回、推荐系统 |
| v2.1.0 | 2026-03-27 | 33工具、分层/WAL/噪音过滤、ESM 重构 |
| v2.0.0 | 2026-03-26 | Node.js ESM 重构，BM25+Vector+RRF |
| v1.x | 2026-03-25 | Python 原型 |

---

## 安装方式

```bash
# Clawhub（推荐）
clawhub install unified-memory

# Curl 安装脚本
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash

# 手动安装
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory && npm install --ignore-scripts
```

---

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务器地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text-v1.5` | Embedding 模型 |
| `MEMORY_FILE` | `~/.openclaw/workspace/memory/memories.json` | 记忆存储路径 |
| `VECTOR_DB_DIR` | `~/.unified-memory/vector.lance` | LanceDB 路径 |

---

## 环境要求

- **Node.js**：≥ 22
- **Ollama**：≥ 0.1.40（可选；缺失时降级到纯 BM25）
- **OpenClaw**：≥ 2026.3（用于技能系统集成）
