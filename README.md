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
│   ├── core/              # 核心引擎
│   │   ├── storage.js     # JSON/LanceDB 存储
│   │   ├── bm25.js        # BM25 关键词搜索
│   │   ├── vector.js      # Ollama 向量搜索
│   │   ├── fusion.js       # RRF 混合融合
│   │   ├── tokenizer.js   # 智能分词
│   │   └── cache.js        # 多级缓存
│   │
│   ├── tools/             # 工具模块
│   │   ├── index.js        # MCP Server 入口
│   │   ├── insights.js     # 用户洞察分析
│   │   ├── export.js       # 导出 json/markdown/csv
│   │   ├── dedup.js        # 相似去重
│   │   ├── decay.js        # 时间衰减
│   │   ├── qa.js          # RAG 智能问答
│   │   └── autostore.js    # 自动存储
│   │
│   ├── quality/            # 质量体系
│   │   ├── smart_forgetter.js  # 智能遗忘
│   │   ├── confidence.js       # 置信度验证
│   │   └── noise_filter.js     # 噪声过滤
│   │
│   ├── graph/              # 知识图谱
│   │   └── graph.js        # 实体关系图
│   │
│   ├── backup/             # 备份同步
│   │   └── sync.js        # 多Agent同步
│   │
│   ├── api/                # REST API
│   │   └── server.js       # HTTP API 服务器
│   │
│   ├── agents/             # 智能体
│   │   ├── memory_agent.js
│   │   └── active_learner.js
│   │
│   ├── collab/             # 协作系统
│   │   ├── agent_collab.js
│   │   └── collab_bus.js
│   │
│   ├── cli/                # CLI 入口
│   │   └── index.js
│   │
│   └── utils/              # 工具函数
│       ├── logger.js
│       ├── counter.js
│       └── text.js
│
├── tests/
├── package.json
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

## 📦 MCP 工具 (11个)

| 工具 | 说明 |
|------|------|
| `memory_search` | BM25 + Vector 混合搜索 |
| `memory_store` | 存储新记忆 |
| `memory_list` | 列出所有记忆 |
| `memory_delete` | 删除记忆 |
| `memory_insights` | 用户洞察分析 |
| `memory_export` | 导出 json/markdown/csv |
| `memory_dedup` | 相似记忆去重 |
| `memory_decay` | 时间衰减 |
| `memory_qa` | RAG 智能问答 |
| `memory_stats` | 统计信息 |
| `memory_health` | 健康检查 |

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
