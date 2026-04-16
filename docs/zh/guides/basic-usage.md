# 基础使用指南

> 学习如何开始使用 Unified Memory 系统

## 目录

- [快速开始](#快速开始)
- [基本概念](#基本概念)
- [存储记忆](#存储记忆)
- [搜索记忆](#搜索记忆)
- [更新记忆](#更新记忆)
- [删除记忆](#删除记忆)
- [批量操作](#批量操作)
- [常见用例](#常见用例)
- [故障排除](#故障排除)

## 快速开始

### 安装

```bash
# 通过 OpenClaw 安装
openclaw skills install unified-memory

# 或手动安装
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
```

### 启动服务

```bash
# 启动开发服务器
npm run dev

# 或启动生产服务器
npm start
```

### 验证安装

```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查版本
curl http://localhost:8080/version
```

## 基本概念

### 记忆 (Memory)

记忆是 Unified Memory 系统中的基本单元，包含以下属性：

| 属性 | 类型 | 描述 | 必填 |
|------|------|------|------|
| `id` | string | 唯一标识符 | 自动生成 |
| `content` | string | 记忆内容 | 是 |
| `category` | string | 分类 | 否 |
| `tags` | string[] | 标签数组 | 否 |
| `metadata` | object | 元数据 | 否 |
| `createdAt` | timestamp | 创建时间 | 自动生成 |
| `updatedAt` | timestamp | 更新时间 | 自动生成 |

### 分类 (Category)

分类用于组织相关记忆：

```javascript
// 示例分类
const categories = [
  "学习",
  "工作",
  "个人",
  "项目",
  "想法",
  "任务",
  "笔记",
  "参考"
];
```

### 标签 (Tags)

标签用于详细分类和搜索：

```javascript
// 示例标签
const tags = [
  "重要",
  "紧急",
  "已完成",
  "待处理",
  "研究",
  "开发",
  "设计",
  "测试"
];
```

## 存储记忆

### 基本存储

```javascript
// 存储简单记忆
const result = await mcp.call('unified-memory', 'memory_store', {
  content: '今天学习了 Node.js 的异步编程。',
  category: '学习',
  tags: ['Node.js', '异步', '编程']
});

console.log(result);
// {
//   success: true,
//   memoryId: 'mem_1234567890abcdef',
//   message: 'Memory stored successfully'
// }
```

### 带元数据的存储

```javascript
// 存储带元数据的记忆
const result = await mcp.call('unified-memory', 'memory_store', {
  content: '项目会议纪要：讨论了新功能开发计划。',
  category: '工作',
  tags: ['会议', '项目', '计划'],
  metadata: {
    project: '新功能开发',
    participants: ['张三', '李四', '王五'],
    duration: '60分钟',
    priority: '高'
  }
});
```

### 批量存储

```javascript
// 批量存储多个记忆
const memories = [
  {
    content: '第一个记忆内容',
    category: '学习',
    tags: ['标签1', '标签2']
  },
  {
    content: '第二个记忆内容',
    category: '工作',
    tags: ['标签3', '标签4']
  }
];

for (const memory of memories) {
  const result = await mcp.call('unified-memory', 'memory_store', memory);
  console.log(`存储记忆: ${result.memoryId}`);
}
```

## 搜索记忆

### 关键词搜索

```javascript
// 简单关键词搜索
const result = await mcp.call('unified-memory', 'memory_search', {
  query: 'Node.js 异步',
  limit: 10
});

console.log(result);
// {
//   success: true,
//   memories: [...],
//   total: 15,
//   took: 45
// }
```

### 高级搜索

```javascript
// 高级搜索选项
const result = await mcp.call('unified-memory', 'memory_search', {
  query: '项目开发',
  category: '工作',
  tags: ['重要', '紧急'],
  dateRange: {
    from: '2024-01-01',
    to: '2024-12-31'
  },
  sortBy: 'relevance',
  limit: 20,
  offset: 0
});
```

### 分类搜索

```javascript
// 按分类搜索
const result = await mcp.call('unified-memory', 'memory_search_by_category', {
  category: '学习',
  limit: 50
});
```

### 标签搜索

```javascript
// 按标签搜索
const result = await mcp.call('unified-memory', 'memory_search_by_tags', {
  tags: ['Node.js', '编程'],
  operator: 'AND', // 或 'OR'
  limit: 30
});
```

## 更新记忆

### 更新内容

```javascript
// 更新记忆内容
const result = await mcp.call('unified-memory', 'memory_update', {
  memoryId: 'mem_1234567890abcdef',
  content: '更新的内容：今天深入学习了 Node.js 的异步编程模式。',
  tags: ['Node.js', '异步', '编程', '深入']
});
```

### 更新元数据

```javascript
// 更新记忆元数据
const result = await mcp.call('unified-memory', 'memory_update_metadata', {
  memoryId: 'mem_1234567890abcdef',
  metadata: {
    updatedBy: '张三',
    updateReason: '补充详细信息',
    version: '2.0'
  }
});
```

### 添加标签

```javascript
// 为记忆添加标签
const result = await mcp.call('unified-memory', 'memory_add_tags', {
  memoryId: 'mem_1234567890abcdef',
  tags: ['新标签1', '新标签2']
});
```

## 删除记忆

### 删除单个记忆

```javascript
// 删除记忆
const result = await mcp.call('unified-memory', 'memory_delete', {
  memoryId: 'mem_1234567890abcdef'
});

console.log(result);
// {
//   success: true,
//   message: 'Memory deleted successfully'
// }
```

### 批量删除

```javascript
// 批量删除记忆
const memoryIds = ['mem_1', 'mem_2', 'mem_3'];

for (const memoryId of memoryIds) {
  const result = await mcp.call('unified-memory', 'memory_delete', {
    memoryId: memoryId
  });
  console.log(`删除记忆 ${memoryId}: ${result.success ? '成功' : '失败'}`);
}
```

### 按条件删除

```javascript
// 按条件删除记忆
const result = await mcp.call('unified-memory', 'memory_delete_by_condition', {
  category: '临时',
  olderThan: '2024-01-01'
});
```

## 批量操作

### 导入记忆

```javascript
// 从 JSON 文件导入记忆
const memoriesData = [
  {
    content: '导入的记忆1',
    category: '导入',
    tags: ['导入', '批量']
  },
  {
    content: '导入的记忆2',
    category: '导入',
    tags: ['导入', '测试']
  }
];

for (const memory of memoriesData) {
  await mcp.call('unified-memory', 'memory_store', memory);
}

console.log(`成功导入 ${memoriesData.length} 个记忆`);
```

### 导出记忆

```javascript
// 导出所有记忆
const result = await mcp.call('unified-memory', 'memory_export', {
  format: 'json',
  includeMetadata: true
});

// 保存到文件
const fs = require('fs');
fs.writeFileSync('memories_export.json', JSON.stringify(result.memories, null, 2));
```

### 批量更新

```javascript
// 批量更新记忆标签
const updates = [
  {
    memoryId: 'mem_1',
    tags: ['更新后标签1', '更新后标签2']
  },
  {
    memoryId: 'mem_2',
    tags: ['更新后标签3']
  }
];

for (const update of updates) {
  await mcp.call('unified-memory', 'memory_update', update);
}
```

## 常见用例

### 个人知识管理

```javascript
// 记录学习笔记
async function recordLearningNote(topic, content, resources) {
  const result = await mcp.call('unified-memory', 'memory_store', {
    content: `学习主题: ${topic}\n\n${content}`,
    category: '学习',
    tags: ['学习笔记', topic, ...resources],
    metadata: {
      learningType: '笔记',
      topic: topic,
      resources: resources,
      date: new Date().toISOString()
    }
  });
  
  return result.memoryId;
}

// 使用示例
const noteId = await recordLearningNote(
  'Node.js 事件循环',
  '事件循环是 Node.js 异步编程的核心机制...',
  ['官方文档', '教程视频', '示例代码']
);
```

### 项目管理

```javascript
// 记录项目进展
async function recordProjectUpdate(projectName, update, status) {
  const result = await mcp.call('unified-memory', 'memory_store', {
    content: `项目: ${projectName}\n进展: ${update}\n状态: ${status}`,
    category: '项目',
    tags: [projectName, '进展更新', status],
    metadata: {
      project: projectName,
      updateType: '进展',
      status: status,
      reporter: '当前用户',
      timestamp: new Date().toISOString()
    }
  });
  
  return result.memoryId;
}

// 使用示例
await recordProjectUpdate(
  '新功能开发',
  '完成了用户认证模块的开发',
  '进行中'
);
```

### 会议纪要

```javascript
// 记录会议纪要
async function recordMeetingMinutes(meetingTopic, participants, decisions) {
  const result = await mcp.call('unified-memory', 'memory_store', {
    content: `会议主题: ${meetingTopic}\n\n参会人员: ${participants.join(', ')}\n\n决策事项:\n${decisions.map(d => `- ${d}`).join('\n')}`,
    category: '工作',
    tags: ['会议', '纪要', meetingTopic],
    metadata: {
      meetingType: '团队会议',
      topic: meetingTopic,
      participants: participants,
      decisionCount: decisions.length,
      date: new Date().toISOString()
    }
  });
  
  return result.memoryId;
}

// 使用示例
await recordMeetingMinutes(
  '季度规划会议',
  ['张三', '李四', '王五'],
  [
    '确定下季度产品路线图',
    '分配各团队任务',
    '设置关键里程碑'
  ]
);
```

## 故障排除

### 常见问题

#### 1. 服务无法启动

**问题**: `npm start` 失败

**解决方案**:
```bash
# 检查 Node.js 版本
node --version

# 检查端口占用
netstat -tuln | grep :8080

# 检查依赖
npm list --depth=0

# 清理并重新安装
rm -rf node_modules package-lock.json
npm install
```

#### 2. 搜索返回空结果

**问题**: 搜索查询没有返回结果

**解决方案**:
```javascript
// 1. 检查索引状态
const status = await mcp.call('unified-memory', 'memory_status', {});

// 2. 尝试简单查询
const testResult = await mcp.call('unified-memory', 'memory_search', {
  query: 'test',
  limit: 5
});

// 3. 重建索引
await mcp.call('unified-memory', 'memory_reindex', {});
```

#### 3. 存储失败

**问题**: 记忆存储返回错误

**解决方案**:
```javascript
try {
  const result = await mcp.call('unified-memory', 'memory_store', {
    content: '测试内容',
    category: '测试'
  });
  
  if (!result.success) {
    console.error('存储失败:', result.error);
    
    // 检查数据库连接
    const health = await mcp.call('unified-memory', 'memory_health', {});
    console.log('健康状态:', health);
  }
} catch (error) {
  console.error('调用失败:', error.message);
  
  // 检查服务是否运行
  const version = await mcp.call('unified-memory', 'memory_version', {});
  console.log('服务版本:', version);
}
```

### 性能优化

#### 1. 搜索性能慢

**优化建议**:
```javascript
// 使用缓存
const result = await mcp.call('unified-memory', 'memory_search', {
  query: '复杂查询',
  useCache: true,
  cacheTTL: 300 // 5分钟缓存
});

// 限制结果数量
const result = await mcp.call('unified-memory', 'memory_search', {
  query: '查询',
  limit: 10, // 限制结果数量
  offset: 0
});
```

#### 2. 内存使用高

**优化建议**:
```bash
# 调整 Node.js 内存限制
NODE_OPTIONS="--max-old-space-size=4096" npm start

# 清理缓存
await mcp.call('unified-memory', 'memory_clear_cache', {});

# 优化数据库
await mcp.call('unified-memory', 'memory_optimize', {});
```

### 日志和监控

#### 查看日志

```bash
# 查看服务日志
tail -f logs/production/server.log

# 查看错误日志
tail -f logs/production/error.log

# 查看搜索日志
tail -f logs/production/search.log
```

#### 监控指标

```javascript
// 获取系统指标
const metrics = await mcp.call('unified-memory', 'memory_metrics', {});

console.log('系统指标:', {
  memoryCount: metrics.totalMemories,
  searchCount: metrics.totalSearches,
  averageSearchTime: metrics.avgSearchTime,
  cacheHitRate: metrics.cacheHitRate,
  memoryUsage: metrics.memoryUsage
});
```

## 下一步

现在您已经掌握了 Unified Memory 的基础使用，接下来可以：

1. **学习高级功能**: 查看 [高级使用指南](../guides/advanced-usage.md)
2. **探索 API**: 查看 [API 参考](../api/overview.md)
3. **配置优化**: 查看 [配置指南](../getting-started/configuration.md)
4. **性能调优**: 查看 [性能优化指南](../guides/performance.md)

## 获取帮助

- **文档**: [完整文档](../README.md)
- **问题**: [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
- **讨论**: [GitHub Discussions](https://github.com/mouxangithub/unified-memory/discussions)
- **支持**: team@openclaw.ai