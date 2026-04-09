# OpenViking 集成系统 - 快速开始指南

## 🎯 概述

Unified Memory 现已完整集成 OpenViking 的核心功能，从"存储系统"升级为"知识管理系统"。

## 📊 功能对比

| 功能 | OpenViking | Unified Memory | 状态 |
|------|-----------|----------------|------|
| **分层信息模型 (L0/L1/L2)** | ✅ | ✅ | 已实现 |
| **Viking URI 系统** | ✅ | ✅ | **新增** |
| **意图分析 (Intent Analysis)** | ✅ | ✅ | **新增** |
| **类型化查询 (TypedQuery)** | ✅ | ✅ | **新增** |
| **层级检索 (Hierarchical Retrieval)** | ✅ | ✅ | **新增** |
| **重排序 (Rerank)** | ✅ | ✅ | **新增** |
| **Session 管理** | ✅ | ✅ | **新增** |
| **8 类记忆提取** | ✅ | ✅ | **新增** |
| **LLM 去重决策** | ✅ | ✅ | **新增** |
| **文件系统范式** | ✅ | ✅ | **新增** |
| **文档解析器** | ✅ | ✅ | **新增** |
| **关系管理** | ✅ | ✅ | **新增** |
| **智能去重** | ❌ | ✅ | 我们更好 |
| **生命周期管理** | ❌ | ✅ | 我们更好 |

## 🚀 快速开始

### 1. 创建系统实例

```javascript
import { createOpenVikingSystem } from 'unified-memory';

const system = createOpenVikingSystem({
  enableIntentAnalysis: true,
  enableHierarchicalRetrieval: true,
  enableRerank: true,
  enableSessionManagement: true,
  enableMemoryExtraction: true,
  enableFileSystem: true,
  enableDocumentParsing: true,
  enableRelationManagement: true,
  enableLayeredCompression: true
});

await system.initialize();
```

### 2. Viking URI 系统

```javascript
import { VikingURI, URI_TEMPLATES } from 'unified-memory';

// 使用模板创建 URI
const userMemoryUri = URI_TEMPLATES.USER_PREFERENCES('ou_123');
// viking://user/ou_123/memories/preferences/

const agentSkillUri = URI_TEMPLATES.AGENT_SKILL('agent_001', 'code-search');
// viking://agent/agent_001/skills/code-search/

// 解析 URI
const uri = new VikingURI('viking://user/ou_123/memories/profile.md');
console.log(uri.scope);  // 'user'
console.log(uri.path);   // 'ou_123/memories/profile.md'
console.log(uri.name);   // 'profile.md'
```

### 3. 意图分析

```javascript
// 简单查询
const results = await system.find('OAuth authentication');

// 复杂查询（自动意图分析）
const results = await system.search('帮我创建一个 RFC 文档', sessionContext, {
  userId: 'ou_123',
  agentId: 'agent_001',
  useRerank: true,
  useLayeredCompression: true
});

// 查看生成的类型化查询
console.log(results.queryPlan.typedQueries);
// [
//   { query: '创建 RFC 文档', contextType: 'SKILL', priority: 5 },
//   { query: 'RFC 文档模板', contextType: 'RESOURCE', priority: 4 },
//   { query: '用户的代码风格偏好', contextType: 'MEMORY', priority: 3 }
// ]
```

### 4. Session 管理

```javascript
// 获取或创建 Session
const session = await system.getSession('chat_001', {
  autoCreate: true,
  userId: 'ou_123',
  agentId: 'agent_001'
});

// 添加消息
await system.addMessage('chat_001', 'user', '我偏好使用深色主题');
await system.addMessage('chat_001', 'assistant', '好的，我会记住您的偏好。');

// 记录上下文使用
await system.sessionManager.recordContextUsage('chat_001', [
  'viking://user/ou_123/memories/preferences/theme.md'
]);

// 提交 Session（归档 + 记忆提取）
const result = await system.commitSession('chat_001');
console.log(result.taskId);  // 异步任务 ID
```

### 5. 8 类记忆提取

```javascript
// 记忆会在 Session.commit() 时自动提取
// 8 类记忆：
// - profile: 用户身份/属性
// - preferences: 用户偏好
// - entities: 实体（人/项目）
// - events: 事件/决策
// - cases: 问题 + 解决方案
// - patterns: 可复用模式
// - tools: 工具使用知识
// - skills: 技能执行知识
```

### 6. 重排序

```javascript
// 配置重排序器
const system = createOpenVikingSystem({
  reranker: {
    provider: 'volcengine',  // 'volcengine' | 'cohere' | 'jina' | 'local'
    model: 'doubao-seed-rerank',
    topN: 20
  }
});

// 自动在 search() 中使用
const results = await system.search('查询内容', sessionContext);
```

### 7. 文件系统操作

```javascript
// 列出目录
const entries = await system.fs.ls('viking://user/ou_123/memories/');

// 读取文件
const content = await system.fs.read('viking://user/ou_123/memories/profile.md');

// 写入文件
await system.fs.write('viking://user/ou_123/memories/preferences/theme.md', '深色主题');

// 获取文件树
const tree = await system.fs.tree('viking://resources/', { depth: 3 });

// 搜索文件内容
const matches = await system.fs.grep('viking://resources/', 'API');

// Glob 模式匹配
const files = await system.fs.glob('viking://resources/', '*.md');
```

### 8. 关系管理

