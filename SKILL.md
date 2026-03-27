# 🧠 Unified Memory v2.0 (unified-memory-ts)

> **完全使用 Node.js ESM 重构** | 129 个模块 | MCP + REST + CLI + WebUI

**项目路径**: `/root/.openclaw/workspace/skills/unified-memory-ts/`

---

## 架构关系

```
OpenClaw Agent
└── unified-memory-ts (Node.js ESM 技能层)
    ├── memory-lancedb-pro (OpenClaw 内置插件) ← 核心存储引擎
    │   ├── Hybrid Search (BM25 + Vector)
    │   ├── Cross-Encoder Rerank
    │   ├── Weibull Decay
    │   ├── Smart Extraction (LLM)
    │   └── Multi-Scope Isolation
    │
    └── 129 个 Node.js 模块
        ├── MCP Server (11 tools)
        ├── REST API 服务器
        ├── WebUI 服务器
        ├── CLI 工具
        ├── Workflow Engine
        ├── Sandbox
        ├── Code Generator
        ├── Push System
        └── LLM Provider (多后端)
```

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 **持久化上下文** | 不再每次重新理解，持久化上下文窗口 |
| 🔍 **混合搜索** | BM25 + 向量 + RRF 融合（完全本地） |
| 💬 **自动存储** | Hooks 模式，无需手动调用 |
| 📊 **用户洞察** | 类别分布、工具使用分析 |
| 🧹 **智能遗忘** | 低价值记忆自动淘汰 |
| 🔗 **知识图谱** | 实体提取和关系可视化 |
| 🤝 **多Agent协作** | 多 Agent 记忆同步 |
| 🏥 **健康检查** | 完整的系统健康监控 |

---

## 129 个 Node.js 模块完整列表

### 核心引擎 (core/)
| 模块 | 说明 |
|------|------|
| `adaptive.js` | 自适应置信度 |
| `association.js` | 关联推荐 |
| `cache.js` | 多级缓存 (L1/L2/L3) |
| `context.js` | 持久化上下文 |
| `faiss_index.js` | FAISS 向量索引 |
| `hierarchy.js` | 分层记忆池 |
| `hyde.js` | HyDE 搜索增强 |
| `incremental_learning.js` | 增量学习 |
| `io.js` | 输入输出 |
| `llm_extract.js` | LLM 智能提取 |
| `persistent_context.js` | 持久化上下文管理 |
| `proactive_care.js` | 主动感知缓存 |
| `proactive_recall.js` | 主动注入 |
| `reflection.js` | 反思机制 |
| `reminder.js` | 智能提醒 |
| `search.js` | 统一搜索接口 |
| `sensitive.js` | 敏感信息检测 |
| `source.js` | 来源追踪 |
| `standard_format.js` | 标准格式 |
| `streaming.js` | 流式处理 |
| `tokenizer.js` | 智能分词 |
| `trace.js` | 决策追溯链 |
| `usage.js` | 使用统计 |
| `v2_patch.js` | v2 兼容补丁 |
| `vector_backends.js` | 向量后端管理 |

### 存储层 (storage.js / storage/)
| 模块 | 说明 |
|------|------|
| `storage.js` | JSON/LanceDB 存储 |
| `vector.js` | Ollama 向量搜索 |
| `bm25.js` | BM25 关键词搜索 |
| `fusion.js` | RRF 混合融合 |

### 工具模块 (tools/)
| 模块 | 说明 |
|------|------|
| `autostore.js` | 自动存储 |
| `concurrent_search.js` | 并发查询 |
| `decay.js` | 时间衰减 |
| `dedup.js` | 相似去重 |
| `export.js` | 导出 json/markdown/csv |
| `feedback_learner.js` | 反馈学习 |
| `health.js` | 健康检查 |
| `inference.js` | 推理增强 |
| `insights.js` | 用户洞察分析 |
| `predict.js` | 记忆预测 |
| `qa.js` | RAG 智能问答 |
| `qmd_search.js` | QMD 风格搜索 |
| `recommend.js` | 关联推荐 |
| `rerank.js` | 重排器 |
| `summary.js` | 记忆摘要 |
| `templates.js` | 模板系统 |
| `auto_extractor.js` | 自动提取 |

