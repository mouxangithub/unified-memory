# memory-system-optimization

> Workspace Memory 与 Unified Memory 的集成优化

## 功能

将 Workspace Memory（Markdown 文件）智能同步到 Unified Memory（向量存储），实现统一检索。

### 核心能力

- **智能同步**：自动扫描、同步、去重
- **统一检索**：向量优先，文件系统兜底
- **健康监控**：实时监控同步状态和性能
- **跨系统去重**：避免重复存储浪费空间

## 使用方法

### 同步记忆

```bash
# 首次同步（干运行）
npm run sync:dry-run

# 正式同步
npm run sync:manual

# 设置定时任务
npm run crontab
```

### 查询记忆

```bash
# 查询
npm run query -- "关键词"

# 查看统计
node api/unified_query_api.js --stats
```

### 健康检查

```bash
# 仪表板
npm run monitor:dashboard

# 单次检查
npm run monitor
```

## 配置

编辑 `config.json`：

```json
{
  "workspacePath": "/root/.openclaw/workspace/memory",
  "unifiedMemoryPath": "/root/.openclaw/skills/unified-memory",
  "sync": {
    "schedule": "0 2 * * *",
    "batchSize": 50
  },
  "dedup": {
    "similarityThreshold": 0.85
  }
}
```

## 模块

| 模块 | 说明 |
|------|------|
| `sync/sync_bridge.js` | 同步桥梁 |
| `sync/sync_cron.js` | 定时调度 |
| `api/unified_query_api.js` | 统一检索 |
| `dedup/cross_system_dedup.js` | 跨系统去重 |
| `monitor/health_check.js` | 健康监控 |

## 依赖

- Node.js 18+
- Unified Memory 技能（`/root/.openclaw/skills/unified-memory`）

## CLI 命令

| 命令 | 说明 |
|------|------|
| `npm run sync:manual` | 执行同步 |
| `npm run sync:dry-run` | 干运行 |
| `npm run query -- "..."` | 查询 |
| `npm run monitor:dashboard` | 监控仪表板 |
| `npm run crontab` | 生成 crontab |
