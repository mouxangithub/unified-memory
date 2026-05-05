# Unified Memory v5 系统架构

> 版本：5.3.0 | 更新日期：2026-05-05

## 1. 系统概述

Unified Memory v5 是一个面向 AI Agent 的**统一记忆系统**，支持：
- 多模态记忆存储（情景/语义/实体）
- 语义向量搜索 + BM25 混合检索
- 实体关系图谱 + 知识网络
- MCP 协议接口，兼容 OpenClaw / Claude / Cursor / Hermes

## 2. 核心模块

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Memory v5                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: 接口层 (MCP / REST / WebSocket)                   │
│  ─────────────────────────────────────────────────────────  │
│  Layer 3: 推理增强层 (Context Manager / Summarizer)         │
│  ─────────────────────────────────────────────────────────  │
│  Layer 2: 索引检索层 (Semantic Index / BM25 / Graph Query)  │
│  ─────────────────────────────────────────────────────────  │
│  Layer 1: 数据接入层 (Memory Store / Entity Extract / Dedup)│
├─────────────────────────────────────────────────────────────┤
│  存储适配器: PostgreSQL + LanceDB + Redis                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| **Memory Store** | `memory_store.js` | 接收记忆、验证、写入存储 |
| **Entity Extractor** | `entity_detection.js` | 实体识别、关系抽取 |
| **Semantic Index** | `memory_graph.js` | 向量索引、相似度计算 |
| **BM25 Search** | `bm25.js` | 关键词全文搜索 |
| **Context Manager** | `context_manager.js` | 上下文组装、记忆召回 |
| **Graph Query** | `memory_graph.js` | 关系路径、邻居查询 |
| **MCP Server** | `gbrain_mcp_server.js` | MCP 协议接口 |

## 3. 功能分层

### Layer 1: 数据接入层
- `memory_store()` - 存储记忆
- `deduplicate()` - 去重检测
- `validate()` - 数据验证

### Layer 2: 索引检索层
- `vector_search()` - 向量相似度搜索
- `bm25_search()` - BM25 关键词搜索
- `hybrid_search()` - 混合搜索 (RRF 融合)
- `graph_query()` - 图谱查询

### Layer 3: 推理增强层
- `context_recall()` - 基于上下文的记忆召回
- `summarize()` - 记忆摘要生成
- `link_entities()` - 实体链接

### Layer 4: 接口协议层
- MCP Tools: `memory_store`, `memory_search`, `memory_get`, `memory_update`, `memory_delete`, `memory_graph_query`
- MCP Resources: `memory://recent`, `memory://entities`, `memory://graph`
- MCP Prompts: `memory_recall`, `memory_context_inject`

## 4. 数据流

```
用户输入 → Layer 1 (存储+去重) 
         → Layer 2 (向量+BM25索引) 
         → Layer 3 (上下文组装)
         → Layer 4 (MCP接口输出)
```

## 5. 技术选型

| 组件 | 技术 | 用途 |
|------|------|------|
| 主存储 | PostgreSQL | 结构化数据、事务 |
| 向量索引 | LanceDB | 高效向量检索 |
| 缓存 | Redis | 热数据、队列 |
| 图谱 | 内存 NetworkX | 轻量图关系 |
| Embedding | Ollama / OpenAI | 文本向量化 |

## 6. 快速链接

- [快速安装](QUICK_START.md)
- [API 参考](API.md)
- [MCP 接口规范](MCP_INTERFACE.md)
