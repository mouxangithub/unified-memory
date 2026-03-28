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
│   ├── index.js           # MCP Server 入口（86工具注册）
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

## 📦 MCP 工具 (86个)

### 核心工具（9个）
| 工具 | 说明 |
|------|------|
| `memory_search` | BM25 + Vector + RRF 混合搜索 |
| `memory_store` | 存储新记忆（支持重要性/类别/来源） |
| `memory_list` | 列出所有记忆 |
| `memory_delete` | 删除记忆 |
| `memory_stats` | 统计信息 |
| `memory_health` | 健康检查 |
| `memory_insights` | 用户洞察分析 |
| `memory_export` | 导出 json/markdown/csv |
| `memory_metrics` | 系统指标 |

### 检索增强（6个）
| 工具 | 说明 |
|------|------|
| `memory_bm25` | 纯 BM25 关键词搜索 |
| `memory_vector` | 纯向量语义搜索 |
| `memory_mmr` | 最大边际相关性多样性 |
| `memory_rerank_llm` | LLM 重排序 |
| `memory_adaptive` | 自适应检索策略 |
| `memory_concurrent_search` | 并发搜索 |

### Preference Slots（5个）
| 工具 | 说明 |
|------|------|
| `memory_preference_slots` | 用户偏好槽位 |
| `memory_preference_get` | 获取偏好值 |
| `memory_preference_set` | 设置偏好值 |
| `memory_preference_infer` | 从对话推断偏好 |
| `memory_preference_explain` | 偏好来源解释 |

### Semantic Versioning（3个）
| 工具 | 说明 |
|------|------|
| `memory_version_list` | 版本历史列表 |
| `memory_version_diff` | 版本差异对比 |
| `memory_version_timeline` | 版本时间线 |

### 主动与预测（6个）
| 工具 | 说明 |
|------|------|
| `memory_proactive_start` | 启动主动召回 |
| `memory_proactive_stop` | 停止主动召回 |
| `memory_proactive_status` | 召回状态 |
| `memory_proactive_recall` | 主动注入记忆 |
| `memory_proactive_trigger` | 触发召回 |
| `memory_proactive_care` | 主动关怀 |

### 知识图谱（4个）
| 工具 | 说明 |
|------|------|
| `memory_graph_entity` | 实体管理 |
| `memory_graph_relation` | 关系管理 |
| `memory_graph_query` | 图查询 |
| `memory_graph_stats` | 图统计 |

### RAG 与问答（3个）
| 工具 | 说明 |
|------|------|
| `memory_qa` | RAG 智能问答 |
| `memory_extract` | LLM 极速抽取 |
| `memory_summary` | 记忆摘要生成 |

### 质量与学习（5个）
| 工具 | 说明 |
|------|------|
| `memory_feedback` | 反馈学习 |
| `memory_noise` | 噪声过滤 |
| `memory_reflection` | 自我反思 |
| `memory_lessons` | 经验教训 |
| `memory_intent` | 意图识别 |

### 可观测性（5个）
| 工具 | 说明 |
|------|------|
| `memory_trace` | 检索链路追踪 |
| `memory_metrics` | 系统指标 |
| `memory_wal` | 预写日志 |
| `memory_templates` | 模板管理 |
| `memory_scope` | 四级隔离（AGENT/USER/TEAM/GLOBAL） |

### 生命周期（7个）
| 工具 | 说明 |
|------|------|
| `memory_autostore` | Hooks 自动存储 |
| `memory_decay` | Weibull 时间衰减 |
| `memory_tier` | 三层自动分层（HOT/WARM/COLD） |
| `memory_dedup` | 语义去重 |
| `memory_reminder_add` | 添加提醒 |
| `memory_reminder_cancel` | 取消提醒 |
| `memory_reminder_list` | 提醒列表 |
| `memory_qmd_search` | QMD 本地文档搜索 |

### 高级推理（5个）
| 工具 | 说明 |
|------|------|
| `memory_rollback` | 回滚到指定版本 |
| `memory_inference` | 上下文推理 |
| `memory_predict` | 记忆使用预测 |
| `memory_predict_enhanced` | 增强预测 |
| `memory_recommend` | 智能推荐 |

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
