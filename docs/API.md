# API 文档 — Unified Memory v4.1.0

> 完整的 MCP 工具 API 参考手册

---

## 目录

- [L2 场景归纳工具](#l2-场景归纳工具)
- [管线调度工具](#管线调度工具)
- [存储核心工具](#存储核心工具)
- [WAL 协议工具](#wal-协议工具)
- [证据链工具](#证据链工具)
- [搜索与检索工具](#搜索与检索工具)

---

## L2 场景归纳工具

### memory_scene_induct

从记忆中归纳场景块，触发 L2 管线阶段。

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `string` | 否 | `"USER"` | 范围：USER / TEAM / AGENT / GLOBAL |
| `timeRange` | `object` | 否 | - | 时间范围 |
| `timeRange.start` | `number` | 否 | - | 开始时间戳 |
| `timeRange.end` | `number` | 否 | - | 结束时间戳 |
| `minMemories` | `number` | 否 | `3` | 最少记忆数 |
| `maxScenes` | `number` | 否 | `20` | 最大场景数 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "[{\"id\":\"scene_xxx\",\"title\":\"...\",\"summary\":\"...\",...}]"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_scene_induct '{
  "scope": "USER",
  "minMemories": 3,
  "maxScenes": 10
}'
```

---

### memory_scene_list

列出所有场景块。

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `string` | 否 | `"USER"` | 范围 |
| `limit` | `number` | 否 | `20` | 返回数量 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "[{\"id\":\"scene_xxx\",\"title\":\"...\",\"summary\":\"...\",\"tags\":[...]}]"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_scene_list '{
  "scope": "USER",
  "limit": 10
}'
```

---

### memory_scene_get

获取场景块详情。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sceneId` | `string` | 是 | 场景块 ID |
| `scope` | `string` | 否 | 范围 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"id\":\"scene_xxx\",\"title\":\"...\",\"summary\":\"...\",\"entities\":[],\"actions\":[],\"memoryIds\":[],\"timeRange\":{},\"tags\":[],\"created\":...}"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_scene_get '{
  "sceneId": "scene_xxx",
  "scope": "USER"
}'
```

---

### memory_scene_delete

删除场景块。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sceneId` | `string` | 是 | 场景块 ID |
| `scope` | `string` | 否 | 范围 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"success\":true}"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_scene_delete '{
  "sceneId": "scene_xxx",
  "scope": "USER"
}'
```

---

### memory_scene_search

搜索场景块。

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | `string` | 是 | - | 搜索关键词 |
| `scope` | `string` | 否 | `"USER"` | 范围 |
| `limit` | `number` | 否 | `10` | 返回数量 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "[{\"id\":\"scene_xxx\",\"title\":\"...\",\"summary\":\"...\"}]"
  }]
}
```

**示例**:

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

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `string` | 否 | `"USER"` | 范围 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"total\":10,\"tags\":[\"会议\",\"项目\"],\"timeRange\":{\"start\":...,\"end\":...}}"
  }]
}
```

---

## 管线调度工具

### memory_pipeline_status

获取四层管线状态。

**参数**: 无

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"enabled\":true,\"stats\":{\"l1Executions\":5,\"l2Executions\":2,\"l3Executions\":1},\"sessionCounters\":{...}}"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_pipeline_status '{}'
```

---

### memory_pipeline_trigger

手动触发管线阶段。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scope` | `string` | 否 | 范围 |
| `stage` | `string` | 否 | 管线阶段：L1 / L2 / L3 / "all" |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"triggered\":\"L2\",\"scenesGenerated\":3}"
  }]
}
```

**示例**:

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

---

### memory_pipeline_config

更新管线配置。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `config` | `object` | 是 | 新的配置对象 |

**可用配置项**:

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | `boolean` | `true` | 是否启用 |
| `everyNConversations` | `number` | `5` | 每 N 轮触发 L1 |
| `enableWarmup` | `boolean` | `true` | Warm-up 模式 |
| `l1IdleTimeoutSeconds` | `number` | `60` | L1 触发延迟 |
| `l2DelayAfterL1Seconds` | `number` | `90` | L2 触发延迟 |
| `l2MinIntervalSeconds` | `number` | `300` | L2 最小间隔 |
| `l2MaxIntervalSeconds` | `number` | `1800` | L2 最大间隔 |
| `sessionActiveWindowHours` | `number` | `24` | Session 超时 |
| `l3TriggerEveryN` | `number` | `50` | L3 触发间隔 |

**返回值**:

```json
{
  "content": [{
    "type": "text",
    "text": "{\"updated\":true,\"config\":{...}}"
  }]
}
```

**示例**:

```bash
mcporter call unified-memory memory_pipeline_config '{
  "config": {
    "everyNConversations": 3,
    "enableWarmup": true
  }
}'
```

---

## 存储核心工具

### memory_store

存储新记忆。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | `string` | 是 | 记忆内容 |
| `category` | `string` | 否 | 分类 |
| `importance` | `number` | 否 | 重要度 (0-1) |
| `tags` | `string[]` | 否 | 标签 |
| `scope` | `string` | 否 | 范围 |
| `lane` | `string` | 否 | 泳道 |

**示例**:

```bash
mcporter call unified-memory memory_store '{
  "text": "用户偏好简洁风格",
  "category": "preference",
  "importance": 0.8,
  "scope": "USER"
}'
```

---

### memory_get

获取单条记忆。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | `string` | 是 | 记忆 ID |

**示例**:

```bash
mcporter call unified-memory memory_get '{"id": "mem_xxx"}'
```

---

### memory_list

分页列出记忆。

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | `number` | 否 | `1` | 页码 |
| `pageSize` | `number` | 否 | `20` | 每页数量 |
| `scope` | `string` | 否 | - | 范围过滤 |

**示例**:

```bash
mcporter call unified-memory memory_list '{
  "page": 1,
  "pageSize": 20,
  "scope": "USER"
}'
```

---

### memory_delete

删除记忆。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | `string` | 是 | 记忆 ID |

**示例**:

```bash
mcporter call unified-memory memory_delete '{"id": "mem_xxx"}'
```

---

### memory_search

混合搜索 (BM25 + Vector + RRF)。

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | `string` | 是 | - | 搜索关键词 |
| `scope` | `string` | 否 | `"USER"` | 范围 |
| `topK` | `number` | 否 | `10` | 返回数量 |
| `category` | `string` | 否 | - | 分类过滤 |

**示例**:

```bash
mcporter call unified-memory memory_search '{
  "query": "用户偏好",
  "scope": "USER",
  "topK": 5
}'
```

---

## WAL 协议工具

### memory_wal_status

获取 WAL 状态。

**参数**: 无

**返回值**:

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

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `op` | `string` | 是 | 操作类型 |
| `collection` | `string` | 是 | 集合名 |
| `data` | `object` | 是 | 数据 |

---

### memory_wal_replay

重放 WAL 进行崩溃恢复。

**参数**: 无

---

### memory_wal_truncate

截断 WAL。

**参数**: 无

---

### memory_wal_export

导出 WAL 为 JSONL。

**参数**: 无

---

### memory_wal_import

从 JSONL 导入 WAL。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | `string` | 是 | JSONL 文件路径 |

---

## 证据链工具

### memory_evidence_add

添加证据到记忆。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `memoryId` | `string` | 是 | 记忆 ID |
| `type` | `string` | 是 | 证据类型 |
| `sourceId` | `string` | 是 | 来源 ID |
| `confidence` | `number` | 否 | 置信度 (0-1) |

---

### memory_evidence_get

获取记忆的证据链。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `memoryId` | `string` | 是 | 记忆 ID |

---

### memory_evidence_stats

获取证据统计。

**参数**: 无

---

## 搜索与检索工具

### memory_bm25

纯 BM25 关键词搜索。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | `string` | 是 | 搜索关键词 |
| `scope` | `string` | 否 | 范围 |
| `topK` | `number` | 否 | 返回数量 |

---

### memory_vector

向量相似度搜索。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | `string` | 是 | 搜索文本 |
| `scope` | `string` | 否 | 范围 |
| `topK` | `number` | 否 | 返回数量 |

---

### memory_mmr

MMR (Maximal Marginal Relevance) 重排。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `results` | `array` | 是 | 待重排结果 |
| `query` | `string` | 是 | 查询文本 |
| `lambda` | `number` | 否 | 多样性权重 (0-1) |

---

## 工具索引

| 工具名 | 类别 | 说明 |
|--------|------|------|
| `memory_scene_induct` | L2 场景归纳 🆕 | 从记忆归纳场景块 |
| `memory_scene_list` | L2 场景归纳 🆕 | 列出场景块 |
| `memory_scene_get` | L2 场景归纳 🆕 | 获取场景块详情 |
| `memory_scene_delete` | L2 场景归纳 🆕 | 删除场景块 |
| `memory_scene_search` | L2 场景归纳 🆕 | 搜索场景块 |
| `memory_scene_stats` | L2 场景归纳 🆕 | 场景统计 |
| `memory_pipeline_status` | 管线调度 🆕 | 管线状态 |
| `memory_pipeline_trigger` | 管线调度 🆕 | 触发管线 |
| `memory_pipeline_config` | 管线调度 🆕 | 管线配置 |
| `memory_store` | 存储核心 | 存储记忆 |
| `memory_get` | 存储核心 | 获取记忆 |
| `memory_list` | 存储核心 | 列出记忆 |
| `memory_delete` | 存储核心 | 删除记忆 |
| `memory_search` | 存储核心 | 混合搜索 |
| `memory_wal_status` | WAL 协议 | WAL 状态 |
| `memory_wal_write` | WAL 协议 | 写 WAL |
| `memory_wal_replay` | WAL 协议 | WAL 恢复 |
| `memory_wal_truncate` | WAL 协议 | 截断 WAL |
| `memory_wal_export` | WAL 协议 | 导出 WAL |
| `memory_wal_import` | WAL 协议 | 导入 WAL |
| `memory_evidence_add` | 证据链 | 添加证据 |
| `memory_evidence_get` | 证据链 | 获取证据链 |
| `memory_evidence_stats` | 证据链 | 证据统计 |
| `memory_bm25` | 搜索检索 | BM25 搜索 |
| `memory_vector` | 搜索检索 | 向量搜索 |
| `memory_mmr` | 搜索检索 | MMR 重排 |

---

*最后更新: 2026-04-06 | v4.1.0*
