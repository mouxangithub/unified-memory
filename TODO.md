# Unified Memory v2.0 - Node.js重构计划

## 架构设计

```
unified-memory/
├── src/
│   ├── core/           # 核心存储和搜索
│   │   ├── storage.js        ✅ 已完成
│   │   ├── bm25.js           ✅ 已完成
│   │   ├── vector.js         ✅ 已完成
│   │   ├── fusion.js         ✅ 已完成
│   │   ├── tokenizer.js      📋 待迁移
│   │   └── cache.js          📋 待迁移
│   │
│   ├── tools/          # 11个MCP工具
│   │   ├── index.js           ✅ 已完成
│   │   ├── insights.js        ✅ 已完成
│   │   ├── export.js         ✅ 已完成
│   │   ├── dedup.js          ✅ 已完成
│   │   ├── decay.js          ✅ 已完成
│   │   ├── qa.js             ✅ 已完成
│   │   └── qmd_search.js     📋 待迁移
│   │
│   ├── cli/            # CLI入口
│   │   ├── search.js         ✅ 已完成
│   │   └── index.js          📋 待迁移
│   │
│   ├── agents/         # 智能体
│   │   ├── memory_agent.js   📋 待迁移
│   │   ├── active_learner.js 📋 待迁移
│   │   └── feedback_learner.js 📋 待迁移
│   │
│   ├── collab/         # 多Agent协作
│   │   ├── agent_collab.js   📋 待迁移
│   │   └── collab_bus.js     📋 待迁移
│   │
│   ├── api/            # API服务器
│   │   ├── server.js        📋 待迁移
│   │   └── routes.js        📋 待迁移
│   │
│   ├── quality/        # 质量体系
│   │   ├── confidence.js    📋 待迁移
│   │   ├── dedup.js         ✅ 已完成
│   │   ├── decay.js         ✅ 已完成
│   │   └── smart_forgetter.js 📋 待迁移
│   │
│   ├── graph/          # 知识图谱
│   │   ├── graph.js         📋 待迁移
│   │   └── visualizer.js    📋 待迁移
│   │
│   ├── backup/         # 备份恢复
│   │   ├── backup.js        📋 待迁移
│   │   └── version_control.js 📋 待迁移
│   │
│   ├── webui/          # Web界面
│   │   └── dashboard.js     📋 待迁移
│   │
│   └── utils/          # 工具函数
│       ├── counter.js       ✅ 已完成
│       ├── text.js          ✅ 已完成
│       └── logger.js        📋 待迁移
│
├── tests/              # 测试
├── package.json        ✅ 已完成
└── README.md          📋 待重写
```

## Python → Node.js 模块映射

### 核心模块 (core/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory.py | storage.js | 存储读写 ✅ |
| memory_bm25.py | bm25.js | BM25搜索 ✅ |
| memory_vector.py | vector.js | 向量搜索 ✅ |
| memory_qmd_search.py | fusion.js | 混合搜索 ✅ |
| smart_chunk.py | tokenizer.js | 分词 |
| memory_cache.py | cache.js | 缓存 |

### 工具模块 (tools/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_insights.py | insights.js | 洞察 ✅ |
| memory_export.py | export.js | 导出 ✅ |
| memory_dedup.py | dedup.js | 去重 ✅ |
| memory_decay.py | decay.js | 衰减 ✅ |
| memory_qa.py | qa.js | 问答 ✅ |
| memory_qmd_search.py | qmd_search.js | QMD搜索 |
| memory_autostore.py | autostore.js | 自动存储 |
| active_learner.py | active_learner.js | 主动学习 |

### 智能体 (agents/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_agent.py | memory_agent.js | 记忆Agent |
| agent.py | agent.js | Agent基类 |
| agent_profile.py | agent_profile.js | Agent画像 |
| agent_task.py | agent_task.js | 任务管理 |

### 多Agent协作 (collab/)
| Python | Node.js | 说明 |
|--------|---------|------|
| agent_collab.py | agent_collab.js | 协作系统 |
| agent_collab_system.py | collab_system.js | 协作引擎 |
| memory_multi_agent_share.py | multi_agent_share.js | 记忆共享 |
| collab_bus.py | collab_bus.js | 协作总线 |
| collab_suggest.py | collab_suggest.js | 协作建议 |

### API服务器 (api/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_api_server.py | server.js | API服务 |
| memory_api.py | routes.js | 路由 |

### 质量体系 (quality/)
| Python | Node.js | 说明 |
|--------|---------|------|
| confidence_validator.py | confidence.js | 置信度验证 |
| memory_quality.py | quality.js | 质量评分 |
| memory_noise_filter.py | noise_filter.js | 噪声过滤 |
| smart_forgetter.py | smart_forgetter.js | 智能遗忘 |

### 知识图谱 (graph/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_graph.py | graph.js | 知识图谱 |
| memory_graph_visualizer.py | visualizer.js | 可视化 |
| knowledge_card.py | knowledge_card.js | 知识卡片 |

### 备份恢复 (backup/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_sync.py | sync.js | 同步 |
| memory_backup.py | backup.js | 备份 |
| memory_version_control.py | version_control.js | 版本控制 |

### Web UI (webui/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_webui.py | dashboard.js | 仪表盘 |

### 系统集成 (system/)
| Python | Node.js | 说明 |
|--------|---------|------|
| memory_openclaw_integration.py | openclaw.js | OpenClaw集成 |
| memory_plugin_system.py | plugin.js | 插件系统 |

## 迁移优先级

### P0 - 核心可用
1. storage, bm25, vector, fusion, config (已完成)
2. tools: insights, export, dedup, decay, qa (已完成)
3. CLI入口
4. 单元测试

### P1 - 日常使用
5. qmd_search (QMD本地文档搜索)
6. autostore (自动存储)
7. active_learner (主动学习)
8. smart_forgetter (智能遗忘)

### P2 - 企业功能
9. memory_agent (记忆Agent)
10. graph + visualizer (知识图谱)
11. api_server (API服务)
12. backup + version_control (备份)

### P3 - 高级功能
13. multi_agent_collaboration (多Agent协作)
14. webui dashboard (Web界面)
15. crossmodal (多模态)
