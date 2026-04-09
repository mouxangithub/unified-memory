# API Reference — Unified Memory v5.0.1

> Complete MCP Tool API Reference | 完整的 MCP 工具 API 参考

**调用方式**: `mcporter call unified-memory <tool-name> '<json-arguments>'`

---

## 目录

- [存储核心](#存储核心)
- [搜索与检索](#搜索与检索)
- [四层管线](#四层管线)
- [场景系统](#场景系统)
- [知识图谱](#知识图谱)
- [证据链](#证据链)
- [WAL 协议](#wal-协议)
- [分析与统计](#分析与统计)
- [智能处理](#智能处理)
- [身份与偏好](#身份与偏好)
- [插件系统](#插件系统)
- [Benchmark](#benchmark)
- [团队协作](#团队协作)
- [v4.0 存储网关](#v40-存储网关)

---

## 存储核心

### memory_store

存储新记忆。

```bash
mcporter call unified-memory memory_store '{
  "text": "用户偏好简洁风格",
  "category": "preference",
  "importance": 0.8,
  "tags": ["风格", "设计"],
  "scope": "USER",
  "lane": "default"
}'
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | `string` | ✅ | 记忆内容 |
| `category` | `string` | 否 | 分类：fact / preference / habit / skill / goal / identity |
| `importance` | `number` | 否 | 重要度 0-1，默认 0.5 |
| `tags` | `string[]` | 否 | 标签列表 |
| `scope` | `string` | 否 | USER / TEAM / AGENT / GLOBAL |
| `lane` | `string` | 否 | 泳道名称 |

---

### memory_get

获取单条记忆。

```bash
mcporter call unified-memory memory_get '{"id": "mem_xxx"}'
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | `string` | ✅ | 记忆 ID |

---

### memory_list

分页列出记忆。

```bash
mcporter call unified-memory memory_list '{
  "page": 1,
  "pageSize": 20,
  "scope": "USER",
  "lane": "default"
}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | `number` | 否 | 1 | 页码 |
| `pageSize` | `number` | 否 | 20 | 每页数量 |
| `scope` | `string` | 否 | USER | 范围过滤 |
| `lane` | `string` | 否 | - | 泳道过滤 |
| `category` | `string` | 否 | - | 分类过滤 |
| `tier` | `string` | 否 | - | HOT / WARM / COLD |

---

### memory_delete

删除记忆。

```bash
mcporter call unified-memory memory_delete '{"id": "mem_xxx"}'
```

---

### memory_search

混合搜索（BM25 + Vector + RRF）。

```bash
mcporter call unified-memory memory_search '{
  "query": "用户偏好",
  "scope": "USER",
  "topK": 5,
  "category": "preference"
}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | `string` | ✅ | - | 搜索关键词 |
| `scope` | `string` | 否 | USER | 范围 |
| `topK` | `number` | 否 | 10 | 返回数量 |
| `category` | `string` | 否 | - | 分类过滤 |
| `lane` | `string` | 否 | - | 泳道 |
| `minScore` | `number` | 否 | 0.0 | 最低分数阈值 |
| `includeEvidence` | `boolean` | 否 | false | 包含证据链 |

---

## 搜索与检索

### memory_bm25

纯 BM25 关键词搜索。

```bash
mcporter call unified-memory memory_bm25 '{
  "query": "用户偏好",
  "scope": "USER",
  "topK": 10
}'
```

### memory_vector

向量相似度搜索。

```bash
mcporter call unified-memory memory_vector '{
  "query": "用户偏好深色主题",
  "scope": "USER",
  "topK": 10
}'
```

### memory_concurrent_search

并发多范围搜索。

```bash
mcporter call unified-memory memory_concurrent_search '{
  "query": "用户偏好",
  "scopes": ["USER", "TEAM"],
  "topK": 5
}'
```

### memory_mmr

MMR (Maximal Marginal Relevance) 重排。

```bash
mcporter call unified-memory memory_mmr '{
  "results": [...],
  "query": "用户偏好",
  "lambda": 0.5
}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `results` | `array` | ✅ | - | 待重排结果 |
| `query` | `string` | ✅ | - | 查询文本 |
| `lambda` | `number` | 否 | 0.5 | 多样性权重 0-1 |

### memory_qmd

QMD (Query Memory Document) 结构化搜索。

```bash
mcporter call unified-memory memory_qmd '{
  "query": "project roadmap",
  "topK": 10
}'
```

### memory_noise

过滤无意义查询。

```bash
mcporter call unified-memory memory_noise '{
  "query": "你好吗"
}'
```

### memory_intent

检测用户意图并路由。

```bash
mcporter call unified-memory memory_intent '{
  "query": "记住我喜欢深色主题"
}'
```

---

## 四层管线

### memory_pipeline_status

获取四层管线状态。

```bash
mcporter call unified-memory memory_pipeline_status '{}'
```

**返回值示例**:
```json
{
  "enabled": true,
  "stats": {
    "l1Executions": 5,
    "l2Executions": 2,
    "l3Executions": 1
  },
  "sessionCounters": {}
}
```

---

### memory_pipeline_trigger

手动触发管线阶段。

```bash
# 触发所有管线阶段
mcporter call unified-memory memory_pipeline_trigger '{
  "scope": "USER",
  "stage": "all"
}'

# 仅触发 L2
mcporter call unified-memory memory_pipeline_trigger '{
  "scope": "USER",
  "stage": "L2"
}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `string` | 否 | USER | 范围 |
| `stage` | `string` | 否 | all | L1 / L2 / L3 / all |

---

### memory_pipeline_config

更新管线配置。

```bash
mcporter call unified-memory memory_pipeline_config '{
  "config": {
    "enabled": true,
    "everyNConversations": 3,
    "l1IdleTimeoutSeconds": 60,
    "l2DelayAfterL1Seconds": 90
  }
}'
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | `boolean` | true | 是否启用 |
| `everyNConversations` | `number` | 5 | 每 N 轮触发 L1 |
| `enableWarmup` | `boolean` | true | Warm-up 模式 |
| `l1IdleTimeoutSeconds` | `number` | 60 | L1 触发延迟 |
| `l2DelayAfterL1Seconds` | `number` | 90 | L2 触发延迟 |
| `l2MinIntervalSeconds` | `number` | 300 | L2 最小间隔 |
| `l2MaxIntervalSeconds` | `number` | 1800 | L2 最大间隔 |
| `sessionActiveWindowHours` | `number` | 24 | Session 超时 |
| `l3TriggerEveryN` | `number` | 50 | L3 触发间隔 |

---

## 场景系统

### memory_scene_induct

从记忆中归纳场景块（L2）。

```bash
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER",
  "minMemories": 3,
  "maxScenes": 10,
  "timeRange": {
    "start": 1740000000000,
    "end": 1741000000000
  }
}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `string` | 否 | USER | 范围 |
| `minMemories` | `number` | 否 | 3 | 最少记忆数 |
| `maxScenes` | `number` | 否 | 20 | 最大场景数 |
| `timeRange.start` | `number` | 否 | - | 开始时间戳 |
| `timeRange.end` | `number` | 否 | - | 结束时间戳 |

---

### memory_scene_list

列出所有场景块。

```bash
mcporter call unified-memory memory_scene_list '{
  "scope": "USER",
  "limit": 20
}'
```

---

### memory_scene_get

获取场景块详情。

```bash
mcporter call unified-memory memory_scene_get '{
  "sceneId": "scene_xxx",
  "scope": "USER"
}'
```

---

### memory_scene_delete

删除场景块。

```bash
mcporter call unified-memory memory_scene_delete '{
  "sceneId": "scene_xxx",
  "scope": "USER"
}'
```

---

### memory_scene_search

搜索场景块。

```bash
mcporter call unified-memory memory_scene_search '{
  "query": "会议",
  "scope": "USER",
  "limit": 5
}'
```

---

### memory_scene_stats

获取场景统计。

```bash
mcporter call unified-memory memory_scene_stats '{"scope": "USER"}'
```

---

## 知识图谱

### memory_graph

知识图谱操作。

```bash
mcporter call unified-memory memory_graph '{"operation": "get_relations", "entity": "张三"}'
```

| operation | 说明 |
|-----------|------|
| `add_entity` | 添加实体 |
| `get_entity` | 获取实体 |
| `add_relation` | 添加关系 |
| `get_relations` | 获取关系 |
| `search` | 搜索实体 |

---

### memory_entity_types_list

列出所有实体类型配置。

```bash
mcporter call unified-memory memory_entity_types_list '{}'
```

**返回值示例**:
```json
{
  "types": [
    { "name": "person", "label": "人物", "color": "#667eea", "priority": 10 },
    { "name": "organization", "label": "组织", "color": "#10b981", "priority": 8 }
  ]
}
```

---

### memory_entity_type_add

添加或更新实体类型。

```bash
mcporter call unified-memory memory_entity_type_add '{
  "typeName": "framework",
  "label": "开发框架",
  "color": "#ff6b6b",
  "keywords": ["React", "Vue", "Angular"],
  "priority": 7
}'
```

---

### memory_entity_get

获取实体详情。

```bash
mcporter call unified-memory memory_entity_get '{"name": "张三"}'
```

---

### memory_entity_search

搜索实体。

```bash
mcporter call unified-memory memory_entity_search '{"query": "OpenClaw"}'
```

---

### memory_relation_add

添加实体关系。

```bash
mcporter call unified-memory memory_relation_add '{
  "source": "张三",
  "target": "OpenClaw",
  "relation": "founder_of"
}'
```

---

## 证据链

### memory_evidence_add

添加证据到记忆。

```bash
mcporter call unified-memory memory_evidence_add '{
  "memoryId": "mem_xxx",
  "type": "transcript",
  "sourceId": "msg_123",
  "confidence": 0.95
}'
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `memoryId` | `string` | ✅ | 记忆 ID |
| `type` | `string` | ✅ | transcript / message / manual / inference / git_note / revision |
| `sourceId` | `string` | ✅ | 来源 ID |
| `confidence` | `number` | 否 | 置信度 0-1 |

---

### memory_evidence_get

获取记忆的证据链。

```bash
mcporter call unified-memory memory_evidence_get '{"memoryId": "mem_xxx"}'
```

---

### memory_evidence_find_by_type

按类型查找证据。

```bash
mcporter call unified-memory memory_evidence_find_by_type '{"type": "transcript"}'
```

---

### memory_evidence_find_by_source

按来源查找证据。

```bash
mcporter call unified-memory memory_evidence_find_by_source '{"sourceId": "msg_123"}'
```

---

### memory_evidence_stats

获取证据统计。

```bash
mcporter call unified-memory memory_evidence_stats '{}'
```

---

## WAL 协议

### memory_wal_status

获取 WAL 状态。

```bash
mcporter call unified-memory memory_wal_status '{}'
```

**返回值示例**:
```json
{
  "total": 100,
  "pending": 5,
  "committed": 95
}
```

---

### memory_wal_write

写入 WAL 条目。

```bash
mcporter call unified-memory memory_wal_write '{
  "op": "insert",
  "collection": "memories",
  "data": {}
}'
```

---

### memory_wal_replay

重放 WAL 进行崩溃恢复。

```bash
mcporter call unified-memory memory_wal_replay '{}'
```

---

### memory_wal_truncate

截断 WAL。

```bash
mcporter call unified-memory memory_wal_truncate '{}'
```

---

### memory_wal_export

导出 WAL 为 JSONL。

```bash
mcporter call unified-memory memory_wal_export '{}'
```

---

### memory_wal_import

从 JSONL 导入 WAL。

```bash
mcporter call unified-memory memory_wal_import '{"file": "/path/to/wal.jsonl"}'
```

---

## 分析与统计

### memory_stats

获取记忆统计。

```bash
mcporter call unified-memory memory_stats '{}'
```

---

### memory_health

健康检查。

```bash
mcporter call unified-memory memory_health '{}'
```

**返回值示例**:
```json
{
  "status": "healthy",
  "storage": "ok",
  "vectorDb": "ok",
  "ollama": "connected",
  "wal": "clean"
}
```

---

### memory_metrics

获取详细使用指标。

```bash
mcporter call unified-memory memory_metrics '{}'
```

---

### memory_budget

获取 Token 预算状态。

```bash
mcporter call unified-memory memory_budget '{}'
```

---

### memory_tier

管理记忆层级。

```bash
mcporter call unified-memory memory_tier '{"operation": "list"}'
```

| operation | 说明 |
|-----------|------|
| `list` | 列出各层记忆 |
| `migrate` | 迁移到指定层 |
| `compress` | 压缩指定层 |

---

### memory_tier_stats

获取各层统计。

```bash
mcporter call unified-memory memory_tier_stats '{}'
```

---

### memory_decay

获取记忆衰减分数。

```bash
mcporter call unified-memory memory_decay '{"memoryId": "mem_xxx"}'
```

---

### memory_dedup

去重记忆。

```bash
mcporter call unified-memory memory_dedup '{"scope": "USER"}'
```

---

### memory_organize

整理记忆。

```bash
mcporter call unified-memory memory_organize '{"scope": "USER"}'
```

---

### memory_full_organize

全量整理。

```bash
mcporter call unified-memory memory_full_organize '{}'
```

---

### memory_archive_old

归档旧记忆。

```bash
mcporter call unified-memory memory_archive_old '{"olderThanDays": 365}'
```

---

### memory_cache

缓存管理。

```bash
mcporter call unified-memory memory_cache '{"operation": "stats"}'
```

---

### memory_scope

范围管理。

```bash
mcporter call unified-memory memory_scope '{"operation": "list"}'
```

---

### memory_dashboard

获取仪表盘数据。

```bash
mcporter call unified-memory memory_dashboard '{}'
```

---

## 智能处理

### memory_extract

从文本中提取实体、关系和事实。

```bash
mcporter call unified-memory memory_extract '{
  "text": "张三是OpenClaw的创始人，擅长JavaScript编程"
}'
```

---

### memory_reflection

反思过去的记忆，识别模式和洞察。

```bash
mcporter call unified-memory memory_reflection '{"scope": "USER"}'
```

---

### memory_lessons

生成和存储经验教训。

```bash
mcporter call unified-memory memory_lessons '{"topic": "项目管理"}'
```

---

### memory_preference

学习和应用用户偏好。

```bash
mcporter call unified-memory memory_preference '{"operation": "learn", "text": "用户喜欢简洁风格"}'
```

---

### memory_inference

从现有记忆推断新事实。

```bash
mcporter call unified-memory memory_inference '{"memoryId": "mem_xxx"}'
```

---

### memory_adaptive

自适应调整。

```bash
mcporter call unified-memory memory_adaptive '{"operation": "optimize"}'
```

---

### memory_compress_tier

压缩指定层的低重要度记忆。

```bash
mcporter call unified-memory memory_compress_tier '{"tier": "COLD"}'
```

---

### memory_recommend

推荐相关记忆。

```bash
mcporter call unified-memory memory_recommend '{"context": "正在讨论项目计划"}'
```

---

### memory_summary

生成记忆摘要。

```bash
mcporter call unified-memory memory_summary '{"scope": "USER"}'
```

---

### memory_qa

基于记忆的问答。

```bash
mcporter call unified-memory memory_qa '{"question": "用户有什么偏好？"}'
```

---

### memory_cognitive

认知分析。

```bash
mcporter call unified-memory memory_cognitive '{}'
```

---

### memory_insights

生成洞察。

```bash
mcporter call unified-memory memory_insights '{}'
```

---

### memory_predict

预测。

```bash
mcporter call unified-memory memory_predict '{"context": "用户正在写代码"}'
```

---

### memory_feedback

反馈学习。

```bash
mcporter call unified-memory memory_feedback '{
  "memoryId": "mem_xxx",
  "feedback": "准确"
}'
```

---

## 身份与偏好

### memory_identity_extract

从记忆中提取身份信息。

```bash
mcporter call unified-memory memory_identity_extract '{"text": "我叫张三，是一名工程师"}'
```

---

### memory_identity_get

获取存储的身份档案。

```bash
mcporter call unified-memory memory_identity_get '{"userId": "user_001"}'
```

---

### memory_identity_update

更新身份档案。

```bash
mcporter call unified-memory memory_identity_update '{
  "userId": "user_001",
  "profile": {
    "name": "张三",
    "role": "工程师"
  }
}'
```

---

## 插件系统

### memory_plugins_list

列出所有已注册插件。

```bash
mcporter call unified-memory memory_plugins_list '{}'
```

---

### memory_plugin_enable

启用插件。

```bash
mcporter call unified-memory memory_plugin_enable '{"pluginName": "kg-enrich"}'
```

---

### memory_plugin_disable

禁用插件。

```bash
mcporter call unified-memory memory_plugin_disable '{"pluginName": "dedup"}'
```

---

### memory_plugin_register

注册外部插件。

```bash
mcporter call unified-memory memory_plugin_register '{
  "name": "my-plugin",
  "version": "1.0.0",
  "hooks": {
    "beforeSearch": "async (query) => query"
  }
}'
```

---

## Benchmark

### memory_benchmark_recall

运行召回率基准测试。

```bash
mcporter call unified-memory memory_benchmark_recall '{}'
```

**返回值示例**:
```json
{
  "timestamp": "2026-04-09T00:00:00Z",
  "dataset_size": 100,
  "metrics": {
    "recall@1": 0.45,
    "recall@5": 0.72,
    "recall@10": 0.85,
    "precision@1": 0.45,
    "precision@5": 0.14,
    "mrr": 0.58
  },
  "results": [...]
}
```

---

## 团队协作

### memory_lanes

泳道管理。

```bash
mcporter call unified-memory memory_lanes '{"operation": "list"}'
```

---

### memory_v4_create_team

创建团队空间。

```bash
mcporter call unified-memory memory_v4_create_team '{
  "teamId": "team_alpha",
  "name": "Alpha Team"
}'
```

---

### memory_v4_list_teams

列出所有团队。

```bash
mcporter call unified-memory memory_v4_list_teams '{}'
```

---

### memory_v4_get_team

获取团队配置。

```bash
mcporter call unified-memory memory_v4_get_team '{"teamId": "team_alpha"}'
```

---

### memory_v4_delete_team

删除团队（记忆保留）。

```bash
mcporter call unified-memory memory_v4_delete_team '{"teamId": "team_alpha"}'
```

---

### memory_v4_team_store

在团队空间中存储记忆。

```bash
mcporter call unified-memory memory_v4_team_store '{
  "teamId": "team_alpha",
  "text": "团队项目计划"
}'
```

---

### memory_v4_team_search

严格团队隔离搜索。

```bash
mcporter call unified-memory memory_v4_team_search '{
  "teamId": "team_alpha",
  "query": "项目计划",
  "topK": 10
}'
```

---

## v4.0 存储网关

### memory_v4_stats

获取存储网关统计。

```bash
mcporter call unified-memory memory_v4_stats '{}'
```

---

### memory_v4_search

增量 BM25 搜索。

```bash
mcporter call unified-memory memory_v4_search '{
  "query": "用户偏好",
  "scope": "USER",
  "topK": 10
}'
```

---

### memory_v4_store

WAL + 增量索引单事务存储。

```bash
mcporter call unified-memory memory_v4_store '{
  "text": "记忆内容",
  "scope": "USER",
  "importance": 0.8
}'
```

---

### memory_v4_list

B-tree 范围过滤列表。

```bash
mcporter call unified-memory memory_v4_list '{
  "scope": "USER",
  "limit": 20,
  "offset": 0
}'
```

---

### memory_v4_hybrid_search

BM25 + 向量 RRF 融合。

```bash
mcporter call unified-memory memory_v4_hybrid_search '{
  "query": "用户偏好",
  "scope": "USER",
  "topK": 10
}'
```

---

### memory_v4_evidence_stats

Evidence 统计。

```bash
mcporter call unified-memory memory_v4_evidence_stats '{}'
```

---

### memory_v4_trim_evidence

手动触发 TTL 清理。

```bash
mcporter call unified-memory memory_v4_trim_evidence '{}'
```

---

### memory_v4_revision_stats

版本历史统计。

```bash
mcporter call unified-memory memory_v4_revision_stats '{}'
```

---

### memory_v4_rate_limit_status

限流状态。

```bash
mcporter call unified-memory memory_v4_rate_limit_status '{}'
```

---

### memory_v4_wal_status

WAL 状态。

```bash
mcporter call unified-memory memory_v4_wal_status '{}'
```

---

### memory_v4_wal_export

JSONL 导出 WAL。

```bash
mcporter call unified-memory memory_v4_wal_export '{}'
```

---

### memory_v4_wal_truncate

删除未提交 WAL。

```bash
mcporter call unified-memory memory_v4_wal_truncate '{}'
```

---

## 本地 Embedding

### memory_local_embedding_status

获取本地 Embedding 服务状态。

```bash
mcporter call unified-memory memory_local_embedding_status '{}'
```

---

### memory_local_embedding_warmup

启动模型预热。

```bash
mcporter call unified-memory memory_local_embedding_warmup '{}'
```

---

### memory_local_embedding_embed

使用本地模型获取向量。

```bash
mcporter call unified-memory memory_local_embedding_embed '{
  "text": "要获取向量的文本"
}'
```

---

## 数据清理器

### memory_cleaner_status

获取清理器状态。

```bash
mcporter call unified-memory memory_cleaner_status '{}'
```

---

### memory_cleaner_config

更新清理器配置。

```bash
mcporter call unified-memory memory_cleaner_config '{
  "config": {
    "enabled": true,
    "retentionDays": 30,
    "cleanTime": "03:00"
  }
}'
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | `boolean` | false | 是否启用 |
| `retentionDays` | `number` | 0 | 保留天数 |
| `cleanTime` | `string` | "03:00" | 清理时间 |
| `allowAggressiveCleanup` | `boolean` | false | 允许高风险清理 |