### 质量体系 (quality/)
| 模块 | 说明 |
|------|------|
| `analytics.js` | 质量分析 |
| `audit.js` | 审计日志 |
| `confidence.js` | 置信度验证 |
| `noise_filter.js` | 噪声过滤 |
| `optimization.js` | 性能优化 |
| `privacy.js` | 隐私保护 |
| `quality.js` | 质量指标 |
| `smart_compress.js` | L3 智能压缩 |
| `smart_forgetter.js` | 智能遗忘 |
| `weibull_decay.js` | Weibull 衰减 |

### 知识图谱 (graph/)
| 模块 | 说明 |
|------|------|
| `graph.js` | 实体关系图 |
| `knowledge_card.js` | 知识卡片 |
| `knowledge_merger.js` | 知识合并 |

### 协作系统 (collab/)
| 模块 | 说明 |
|------|------|
| `agent_collab.js` | Agent 协作 |
| `analytics.js` | 协作分析 |
| `cloud.js` | 云端同步 |
| `cloud_deployment.js` | 云端部署 |
| `collab.js` | 协作管理 |
| `collab_bus.js` | 协作总线 |
| `collab_suggest.js` | 协作建议 |
| `distributed_sync.js` | 分布式同步 |
| `multi_agent_share.js` | 多 Agent 共享 |
| `multi_tenant.js` | 多租户 |
| `push.js` | Push 推送系统 |
| `realtime_sync.js` | 实时同步 |
| `sync.js` | 同步管理 |

### 备份同步 (backup/)
| 模块 | 说明 |
|------|------|
| `backup.js` | 备份管理 |
| `sync.js` | 多 Agent 同步 |

### 基准测试 (benchmark/)
| 模块 | 说明 |
|------|------|
| `benchmark.js` | 基准测试 |
| `perf.js` | 性能分析 |
| `pool.js` | 连接池 |
| `real_benchmark.js` | 真实评测 |

### 多模态 (multimodal/)
| 模块 | 说明 |
|------|------|
| `crossmodal.js` | 跨模态检索 |
| `multimodal.js` | 多模态记忆 |

### API 层 (api/)
| 模块 | 说明 |
|------|------|
| `api.js` | API 入口 |
| `mcp_server.js` | MCP Server (11 tools) |
| `rest_server.js` | REST API 服务器 |
| `routes.js` | 路由管理 |
| `server.js` | HTTP 服务器 |
| `simple_server.js` | 简化服务器 |

### CLI (cli/)
| 模块 | 说明 |
|------|------|
| `index.js` | CLI 入口 |
| `search.js` | 搜索命令 |

### Agents (agents/)
| 模块 | 说明 |
|------|------|
| `active_learner.js` | 主动学习器 |
| `agent.js` | Agent 核心 |
| `agent_collab_system.js` | 协作系统 |
| `agent_memory.js` | Agent 记忆 |
| `agent_profile.js` | Agent 画像 |
| `bridge.js` | 桥接器 |
| `memory_agent.js` | 记忆 Agent |
| `optimize.js` | 优化器 |
| `rerank_full.js` | 完整重排 |
| `roles.js` | 角色系统 |
| `sqlite.js` | SQLite 备用存储 |
| `usage_stats.js` | 使用统计 |
| `version_control.js` | 版本控制 |

### 系统模块 (system/)
| 模块 | 说明 |
|------|------|
| `all_in_one.js` | 一体化入口 |
| `code_generator.js` | 代码生成器 |
| `compress_eval.js` | 压缩质量评估 |
| `fallback_handler.js` | 降级处理 |
| `integration.js` | 集成钩子 |
| `llm_provider.js` | LLM Provider (多后端) |
| `local_llm.js` | 本地 LLM |
| `multimodal_fusion.js` | 多模态融合 |
| `openclaw_integration.js` | OpenClaw 集成 |
| `plugin_system.js` | 插件系统 |
| `preheat.js` | 批量预热 |
| `sandbox.js` | 代码沙箱 (Docker) |
| `task_queue.js` | 任务队列 |
| `workflow_engine.js` | 工作流引擎 (SOP + DAG) |

