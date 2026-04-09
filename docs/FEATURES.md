# Unified Memory — 功能列表

> 完整的特性参考文档 | Complete Feature Reference

---

## 目录

- [核心架构](#核心架构)
- [存储与持久化](#存储与持久化)
- [搜索与检索](#搜索与检索)
- [智能处理](#智能处理)
- [可观测性](#可观测性)
- [协作与多租户](#协作与多租户)
- [v4.4+ 新增功能](#v44-新增功能)
- [v5.0 OpenViking 集成](#v50-openviking-集成)

---

## 核心架构

### 四层渐进式管线 (L0→L1→L2→L3)

```
L0 (对话录制) ──────────────────────────────────────────────
│  transcript_first.js
│  • 捕获原始对话，完整保留上下文
│  • JSONL 格式存储
│  • 支持增量捕获
▼
L1 (记忆提取) ──────────────────────────────────────────────
│  extract.js + memory_types/
│  • 从对话中提取关键信息、实体、关系、偏好
│  • 支持 6 种记忆类型自动检测
│  • LLM 实体/关系/偏好提取
▼
L2 (场景归纳) ──────────────────────────────────────────────
│  scene_block.js
│  • 按时间窗口聚类记忆，生成场景块
│  • 提取场景主题、关键实体、行动项
│  • 支持场景搜索和导航
▼
L3 (用户画像) ──────────────────────────────────────────────
│  profile.js + persona_generator.js
│  • 静态 + 动态双画像
│  • 用户偏好、习惯、目标
│  • 自动更新，定时刷新
```

### 分层压缩 (Token 节省)

| 层级 | Token 限制 | 用途 | 说明 |
|------|-----------|------|------|
| **L0** | ~100 tokens | 抽象层 | 快速过滤，向量搜索 |
| **L1** | ~2k tokens | 概览层 | 内容导航，重排序 |
| **L2** | 无限制 | 详情层 | 按需加载完整内容 |

---

## 存储与持久化

### WAL 协议 (Write-Ahead Log)

| 功能 | 说明 |
|------|------|
| 崩溃恢复 | 启动时自动回放未提交的操作 |
| Checksum 校验 | 每条 WAL 条目包含校验和 |
| 原子性写入 | WAL + 存储单事务 |
| 导出/导入 | JSONL 格式备份和恢复 |

### Tier 分层管理

| Tier | 最大年龄 | 最大数量 | 压缩率 | 存储位置 |
|------|---------|---------|--------|---------|
| **HOT** | 7 天 | 10 条 | 50% | `memory/hot/` |
| **WARM** | 30 天 | 50 条 | 30% | `memory/warm/` |
| **COLD** | 365 天 | 1000 条 | 10% | `memory/cold/` |

### 向量存储后端

| 后端 | 说明 | 配置 |
|------|------|------|
| **LanceDB** | 嵌入式向量数据库（默认） | `VECTOR_STORE_TYPE=lancedb` |
| **SQLite** | SQLite + sqlite-vec 扩展 | `VECTOR_STORE_TYPE=sqlite` |

### 存储后端

| 后端 | 模式 | 说明 |
|------|------|------|
| **JSON** | 文件（默认） | `memories.json`，写缓冲优化 |
| **SQLite** | 数据库 | `STORAGE_MODE=sqlite`，高并发 |

---

## 搜索与检索

### 混合搜索 (Hybrid Search)

```
BM25 关键词检索
      +
向量相似度检索 (cosine distance)
      ↓
RRF 融合 (Reciprocal Rank Fusion, k=60)
      ↓
Scope 范围过滤 (B-tree O(log n))
      ↓
Weibull 衰减 (time + access 加权)
      ↓
Top-K 结果 (带 evidence metadata)
```

### 向量搜索提供商

| 提供商 | 模型 | 维度 | 说明 |
|--------|------|------|------|
| **Ollama** | nomic-embed-text | 1536 | 本地，推荐 |
| **本地 Embedding** | embeddinggemma-300m | 768 | 完全离线 |
| **OpenAI** | text-embedding-3-small | 1536 | 需要 API key |
| **Jina** | jina-embeddings-v3 | 1024 | 免费额度 |
| **SiliconFlow** | Pro/Yg-16 | 2048 | 需要 API key |

### 搜索特性

| 功能 | 说明 |
|------|------|
| **BM25** | 关键词全文搜索，重要性加权 |
| **向量搜索** | 语义相似度检索 |
| **RRF 融合** | 归一化分数合并 |
| **MMR 重排** | Maximal Marginal Relevance 多样性优化 |
| **QMD 搜索** | Query Memory Document 结构化查询 |
| **并发搜索** | 多查询并行执行 |
| **范围过滤** | AGENT / USER / TEAM / GLOBAL 隔离 |
| **中文分词** | @node-rs/jieba 原生集成 |
| **Intent 路由** | 智能路由到合适的处理器 |
| **噪声过滤** | 过滤无意义查询 |

---

## 智能处理

### 记忆类型系统

| 类型 | 说明 | 优先级 | 保留期 |
|------|------|--------|---------|
| **facts** | 事实型记忆 | 高 | 永久 |
| **patterns** | 模式型记忆 | 中 | 6 个月 |
| **skills** | 技能型记忆 | 高 | 1 年 |
| **cases** | 案例型记忆 | 中 | 6 个月 |
| **events** | 事件型记忆 | 低 | 3 个月 |
| **preferences** | 偏好型记忆 | 高 | 永久 |

### 智能去重

| 策略 | 说明 |
|------|------|
| **精确去重** | 完全相同的文本 |
| **语义去重** | 向量相似度 > 0.95 |
| **FTS 去重** | 全文搜索相似度 > 0.85 |
| **LLM 去重** | LLM 深度判断矛盾 |

### 矛盾检测与解决

| 功能 | 说明 |
|------|------|
| **规则检测** | 地点、时间、状态矛盾 |
| **LLM 深度判断** | 复杂矛盾识别 |
| **自动解决** | 保留较新记忆，标记旧记忆为过期 |

### 遗忘曲线

| 功能 | 说明 |
|------|------|
| **Weibull 衰减** | Shape=1.5, Scale=30 天 |
| **访问奖励** | 每次访问 +5%，最高 +50% |
| **重要性加权** | 重要性 × 衰减系数 |

### 主动记忆管理

| 功能 | 说明 |
|------|------|
| **Proactive Care** | 监控和维护重要记忆 |
| **Proactive Recall** | 提醒用户相关记忆 |
| **Reminder** | 根据记忆内容设置提醒 |
| **临时过期** | 自动清理有过期时间的记忆 |

---

## 可观测性

### Web UI 仪表板

| 页面 | 功能 |
|------|------|
| **Overview** | 统计卡片、分类分布、最近记忆 |
| **Memory List** | 分页、过滤、排序 |
| **Search** | 关键词搜索 |
| **API** | REST API 端点 |

### REST API 端点

| 端点 | 功能 |
|------|------|
| `GET /api/stats` | 完整统计 |
| `GET /api/memories` | 记忆列表（分页） |
| `GET /api/categories` | 分类列表 |
| `GET /api/search?q=` | 搜索 |
| `GET /api/recent` | 最近记忆 |
| `GET /api/top` | 高重要性记忆 |
| `GET /health` | 健康检查 |

### 指标与追踪

| 功能 | 说明 |
|------|------|
| **Token 预算** | 自动压缩与限制 |
| **访问追踪** | 访问历史，修改追踪 |
| **证据链** | 来源追踪，置信度评分 |
| **版本历史** | 每条记忆最多 50 个修订版本 |

---

## 协作与多租户

### 泳道记忆 (Memory Lanes)

| 功能 | 说明 |
|------|------|
| **独立隔离** | 每个泳道独立的内存文件 |
| **搜索范围** | 独立的搜索范围 |
| **分层管理** | 独立的 Tier 管理 |

### 团队空间 (Team Spaces)

| 功能 | 说明 |
|------|------|
| **创建团队** | `memory_v4_create_team` |
| **团队存储** | `memory_v4_team_store` |
| **严格隔离** | 仅搜索团队内记忆，绝不泄露 |
| **共享访问** | 团队成员共享访问 |

### 范围系统 (Scope)

| Scope | 说明 |
|-------|------|
| **USER** | 当前用户私有（默认） |
| **TEAM** | 团队内共享 |
| **AGENT** | Agent 专用 |
| **GLOBAL** | 所有 Agent 和用户可访问 |

---

## v4.4+ 新增功能

### Benchmark 召回率验证

| 功能 | 说明 |
|------|------|
| **recall@K** | 前 K 个结果中包含的相关记忆比例 |
| **precision@K** | 前 K 个结果中相关记忆的占比 |
| **MRR** | 首个相关结果的倒数排名平均值 |
| **LoCoMo 格式** | 标准数据集加载器 |

### 可配置实体类型

| 功能 | 说明 |
|------|------|
| **配置文件加载** | `entity_types.json` |
| **运行时扩展** | 动态添加新类型 |
| **默认 8 种** | person, organization, project, topic, tool, location, date, event |

### 插件系统

| Hook | 触发时机 | 功能 |
|------|---------|------|
| **beforeSearch** | 搜索前 | 自定义查询处理 |
| **afterSearch** | 搜索后 | 后处理结果 |
| **beforeWrite** | 写入前 | 自定义写入逻辑 |
| **afterWrite** | 写入后 | 后处理记忆 |
| **onConflictDetected** | 冲突检测 | 自定义冲突解决 |

### 内置插件

| 插件 | 功能 |
|------|------|
| **kg-enrich** | 知识图谱增强 |
| **dedup** | 写入前去重 |
| **revision** | 版本追踪 |

### 数据清理器

| 功能 | 说明 |
|------|------|
| **自动清理** | 按 retentionDays 保留天数 |
| **每日定时** | 默认 03:00 |
| **向量清理** | 支持向量数据库清理 |

### 本地 Embedding

| 功能 | 说明 |
|------|------|
| **完全离线** | 无需任何 API |
| **node-llama-cpp** | GGUF 模型支持 |
| **自动回退** | 本地不可用时回退到远程 |

---

## v5.0 OpenViking 集成

### Viking URI 系统

```javascript
// URI 格式
viking://user/{user_id}/memories/preferences/coding
viking://agent/{agent_id}/memories/cases/{case_id}
viking://session/{session_id}/messages

// API
await client.ls('viking://user/ou_xxx/memories/')
await client.read('viking://user/ou_xxx/memories/preferences/coding.md')
await client.tree('viking://agent/')
```

### 意图分析 (Intent Analysis)

```javascript
// 输入
"帮我创建一个 RFC 文档"

// 输出
[
    TypedQuery(query="创建 RFC 文档", context_type=SKILL, intent="执行任务", priority=5),
    TypedQuery(query="RFC 文档模板", context_type=RESOURCE, intent="查找模板", priority=4),
    TypedQuery(query="用户的代码风格偏好", context_type=MEMORY, intent="个性化", priority=3)
]
```

### Session 管理

| 功能 | 说明 |
|------|------|
| **创建 Session** | 独立对话上下文 |
| **添加消息** | 记录用户/助手消息 |
| **使用追踪** | 记录使用的上下文和技能 |
| **提交归档** | 自动记忆提取 |

### 8 类记忆提取

| 类别 | 归属 | 说明 |
|------|------|------|
| **profile** | user | 用户身份/属性 |
| **preferences** | user | 用户偏好 |
| **entities** | user | 实体（人/项目） |
| **events** | user | 事件/决策 |
| **cases** | agent | 问题 + 解决方案 |
| **patterns** | agent | 可复用模式 |
| **tools** | agent | 工具使用知识 |
| **skills** | agent | 技能执行知识 |

### 文件系统命令

| 命令 | 说明 |
|------|------|
| **ls** | 列出目录 |
| **tree** | 获取目录树 |
| **read** | 读取文件 |
| **write** | 写入文件 |
| **grep** | 搜索文件内容 |
| **glob** | Glob 模式匹配 |

### 关系管理

| 功能 | 说明 |
|------|------|
| **link** | 添加关系 |
| **relations** | 查询关系 |
| **unlink** | 删除关系 |

### 文档解析器

| 格式 | 支持 |
|------|------|
| **Markdown** | ✅ |
| **Plain text** | ✅ |
| **PDF** | ✅ |
| **HTML** | ✅ |
| **Code** | ✅ Python, JS, TS, Go, Rust, Java, C/C++ |
| **Image** | ✅ |
| **Video** | ✅ |
| **Audio** | ✅ |

### 重排序 (Rerank)

| 提供商 | 模型 |
|--------|------|
| **Volcengine** | doubao-seed-rerank |
| **Cohere** | rerank models |
| **Jina** | jina-reranker |
| **Local** | 本地模型 |

---

## 功能索引

| 功能 | 工具/模块 | 版本 |
|------|----------|------|
| 四层管线 | `memory_pipeline_*` | v4.1+ |
| 场景归纳 | `memory_scene_*` | v4.1+ |
| 中文分词 | @node-rs/jieba | v4.1+ |
| Hook 集成 | before_prompt_build, agent_end | v4.1+ |
| 本地 Embedding | `memory_local_embedding_*` | v4.1.2+ |
| 数据清理器 | `memory_cleaner_*` | v4.1.1+ |
| Benchmark | `memory_benchmark_recall` | v4.4+ |
| 可配置实体 | `memory_entity_type_*` | v4.4+ |
| 插件系统 | `memory_plugin_*` | v4.4+ |
| Viking URI | `viking_uri.js` | v5.0 |
| 意图分析 | `intent_analyzer.js` | v5.0 |
| Session 管理 | `session_manager.js` | v5.0 |
| 8 类记忆 | `memory_extractor.js` | v5.0 |
| 分层压缩 | `layered_compressor.js` | v5.0 |
| 关系管理 | `relation_manager.js` | v5.0 |
| 文档解析 | `document_parser.js` | v5.0 |
| 重排序 | `reranker.js` | v5.0 |

---

*最后更新: 2026-04-09 | v5.0.0*