---

### memory_cleaner_run

手动执行清理。

```bash
mcporter call unified-memory memory_cleaner_run '{}'
```

---

## 云备份

### memory_cloud_backup

备份到云存储。

```bash
mcporter call unified-memory memory_cloud_backup '{}'
```

---

### memory_cloud_restore

从云备份恢复。

```bash
mcporter call unified-memory memory_cloud_restore '{"backupId": "backup_xxx"}'
```

---

### memory_cloud_backup_api

云备份 API 管理。

```bash
mcporter call unified-memory memory_cloud_backup_api '{"operation": "list_backups"}'
```

---

## 主动记忆

### memory_proactive

主动记忆管理。

```bash
mcporter call unified-memory memory_proactive '{"operation": "suggest"}'
```

---

### memory_proactive_care

主动关怀。

```bash
mcporter call unified-memory memory_proactive_care '{}'
```

---

### memory_proactive_recall

主动召回。

```bash
mcporter call unified-memory memory_proactive_recall '{}'
```

---

### memory_reminder

设置提醒。

```bash
mcporter call unified-memory memory_reminder '{
  "memoryId": "mem_xxx",
  "remindAt": "2026-04-10T10:00:00+08:00"
}'
```

---

## 版本与追踪

### memory_version

版本历史管理。

