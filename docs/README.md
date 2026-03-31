# Unified Memory Documentation
<!-- zh -->
> 统一记忆系统文档索引 | Documentation Index

---

## 📚 Documentation Overview
<!-- zh -->

| Document | Description |
|----------|-------------|
| **[README.md](README.md)** | 项目总览、快速开始 |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 系统架构详解（中英双语）|
| **[competitive-analysis.md](competitive-analysis.md)** | 竞品分析报告 |
| **[v3.8.0-release-notes.md](v3.8.0-release-notes.md)** | v3.8.x 版本发布说明 |
| **[../CHANGELOG.md](../CHANGELOG.md)** | 完整版本变更历史 |

---

## 🗂️ Documentation Structure
<!-- zh -->

```
docs/
├── README.md                    ← 文档索引（本文档）
├── ARCHITECTURE.md             ← 系统架构（中英双语）
├── competitive-analysis.md      ← 竞品分析
└── v3.8.0-release-notes.md      ← v3.8.x 发布说明

../
├── CHANGELOG.md                 ← 完整版本历史
├── SKILL.md                     ← Skill 定义
└── src/                         ← 源代码
    ├── storage.js               ← 核心存储
    ├── tier.js                  ← HOT/WARM/COLD 分层
    ├── search.js                ← 混合搜索
    ├── wal.js                   ← WAL 预写日志
    ├── evidence.js              ← 证据链
    └── organize.js              ← 自动整理
```

---

## 🚀 Quick Start
<!-- zh -->

```bash
# 安装依赖
npm install

# 初始化记忆系统
npm run init

# 写入第一条记忆
mcporter call unified-memory.memory_write(
  text: "Hello, World!",
  scope: "agent",
  category: "fact",
  importance: 0.8
)

# 搜索记忆
mcporter call unified-memory.memory_search(query: "Hello")
```

---

## 🔑 Core Concepts
<!-- zh -->

### 存储层 (Storage Layer)
- **Memory File** (`memory/*.md`) — 分层记忆文件
- **LanceDB** — 向量嵌入存储
- **BM25 Index** — 关键词全文索引
- **WAL** (`src/wal.js`) — 预写日志，崩溃恢复

### 搜索层 (Search Layer)
- **Hybrid Search** — BM25 + Vector + RRF 混合检索
- **Scope Isolation** — AGENT / USER / TEAM / GLOBAL 隔离
- **Weibull Decay** — 基于遗忘曲线的衰减

### 智能层 (Intelligence Layer)
- **Cognitive Scheduler** — 主动记忆探索
- **Memory Lanes** — 多车道并行
- **Evidence Chain** — 记忆来源追溯
- **Auto Organization** — 自动 HOT/WARM/COLD 分层

---

## 📖 Document Descriptions
<!-- zh -->

### [ARCHITECTURE.md](ARCHITECTURE.md)
**系统架构文档** — 详细阐述 unified-memory 的三层架构设计，包括存储层、搜索层、智能层的核心组件和交互关系。包含 ASCII 数据流图。

### [competitive-analysis.md](competitive-analysis.md)
**竞品分析报告** — 对比分析 Elite Longterm Memory、Smart Memory、Memory Tiering、Memory Qdrant 等竞品，明确 unified-memory 的优势和差距，包含实施路线图。

### [v3.8.0-release-notes.md](v3.8.0-release-notes.md)
**v3.8.x 发布说明** — 详细介绍 v3.8.0 的三大核心功能：WAL 协议、证据链机制、自动整理机制，包含新工具清单、迁移指南和技术细节。

### [../CHANGELOG.md](../CHANGELOG.md)
**完整版本历史** — 记录 unified-memory 从 v1.x 到 v3.8.0 的所有版本变更，包含每个版本的 features、bug fixes 和系统健康状态。

---

## 🛠️ Tools by Category
<!-- zh -->

| Category | Tool Count | Key Tools |
|----------|-----------|-----------|
| **Core** | ~30 | `memory_write`, `memory_read`, `memory_search`, `memory_delete` |
| **Session** | ~10 | `memory_session_*` |
| **Transcript** | ~8 | `memory_transcript_*` |
| **Git Notes** | ~10 | `memory_git_*` |
| **Revision** | ~5 | `memory_revision_*` |
| **Budget** | ~5 | `memory_budget_*` |
| **Cognitive** | ~5 | `memory_cognitive_*` |
| **Lanes** | ~5 | `memory_lanes_*` |
| **Cloud Backup** | ~6 | `memory_cloud_*` |
| **WAL** | ~6 | `memory_wal_*` |
| **Evidence** | ~5 | `memory_evidence_*` |
| **Organization** | ~5 | `memory_organize_*` |
| **Others** | ~17 | QMD, Weibull, KG, Identity, etc. |

**Total: 112 tools**

---

## 🔗 Related Resources
<!-- zh -->

- [GitHub Repository](https://github.com/mouxangithub/unified-memory)
- [Elite Longterm Memory](https://github.com/NextFrontierBuilds/elite-longterm-memory)
- [Smart Memory](https://github.com/nextfrontierbuilds/smart-memory)
- [Memory Tiering](https://github.com/nextfrontierbuilds/memory-tiering)
- [Memory Qdrant](https://github.com/nextfrontierbuilds/memory-qdrant)

---

*Last updated: 2026-03-31*
