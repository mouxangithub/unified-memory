# 🧠 Unified Memory v2.0

> AI Agent 专用记忆系统 - 多层级、持久化、主动式记忆
> 完全使用 Node.js 重构，支持 MCP (Model Context Protocol)

[![GitHub stars](https://img.shields.io/github/stars/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green.svg)](https://nodejs.org/)

## 🌟 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 **持久化上下文** | 不再每次重新理解，持久化上下文窗口 |
| 🔍 **混合搜索** | BM25 + 向量 + RRF 融合 (完全本地) |
| 💬 **自动存储** | Hooks 模式，无需手动调用 |
| 📊 **用户洞察** | 类别分布、工具使用分析 |
| 🧹 **智能遗忘** | 低价值记忆自动淘汰 |
| 🔗 **知识图谱** | 实体提取和关系可视化 |
| 🤝 **多Agent协作** | 多 Agent 记忆同步 |
| 🏥 **健康检查** | 完整的系统健康监控 |

## 📁 架构

```
unified-memory/
├── src/
│   ├── index.js           # MCP Server 入口（34工具注册）
│   ├── search.js          # 核心搜索管道（BM25→Vector→Rerank→MMR→RRF）
│   │
│   ├── core/               # 核心引擎（25个模块）
│   │   ├── storage.js     # JSON 持久化存储
│   │   ├── bm25.js        # BM25 关键词搜索
│   │   ├── vector.js      # Ollama 向量搜索
│   │   ├── fusion.js       # RRF 融合
│   │   ├── tokenizer.js   # 智能分词
│   │   ├── cache.js        # 多级缓存
│   │   ├── adaptive.js     # 自适应检索策略
│   │   ├── hierarchy.js   # 层级记忆
│   │   └── ... (共25个)
│   │
│   ├── tools/             # 工具模块（17个）
│   │   ├── search.js      # 混合搜索
│   │   ├── store.js       # 存储
│   │   ├── insights.js     # 用户洞察
│   │   ├── dedup.js        # 相似去重
│   │   ├── decay.js        # 时间衰减
│   │   ├── tier.js         # 三层分层
│   │   └── ... (共17个)
│   │
│   ├── quality/           # 质量体系
│   │   ├── noise_filter.js
│   │   ├── confidence.js
│   │   └── smart_forgetter.js
│   │
│   ├── graph/             # 知识图谱
│   ├── backup/             # 多Agent同步
│   ├── api/                # REST API
│   ├── agents/             # 智能体
│   ├── collab/             # 协作系统
│   ├── visualize/          # 可视化
│   ├── webui/              # Web界面
│   ├── cli/                # CLI 入口
│   └── utils/              # 工具函数
│
├── tests/
├── package.json
├── SKILL.md               # OpenClaw Skill 规范（34工具完整文档）
└── README.md
```

## 🚀 快速开始

### MCP Server (用于 AI Agent)

```bash
# 直接运行
node src/index.js

# 使用 mcporter
mcporter call unified-memory memory_search '{"query": "刘总偏好"}'
```

### CLI 工具

```bash
# 搜索
node src/cli/index.js search "刘总偏好"

# 存储
node src/cli/index.js store "学会了React开发" --category learning --importance 0.8

# 统计
node src/cli/index.js stats

# 去重
node src/cli/index.js dedup --threshold 0.9

# 知识图谱
node src/cli/index.js graph build

# 启动API服务器
node src/cli/index.js server --port 38421
```

### REST API

```bash
# 搜索
curl "http://localhost:38421/search?q=刘总偏好&topK=5"

# 列出记忆
curl http://localhost:38421/memory

# 健康检查
curl http://localhost:38421/health
```

## 📦 MCP 工具 (34个)

### 核心工具
| 工具 | 说明 |
|------|------|
| `memory_search` | BM25 + Vector + RRF 混合搜索 |
| `memory_store` | 存储新记忆（支持重要性/类别/来源） |
| `memory_list` | 列出所有记忆 |
| `memory_delete` | 删除记忆 |
| `memory_stats` | 统计信息 |
| `memory_health` | 健康检查 |

### 检索增强
| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | 纯向量语义搜索 |
| `memory_mmr` | 最大边际相关性多样性 |
| `memory_rerank_llm` | LLM 重排序 |
| `memory_scope` | 四级隔离过滤（AGENT/USER/TEAM/GLOBAL） |
| `memory_adaptive` | 自适应检索策略 |
| `memory_intent` | 查询意图路由 |
| `memory_noise` | 噪声过滤 |

### 写入链路
| 工具 | 说明 |
|------|------|
| `memory_extract` | LLM 8秒极速抽取 6类记忆 |
| `memory_autostore` | Hooks 自动存储 |
| `memory_wal` | Write-Ahead Log 写入日志 |

### 智能处理
| 工具 | 说明 |
|------|------|
| `memory_dedup` | 批量相似去重（Jaccard 0.75） |
| `memory_decay` | Weibull 时间衰减 |
| `memory_tier` | 三层自动分层（HOT/WARM/COLD） |
| `memory_reflection` | 自我反思学习 |

### RAG 与问答
| 工具 | 说明 |
|------|------|
| `memory_qa` | RAG 智能问答 |
| `memory_inference` | 上下文推理 |

### 主动与预测
| 工具 | 说明 |
|------|------|
| `memory_predict` | 记忆使用预测 |
| `memory_recommend` | 智能推荐 |
| `memory_preference_slots` | 用户偏好提取 |
| `memory_lessons` | 经验教训学习 |

### 增强智能
| 工具 | 说明 |
|------|------|
| `memory_insights` | 用户洞察分析 |
| `memory_summary` | 记忆摘要生成 |
| `memory_feedback` | 反馈学习 |
| `memory_concurrent_search` | 并发搜索 |
| `memory_export` | 导出 json/markdown/csv |

### 配置与偏好
| 工具 | 说明 |
|------|------|
| `memory_templates` | 模板管理 |
| `memory_qmd_search` | QMD 本地文档搜索 |

## ⚙️ 配置

环境变量:

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
OLLAMA_LLM_MODEL=deepseek-v3.2:cloud
```

或创建 `~/.openclaw/workspace/memory/config.json`:

```json
{
  "ollamaUrl": "http://localhost:11434",
  "embedModel": "nomic-embed-text:latest",
  "llmModel": "minimax-m2.7:cloud"
}
```

## 🔌 接入 OpenClaw

```bash
# 在 mcporter.json 中注册
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory-ts/src/index.js"],
      "env": {},
      "lifecycle": "keep-alive"
    }
  }
}
```

## 📊 搜索算法

混合搜索使用 **RRF (Reciprocal Rank Fusion)**:

```
RRF_score = Σ 1/(k+rank_i)
```

- BM25: 关键词精确匹配
- Vector: 语义相似度 (Ollama nomic-embed-text)
- k=60: RRF 平滑参数

## 🔧 开发

```bash
# 安装依赖
npm install

# 测试 MCP Server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node src/index.js

# CLI 帮助
node src/cli/index.js help
```

## 📄 License

MIT

---

## 🔗 Other Languages | 其他语言

- [中文文档](./README_CN.md) - 完整中文文档
- [快速入门](./README_QUICK_START.md) - 🚀 3步快速上手
- [SKILL.md](./SKILL.md) - OpenClaw Skill specification

---

*更新: 2026-03-27*
