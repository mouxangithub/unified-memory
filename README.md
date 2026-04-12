# Memory System Optimization

> 记忆系统优化项目 - Workspace Memory 与 Unified Memory 的集成优化

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![JavaScript](https://img.shields.io/badge/javascript-ES2022-orange)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

## 为什么需要这个项目

OpenClaw 的记忆系统存在两个独立的存储层：

1. **Workspace Memory** - 文件系统中的 Markdown 文件，持久化但检索效率低
2. **Unified Memory** - 向量数据库，高效检索但需要手动同步

这两个系统长期独立运行，导致：
- 记忆重复存储浪费空间
- 检索结果不一致
- 维护成本高

**本项目解决的核心问题**：建立 Workspace Memory 与 Unified Memory 之间的智能同步机制，实现"一次写入，统一检索"。

## 核心功能

| 模块 | 功能 | 适用场景 |
|------|------|----------|
| **SyncBridge** | 单向同步 Workspace Memory → Unified Memory | 每日定时同步 |
| **UnifiedQueryAPI** | 统一检索接口（优先向量，文件系统兜底） | 实时查询 |
| **CrossSystemDeduplicator** | 跨系统去重检查 | 存储前验证 |
| **MemoryHealthMonitor** | 健康监控与性能基准 | 运维监控 |

## 快速开始

### 前置条件

- Node.js 18+
- 已安装 Unified Memory 技能（位于 `/root/.openclaw/skills/unified-memory`）

### 安装

```bash
cd /root/.openclaw/workspace/memory-optimization
npm install
```

### 首次同步

```bash
# 干运行模式（不实际写入）
npm run sync:dry-run

# 正式同步
npm run sync:manual
```

### 查询记忆

```bash
# 基本查询
npm run query -- "搜索关键词"

# 启动查询服务器（可选）
npm run query -- --server 3851
```

### 设置定时同步

```bash
# 生成 crontab 配置
npm run crontab

# 输出示例：
# 0 2 * * * cd /root/.openclaw/workspace/memory-optimization && node sync/sync_cron.js --scheduled >> logs/cron.log 2>&1
```

### 健康监控

```bash
# 单次检查
npm run monitor

# 仪表板视图
npm run monitor:dashboard
```

## 项目结构

```
memory-optimization/
├── sync/                          # 同步模块
│   ├── sync_bridge.js             # 同步桥梁（核心）
│   ├── sync_cron.js               # 定时调度
│   └── sync_state.json            # 同步状态持久化
├── dedup/                         # 去重模块
│   └── cross_system_dedup.js      # 跨系统去重
├── api/                           # API模块
│   └── unified_query_api.js       # 统一检索API
├── monitor/                       # 监控模块
│   └── health_check.js            # 健康检查
├── scripts/                       # 脚本
│   ├── deploy.js                  # 部署脚本
│   └── test.js                    # 测试脚本
├── logs/                          # 日志目录
│   └── reports/                   # 健康报告
├── config.json                    # 配置文件
├── index.js                       # 主入口
└── package.json                   # 项目配置
```

## 配置说明

编辑 `config.json` 自定义行为：

```json
{
  "workspacePath": "/root/.openclaw/workspace/memory",
  "unifiedMemoryPath": "/root/.openclaw/skills/unified-memory",
  "sync": {
    "enabled": true,
    "schedule": "0 2 * * *",
    "batchSize": 50,
    "dryRun": false
  },
  "dedup": {
    "similarityThreshold": 0.85,
    "exactMatchThreshold": 0.95,
    "cacheSize": 1000
  },
  "monitor": {
    "healthCheckInterval": 3600,
    "alertThreshold": 3
  },
  "api": {
    "port": 3851,
    "cacheSize": 100,
    "enableStats": true
  }
}
```

### 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `sync.schedule` | `0 2 * * *` | Cron 表达式，每天凌晨 2 点执行 |
| `sync.batchSize` | `50` | 每批处理的记忆数量 |
| `dedup.similarityThreshold` | `0.85` | 语义相似度阈值，超过则视为重复 |
| `dedup.exactMatchThreshold` | `0.95` | 精确匹配阈值 |
| `api.cacheSize` | `100` | 查询结果缓存大小 |

## 模块详解

### SyncBridge - 同步桥梁

将 Workspace Memory 中的 Markdown 文件解析并同步到 Unified Memory。

**工作流程**：
1. 扫描 Workspace Memory 目录中的 `.md` 文件
2. 按修改时间过滤出需要同步的文件
3. 解析 Markdown 内容，提取记忆段落
4. 对每个记忆执行去重检查
5. 存储到 Unified Memory 向量数据库

**支持的记忆类型**：
- `facts` - 事实型（成绩、数据、金额）
- `patterns` - 模式型（规律、趋势、周期）
- `skills` - 技能型（方法、技巧、步骤）
- `cases` - 案例型（示例、故事、经历）
- `events` - 事件型（会议、活动、记录）
- `preferences` - 偏好型（喜欢、习惯、偏好）

### UnifiedQueryAPI - 统一检索

提供统一的记忆查询接口。

**查询优先级**：
1. **优先**：Unified Memory 向量检索 + BM25
2. **兜底**：文件系统全文搜索
3. **后处理**：结果合并、去重、排序

**结果缓存**：最近 100 次查询结果自动缓存

### CrossSystemDeduplicator - 跨系统去重

在存储前检查记忆是否重复，支持：

- **Unified Memory 内部去重**：检查已有向量存储
- **跨系统去重**：检查 Workspace 文件系统
- **语义相似度计算**：基于关键词重叠和长度比

### MemoryHealthMonitor - 健康监控

定期检查各组件健康状态：

- Workspace Memory 文件完整性
- Unified Memory 服务状态
- 同步延迟监控
- 检索性能基准

## 监控指标

| 指标 | 说明 | 健康阈值 |
|------|------|----------|
| `syncDelayHours` | 距离上次同步的小时数 | < 24h |
| `totalMemoriesSynced` | 累计同步记忆数 | 持续增长 |
| `duplicateRate` | 重复检测率 | < 15% |
| `avgQueryTime` | 平均查询响应时间 | < 500ms |
| `cacheHitRate` | 缓存命中率 | > 60% |

## 故障排除

### 同步失败

```bash
# 1. 检查目录权限
ls -la /root/.openclaw/workspace/memory
ls -la /root/.openclaw/skills/unified-memory

# 2. 检查 Unified Memory 服务
cd /root/.openclaw/skills/unified-memory
node -e "console.log('OK')"

# 3. 查看同步日志
cat logs/sync_*.jsonl | tail -50
```

### 查询性能慢

```bash
# 1. 检查缓存命中率
npm run query -- --stats

# 2. 查看 Unified Memory 状态
npm run monitor

# 3. 清理缓存
npm run query -- --clear-cache
```

### 去重效果差

```bash
# 1. 调整相似度阈值
# 编辑 config.json
"similarityThreshold": 0.80

# 2. 查看去重统计
node dedup/cross_system_dedup.js --stats

# 3. 清理去重缓存
node dedup/cross_system_dedup.js --clear-cache
```

## 后续开发计划

| 阶段 | 功能 | 状态 |
|------|------|------|
| v1.1 | 双向同步（Unified Memory → Workspace） | 待开发 |
| v1.2 | 智能压缩（自动归档旧记忆） | 待开发 |
| v1.3 | 实时索引（对话时实时同步） | 待开发 |
| v2.0 | 记忆网格（跨会话记忆共享） | 规划中 |

## 贡献指南

See [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License - see [LICENSE](LICENSE) 文件