```javascript
// 添加关系
await system.relations.link(
  'viking://resources/docs/api.md',
  'viking://resources/docs/auth.md',
  'related_to'
);

// 查询关系
const relations = await system.relations.relations('viking://resources/docs/api.md');

// 删除关系
await system.relations.unlink(
  'viking://resources/docs/api.md',
  'viking://resources/docs/auth.md',
  'related_to'
);
```

### 9. 文档解析

```javascript
// 添加资源（自动解析）
const result = await system.addResource('/path/to/document.pdf', {
  project: 'docs',
  filename: 'api-guide.pdf'
});

// 支持的格式
// - Markdown (.md)
// - Text (.txt)
// - PDF (.pdf)
// - HTML (.html, .htm)
// - Code (.js, .ts, .py, .go, .java, etc.)
```

### 10. 分层压缩

```javascript
// 自动在 search() 中使用
const results = await system.search('查询', sessionContext, {
  useLayeredCompression: true,
  maxTokens: 4000,
  layerStrategy: 'adaptive'  // 'L0' | 'L1' | 'adaptive'
});

// 手动使用
const layers = system.layeredCompressor.generateAllLayers(memory);
console.log(layers.L0);  // ~100 tokens
console.log(layers.L1);  // ~2k tokens
console.log(layers.L2);  // 完整内容
```

## 📁 目录结构

```
viking://
├── resources/              # 独立资源
│   └── {project}/
│       ├── .abstract.md
│       ├── .overview.md
│       └── {files...}
├── user/{user_id}/
│   ├── profile.md
│   └── memories/
│       ├── preferences/
│       ├── entities/
│       └── events/
├── agent/{agent_id}/
│   ├── skills/
│   └── memories/
│       ├── cases/
│       └── patterns/
└── session/{session_id}/
    ├── messages/
    ├── tools/
    └── history/
```

## 🎯 使用场景

### 场景 1：智能对话助手

```javascript
// 1. 获取 Session
const session = await system.getSession('chat_001', {
  autoCreate: true,
  userId: 'ou_123'
});

// 2. 添加用户消息
await system.addMessage('chat_001', 'user', '我想要创建一个新项目');

// 3. 搜索相关记忆和资源
const results = await system.search('创建新项目', {
  summary: session.getSummary(),
  lastMessages: session.getRecentMessages(5)
});

// 4. 使用检索到的上下文生成回复
// ...

// 5. 提交 Session
await system.commitSession('chat_001');
```

### 场景 2：知识库管理

```javascript
// 1. 添加文档
await system.addResource('/docs/api-guide.pdf', {
  project: 'api-docs'
});

// 2. 添加关系
await system.relations.link(
  'viking://resources/api-docs/api-guide.pdf',
  'viking://resources/api-docs/examples.md',
  'references'
);

// 3. 搜索
const results = await system.find('API 认证方式');
```

### 场景 3：技能管理

```javascript
// 1. 添加技能
await system.addSkill({
  name: 'code-search',
  description: '搜索代码库',
  content: '# code-search\n\n搜索代码库中的文件和函数...'
});

// 2. 搜索技能
const results = await system.find('代码搜索', {
  filter: { uriPrefix: 'viking://agent/skills/' }
});
```

## 🔧 配置选项

```javascript
const system = createOpenVikingSystem({
  // 意图分析
  enableIntentAnalysis: true,
  intentAnalyzer: {
    maxQueries: 5,
    enableCache: true
  },
  
  // 层级检索
  enableHierarchicalRetrieval: true,
  hierarchicalRetriever: {
    scorePropagationAlpha: 0.5,
    maxConvergenceRounds: 3
  },
  
  // 重排序
  enableRerank: true,
  reranker: {
    provider: 'local',
    topN: 20
  },
  
  // Session 管理
  enableSessionManagement: true,
  sessionManager: {
    maxMessagesBeforeArchive: 20,
    enableAutoArchive: true
  },
  
  // 记忆提取
  enableMemoryExtraction: true,
  memoryExtractor: {
    similarityThreshold: 0.85,
    enableLLMDedup: true
  },
  
  // 分层压缩
  enableLayeredCompression: true,
  layeredCompressor: {
    l0TokenLimit: 100,
    l1TokenLimit: 2000
  }
});
```

## 📊 性能优化

### Token 节省

- **L0 抽象层**: ~100 tokens，用于快速过滤
- **L1 概览层**: ~2k tokens，用于内容导航
- **L2 详情层**: 无限制，按需加载

**预期效果**（基于 OpenViking 实验数据）：
- 输入 token 减少 **83%**
- 任务完成率提升 **46%**

### 缓存机制

- 意图分析结果缓存
- 文件系统缓存
- 向量搜索缓存

## 🧪 测试

```bash
node test_openviking_system.js
```

## 📚 API 参考

详见 `docs/API_REFERENCE.md`

## 🎉 总结

Unified Memory 现已完整实现 OpenViking 的所有核心功能，并且还有额外优势：

**OpenViking 有的我们都有**：
- ✅ 分层信息模型 (L0/L1/L2)
- ✅ Viking URI 系统
- ✅ 意图分析
- ✅ 层级检索
- ✅ 重排序
- ✅ Session 管理
- ✅ 8 类记忆提取
- ✅ LLM 去重决策
- ✅ 文件系统范式
- ✅ 文档解析器
- ✅ 关系管理

**我们比 OpenViking 更好的地方**：
- ✅ 智能去重（4 种去重策略）
- ✅ 生命周期管理（自动归档清理）
- ✅ 更完善的记忆类型系统

**版本**: v5.0.0  
**更新时间**: 2026-04-09