```bash
mcporter call unified-memory memory_version '{"memoryId": "mem_xxx"}'
```

---

### memory_trace

访问和修改追踪。

```bash
mcporter call unified-memory memory_trace '{"memoryId": "mem_xxx"}'
```

---

### memory_transcript

Transcript 管理。

```bash
mcporter call unified-memory memory_transcript '{"operation": "list"}'
```

---

### memory_session

会话记忆管理。

```bash
mcporter call unified-memory memory_session '{"operation": "list"}'
```

---

### memory_git_notes

Git commit 记忆。

```bash
mcporter call unified-memory memory_git_notes '{"operation": "list"}'
```

---

## 工具索引

| 类别 | 工具数 | 工具 |
|------|--------|------|
| 存储核心 | 5 | store, get, list, delete, search |
| 搜索检索 | 7 | bm25, vector, concurrent, mmr, qmd, noise, intent |
| 四层管线 | 3 | pipeline_status, pipeline_trigger, pipeline_config |
| 场景系统 | 6 | scene_induct, scene_list, scene_get, scene_delete, scene_search, scene_stats |
| 知识图谱 | 6 | graph, entity_types_list, entity_type_add, entity_get, entity_search, relation_add |
| 证据链 | 6 | evidence_add, evidence_get, evidence_find_by_type, evidence_find_by_source, evidence_stats |
| WAL 协议 | 6 | wal_status, wal_write, wal_replay, wal_truncate, wal_export, wal_import |
| 分析统计 | 15 | stats, health, metrics, budget, tier, tier_stats, decay, dedup, organize, full_organize, archive_old, cache, scope, dashboard |
| 智能处理 | 14 | extract, reflection, lessons, preference, inference, adaptive, compress_tier, recommend, summary, qa, cognitive, insights, predict, feedback |
| 身份偏好 | 3 | identity_extract, identity_get, identity_update |
| 插件系统 | 4 | plugins_list, plugin_enable, plugin_disable, plugin_register |
| Benchmark | 1 | benchmark_recall |
| 团队协作 | 6 | lanes, v4_create_team, v4_list_teams, v4_get_team, v4_delete_team, v4_team_store, v4_team_search |
| v4.0 存储网关 | 12 | v4_stats, v4_search, v4_store, v4_list, v4_hybrid_search, v4_evidence_stats, v4_trim_evidence, v4_revision_stats, v4_rate_limit_status, v4_wal_status, v4_wal_export, v4_wal_truncate |
| 本地 Embedding | 3 | local_embedding_status, local_embedding_warmup, local_embedding_embed |
| 数据清理器 | 3 | cleaner_status, cleaner_config, cleaner_run |
| 云备份 | 3 | cloud_backup, cloud_restore, cloud_backup_api |
| 主动记忆 | 4 | proactive, proactive_care, proactive_recall, reminder |
| 版本追踪 | 6 | version, trace, transcript, transcript_*, session, git_notes |

**总计**: 100+ MCP 工具

---

*最后更新: 2026-04-09 | v5.0.1*
