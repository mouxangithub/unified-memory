# API 文档

## 模块 API

### SyncBridge

同步 Workspace Memory 到 Unified Memory。

```javascript
import SyncBridge from './sync/sync_bridge.js';

const bridge = new SyncBridge({
  workspacePath: '/root/.openclaw/workspace/memory',
  unifiedMemoryPath: '/root/.openclaw/skills/unified-memory',
  batchSize: 50,
  dryRun: false
});

// 执行同步
const result = await bridge.sync();
```

#### 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `workspacePath` | `string` | `.../workspace/memory` | Workspace Memory 路径 |
| `unifiedMemoryPath` | `string` | `.../skills/unified-memory` | Unified Memory 路径 |
| `batchSize` | `number` | `50` | 每批处理记忆数 |
| `dryRun` | `boolean` | `false` | 干运行模式 |

#### 返回值

```javascript
{
  lastSyncTime: "2026-04-12T02:00:00.000Z",
  lastSyncMtime: {
    "2026-03-30.md": 1714569600000
  },
  totalFilesProcessed: 10,
  totalMemoriesSynced: 156,
  errors: []
}
```

---

### UnifiedQueryAPI

统一检索接口。

```javascript
import UnifiedQueryAPI from './api/unified_query_api.js';

const api = new UnifiedQueryAPI({
  workspacePath: '/root/.openclaw/workspace/memory',
  unifiedMemoryPath: '/root/.openclaw/skills/unified-memory',
  cacheSize: 100
});

// 查询
const result = await api.query("记忆优化", {
  limit: 10,
  sortBy: 'score',
  order: 'desc'
});
```

#### query(options)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | `string` | 必填 | 搜索关键词 |
| `limit` | `number` | `10` | 返回结果数量 |
| `sortBy` | `string` | `'score'` | 排序字段：`score` / `timestamp` |
| `order` | `string` | `'desc'` | 排序方向：`desc` / `asc` |
| `requireFallback` | `boolean` | `false` | 是否强制搜索文件系统 |
| `filters` | `object` | `{}` | 过滤条件 |

#### 返回值

```javascript
{
  success: true,
  query: "记忆优化",
  results: [
    {
      content: "记忆系统优化项目...",
      source: "unified",
      score: 0.95,
      metadata: {
        type: "events",
        timestamp: "2026-04-12T00:00:00.000Z"
      }
    }
  ],
  stats: {
    total: 5,
    unifiedHit: true,
    unifiedResults: 4,
    filesystemResults: 1,
    responseTime: 45
  }
}
```

#### getStats()

获取查询统计。

```javascript
api.getStats();
// {
//   queries: { total: 100, unifiedHits: 85, fallbackRate: "15.00%" },
//   performance: { avgResponseTime: "32.50ms", cacheSize: 100 }
// }
```

---

### CrossSystemDeduplicator

跨系统去重。

```javascript
import CrossSystemDeduplicator from './dedup/cross_system_dedup.js';

const dedup = new CrossSystemDeduplicator({
  similarityThreshold: 0.85,
  exactMatchThreshold: 0.95,
  cacheSize: 1000
});

// 检查重复
const result = await dedup.checkDuplicate({
  content: "记忆系统需要优化",
  source: "workspace:2026-04-12.md",
  type: "events"
}, {
  sources: ['unified_memory', 'workspace_filesystem'],
  crossSystemDedup: true
});
```

#### checkDuplicate(memory, options)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `memory.content` | `string` | 必填 | 记忆内容 |
| `memory.source` | `string` | 必填 | 来源标识 |
| `memory.type` | `string` | `'events'` | 记忆类型 |
| `options.sources` | `string[]` | `['unified_memory', 'workspace_filesystem']` | 检查来源 |
| `options.crossSystemDedup` | `boolean` | `true` | 是否跨系统检查 |
| `options.similarityThreshold` | `number` | `0.85` | 相似度阈值 |

#### 返回值

```javascript
{
  isDuplicate: false,
  duplicateOf: null,
  similarity: 0.45,
  sourcesChecked: ['unified_memory', 'workspace_filesystem'],
  details: [],
  fingerprint: "abc123",
  responseTime: 23
}
```

#### batchCheckDuplicates(memories, options)

批量检查重复。

```javascript
const results = await dedup.batchCheckDuplicates(memories, {
  batchSize: 10,
  progressCallback: (done, total) => {
    console.log(`进度: ${done}/${total}`);
  }
});
```

---

### MemoryHealthMonitor

健康监控。

```javascript
import MemoryHealthMonitor from './monitor/health_check.js';

const monitor = new MemoryHealthMonitor({
  workspacePath: '/root/.openclaw/workspace/memory',
  unifiedMemoryPath: '/root/.openclaw/skills/unified-memory'
});

// 执行健康检查
const result = await monitor.checkHealth();
```

#### checkHealth()

返回完整的健康检查报告。

```javascript
{
  success: true,
  timestamp: "2026-04-12T10:00:00.000Z",
  overallStatus: "healthy", // healthy | degraded | unhealthy | failed
  checks: {
    workspaceMemory: {
      healthy: true,
      metrics: {
        totalFiles: 45,
        mdFiles: 38,
        estimatedTotalSizeMB: "2.45"
      },
      issues: []
    },
    unifiedMemory: {
      healthy: true,
      metrics: {
        version: "1.0.0",
        totalMemories: 1250
      },
      issues: []
    },
    syncStatus: {
      healthy: true,
      metrics: {
        lastSyncTime: "2026-04-12T02:00:00.000Z",
        syncDelayHours: "8.0"
      },
      issues: []
    },
    searchPerformance: {
      healthy: true,
      metrics: {
        avgQueryTimeMs: "32.5"
      },
      issues: []
    }
  },
  recommendations: [],
  stats: { ... }
}
```

#### getHistoricalReports(limit)

获取历史健康报告。

```javascript
const reports = await monitor.getHistoricalReports(10);
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `npm run sync:manual` | 执行一次同步 |
| `npm run sync:dry-run` | 干运行同步 |
| `npm run query -- "关键词"` | 执行查询 |
| `npm run dedup` | 运行去重检查 |
| `npm run monitor` | 健康检查 |
| `npm run monitor:dashboard` | 健康仪表板 |
| `npm run crontab` | 生成 crontab 配置 |