### 可视化 (visualize/)
| 模块 | 说明 |
|------|------|
| `graph_visualizer.js` | 图谱可视化 |
| `heatmap.js` | 热力图 |
| `visualize.js` | 可视化引擎 |

### WebUI (webui/)
| 模块 | 说明 |
|------|------|
| `dashboard.js` | Web Dashboard |
| `webui.js` | WebUI 服务器 |

### 工具函数 (utils/)
| 模块 | 说明 |
|------|------|
| `counter.js` | 计数器 |
| `logger.js` | 日志系统 |
| `text.js` | 文本处理 |

### 根目录入口
| 模块 | 说明 |
|------|------|
| `index.js` | MCP Server 入口 |
| `manager.js` | 管理器 |
| `memory.js` | 记忆核心 |
| `types.js` | 类型定义 |
| `unified_memory.js` | 统一记忆 |
| `config.js` | 配置管理 |

---

## 使用方式

### MCP Server (11 tools)

```bash
# 直接运行
node src/index.js

# 使用 mcporter
mcporter call unified-memory memory_search '{"query": "刘总偏好"}'
```

| MCP 工具 | 说明 |
|----------|------|
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

# 健康检查
node src/cli/index.js health

# 启动 API 服务器
node src/cli/index.js server --port 38421

# 启动 WebUI 服务器
node src/cli/index.js webui --port 38422
```

### REST API

```bash
# 搜索
curl "http://localhost:38421/search?q=刘总偏好&topK=5"

# 存储
curl -X POST http://localhost:38421/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "记忆内容", "category": "learning"}'

# 列出记忆
curl http://localhost:38421/memory

# 健康检查
curl http://localhost:38421/health

# 统计
curl http://localhost:38421/stats

# 导出
curl "http://localhost:38421/export?format=markdown"
```

### WebUI

```bash
# 启动
node src/webui/webui.js --port 38422

# 访问
open http://localhost:38422
```

### Workflow Engine (SOP + DAG)

```bash
# 执行工作流
node src/system/workflow_engine.js --flow my_workflow

# SOP 模式
node src/system/workflow_engine.js --mode sop --steps step1,step2,step3

# DAG 模式
node src/system/workflow_engine.js --mode dag --file workflow.json
```

### Sandbox (Docker 隔离执行)

```bash
# 执行代码
node src/system/sandbox.js --lang python --code "print('hello')"

# 多语言支持: python / javascript / typescript / bash / go / ruby
```

### Code Generator

```bash
# 生成项目
node src/system/code_generator.js --type fastapi --name my_api

# 支持: fastapi / flask / django / express / docker
```

### Push System

```bash
# 推送记忆
node src/collab/push.js --to agent_id --priority high

# 实时同步
node src/collab/realtime_sync.js --interval 30
```

### LLM Provider (多后端)

```bash
# 配置
node src/system/llm_provider.js --provider openai --model gpt-4

# 支持: openai / claude / 智谱 / 百度 / 阿里 / ollama
```

---

## 配置

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

---

## 搜索算法

混合搜索使用 **RRF (Reciprocal Rank Fusion)**:

```
RRF_score = Σ 1/(k+rank_i)
```

- BM25: 关键词精确匹配
- Vector: 语义相似度 (Ollama nomic-embed-text)
- k=60: RRF 平滑参数

---

## 开发

```bash
# 安装依赖
npm install

# 测试 MCP Server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node src/index.js

# CLI 帮助
node src/cli/index.js help

# 运行 benchmark
node src/benchmark/benchmark.js
```

---

## 版本

当前版本: **v2.0.0** (2026-03-27)

---

## License

MIT

---

## 🔗 Other Languages | 其他语言

- [English Version](./SKILL_EN.md) - Full English SKILL documentation
- [README.md](./README.md) - Full English documentation
- [README_CN.md](./README_CN.md) - 完整中文文档
- [README_QUICK_START.md](./README_QUICK_START.md) - 🚀 快速入门指南
