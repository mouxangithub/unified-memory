# Contributing to Unified Memory

> 统一记忆系统贡献指南 | Contribution Guide

---

## 目录

- [欢迎贡献](#欢迎贡献)
- [开发环境](#开发环境)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [文档规范](#文档规范)
- [测试规范](#测试规范)
- [MCP 工具开发](#mcp-工具开发)
- [插件开发](#插件开发)

---

## 欢迎贡献

Unified Memory 是一个开源的四层渐进式 AI 记忆系统，欢迎任何形式的贡献：

- 🐛 Bug 修复
- ✨ 新功能
- 📝 文档改进
- 💡 优化建议
- 🧪 测试用例

---

## 开发环境

### 环境要求

| 要求 | 版本 |
|------|------|
| Node.js | >= 18.0.0 |
| npm | >= 9.0.0 |
| Git | >= 2.30.0 |

### 安装步骤

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 2. 安装依赖
npm install

# 3. 复制环境配置
cp .env.example .env

# 4. 验证安装
mcporter call unified-memory memory_health '{}'
```

### 开发命令

```bash
# 开发模式（监听文件变化）
npm run dev

# 运行测试
npm test

# 运行特定测试文件
node --test src/core/test/*.test.js

# 代码格式化
npm run format

# 代码检查
npm run lint

# 构建文档
npm run docs
```

---

## 代码规范

### JavaScript 风格

使用 ESM 模块系统：

```javascript
// ✅ 正确的导入方式
import { memoryStore } from './storage.js';
import { getConfig } from './config.js';

// ❌ 避免使用 require
const storage = require('./storage.js');
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | kebab-case | `memory-store.js` |
| 类名 | PascalCase | `class MemoryStore` |
| 函数名 | camelCase | `function storeMemory()` |
| 常量 | UPPER_SNAKE | `const MAX_TOKEN_LIMIT` |
| 私有方法 | 下划线前缀 | `_internalMethod()` |
| 工具函数 | camelCase | `formatDate()` |

### 注释规范

```javascript
/**
 * 存储新记忆
 *
 * @param {Object} options - 存储选项
 * @param {string} options.text - 记忆内容
 * @param {string} [options.category] - 分类
 * @param {number} [options.importance] - 重要度 0-1
 * @param {string} [options.scope] - 范围 USER/TEAM/AGENT/GLOBAL
 * @returns {Promise<{id: string, success: boolean}>}
 *
 * @example
 * const result = await storeMemory({
 *   text: '用户偏好简洁风格',
 *   category: 'preference',
 *   importance: 0.8,
 *   scope: 'USER'
 * });
 */
async function storeMemory(options) {
  // 实现...
}
```

### 错误处理

```javascript
// ✅ 使用 try-catch 包装异步操作
try {
  const result = await someAsyncOperation();
  return result;
} catch (error) {
  logger.error('操作失败', { error: error.message });
  throw new MemoryError('STORE_FAILED', error.message);
}

// ✅ 使用自定义错误类
class MemoryError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
    this.name = 'MemoryError';
  }
}
```

### 类型定义

使用 JSDoc 进行类型标注：

```javascript
/**
 * @typedef {Object} Memory
 * @property {string} id - 记忆唯一标识
 * @property {string} text - 记忆内容
 * @property {string} category - 分类
 * @property {number} importance - 重要度 0-1
 * @property {string} scope - 范围
 * @property {string} tier - 层级 HOT/WARM/COLD
 * @property {number} created - 创建时间戳
 * @property {number} lastAccessed - 最后访问时间
 * @property {number} accessCount - 访问次数
 */

/**
 * @typedef {Object} SearchOptions
 * @property {string} query - 搜索关键词
 * @property {string} [scope] - 范围过滤
 * @property {number} [topK] - 返回数量
 * @property {number} [minScore] - 最低分数
 */
```

---

## 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（不是新功能或修复） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建或辅助工具变更 |

### Scope 范围

| Scope | 说明 |
|-------|------|
| `storage` | 存储相关 |
| `search` | 搜索相关 |
| `pipeline` | 管线相关 |
| `api` | API 工具 |
| `docs` | 文档相关 |
| `core` | 核心模块 |
| `config` | 配置相关 |
| `test` | 测试相关 |

### 示例

```
feat(api): 添加 memory_scene_induct 工具

添加场景归纳功能，支持从记忆中自动提取场景块。

- 新增 scene_induct 工具
- 新增 scene_list/get/delete/search/stats 工具
- 更新管线调度器支持 L2 阶段

Closes #123
```

```
fix(storage): 修复 WAL 重放时的 checksum 校验

WAL 重放时未正确校验 checksum，现已修复。

- 添加 checksum 校验逻辑
- 添加单元测试
- 更新文档说明

Fixes #456
```

### 提交检查清单

- [ ] 代码符合规范
- [ ] 有对应的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰明了
- [ ] 所有测试通过

---

## 文档规范

### 文档位置

| 文档 | 位置 | 说明 |
|------|------|------|
| README | `README.md` | 项目主文档 |
| 技术参考 | `SKILL.md` | 完整技术参考 |
| 快速开始 | `QUICKSTART.md` | 快速开始指南 |
| API 参考 | `docs/API_REFERENCE.md` | MCP 工具 API |
| 架构文档 | `docs/ARCHITECTURE.md` | 系统架构 |
| 功能列表 | `docs/FEATURES.md` | 完整功能列表 |
| 更新日志 | `CHANGELOG.md` | 版本变更记录 |

### 文档编写规范

1. **使用中文**：优先使用简体中文
2. **代码示例**：提供可运行的示例
3. **表格**：使用表格整理信息
4. **代码块**：指定语言便于高亮
5. **交叉引用**：链接到相关文档

### 示例格式

```markdown
### memory_store

存储新记忆。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | `string` | ✅ | 记忆内容 |

**示例**:

\`\`\`bash
mcporter call unified-memory memory_store '{
  "text": "用户偏好简洁风格",
  "category": "preference"
}'
\`\`\`

**返回值**:

\`\`\`json
{
  "id": "mem_xxx",
  "success": true
}
\`\`\`
```

---

## 测试规范

### 测试文件命名

```
src/
├── core/
│   └── storage.test.js    ← 单元测试
├── __tests__/
│   └── integration.test.js ← 集成测试
└── examples/
    └── test-example.js   ← 示例测试
```

### 测试结构

使用 Node.js 内置测试模块：

```javascript
import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';

describe('MemoryStore', () => {
  let store;

  before(() => {
    store = new MemoryStore();
  });

  it('should store memory successfully', async () => {
    const result = await store.store({
      text: '测试记忆',
      importance: 0.8
    });

    assert.strictEqual(result.success, true);
    assert.ok(result.id);
  });

  it('should throw error for empty text', async () => {
    await assert.rejects(
      () => store.store({ text: '' }),
      { code: 'VALIDATION_ERROR' }
    );
  });
});
```

### 测试覆盖率

- 核心功能覆盖率 > 80%
- API 工具覆盖率 > 90%
- 边界条件必须测试

### 运行测试

```bash
# 运行所有测试
npm test

# 运行特定测试
node --test src/core/storage.test.js

# 生成覆盖率报告
npm run test:coverage
```

---

## MCP 工具开发

### 工具注册

在 `src/index.js` 中注册新工具：

```javascript
// 1. 导入工具函数
import { memorySceneInduct } from './scene_tools.js';

// 2. 注册工具
server.setRequestHandler(new CallToolRequestSchema(), async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    // ... existing tools ...

    // 新增工具
    case 'memory_scene_induct':
      return handleJsonResult(memorySceneInduct(args));

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});
```

### 工具函数规范

```javascript
/**
 * 场景归纳 - 从记忆中提取场景块
 *
 * @param {Object} args - 工具参数
 * @param {string} [args.scope='USER'] - 范围
 * @param {number} [args.minMemories=3] - 最少记忆数
 * @param {number} [args.maxScenes=20] - 最大场景数
 * @returns {Promise<Array>} 场景块列表
 *
 * @example
 * const scenes = await memorySceneInduct({
 *   scope: 'USER',
 *   minMemories: 3,
 *   maxScenes: 10
 * });
 */
export async function memorySceneInduct(args = {}) {
  const {
    scope = 'USER',
    minMemories = 3,
    maxScenes = 20
  } = args;

  // 1. 参数验证
  validateScope(scope);
  validateRange(minMemories, 1, 100, 'minMemories');
  validateRange(maxScenes, 1, 100, 'maxScenes');

  // 2. 获取相关记忆
  const memories = await getMemories({ scope, minCount: minMemories });

  // 3. 场景归纳逻辑
  const scenes = await inductScenes(memories, { maxScenes });

  // 4. 返回结果
  return scenes.map(scene => ({
    id: scene.id,
    title: scene.title,
    summary: scene.summary,
    entities: scene.entities,
    actions: scene.actions,
    memoryIds: scene.memoryIds,
    timeRange: scene.timeRange,
    tags: scene.tags,
    scope: scene.scope
  }));
}
```

### 工具返回格式

```javascript
// 成功返回 - 使用 handleJsonResult
return handleJsonResult({
  success: true,
  data: resultData
});

// 错误返回 - 使用 handleError
if (error.code === 'NOT_FOUND') {
  return handleError(`Memory not found: ${id}`, 'NOT_FOUND');
}
```

---

## 插件开发

### 插件结构

```javascript
/**
 * @typedef {Object} Plugin
 * @property {string} name - 插件名称
 * @property {string} version - 插件版本
 * @property {string} description - 插件描述
 * @property {boolean} enabled - 是否启用
 * @property {PluginHooks} hooks - 插件钩子
 * @property {Object} config - 插件配置
 */

/**
 * @typedef {Object} PluginHooks
 * @property {Function} [beforeSearch] - 搜索前
 * @property {Function} [afterSearch] - 搜索后
 * @property {Function} [beforeWrite] - 写入前
 * @property {Function} [afterWrite] - 写入后
 * @property {Function} [onConflictDetected] - 冲突检测
 */
```

### 插件示例

```javascript
/**
 * 示例插件：关键词高亮
 */
export const keywordHighlighter = {
  name: 'keyword-highlighter',
  version: '1.0.0',
  description: '在搜索结果中高亮关键词',
  enabled: true,

  hooks: {
    /**
     * 搜索后处理 - 高亮关键词
     */
    afterSearch: async (results, context) => {
      const { query } = context;
      const keywords = extractKeywords(query);

      return results.map(result => ({
        ...result,
        highlights: highlightText(result.text, keywords)
      }));
    }
  },

  config: {
    highlightTag: '**',  // 高亮标签
    maxHighlights: 5     // 最大高亮数
  }
};
```

### 注册插件

```bash
mcporter call unified-memory memory_plugin_register '{
  "name": "keyword-highlighter",
  "version": "1.0.0",
  "description": "在搜索结果中高亮关键词",
  "hooks": {
    "afterSearch": "async (results, context) => { ... }"
  }
}'
```

---

## 版本管理

### 语义化版本

```
major.minor.patch
 │     │     └── 补丁版本（Bug 修复）
 │     └──────── 次版本（新功能，向后兼容）
 └───────────── 主版本（破坏性变更）
```

### 版本发布流程

1. 更新 `CHANGELOG.md`
2. 更新 `package.json` 版本号
3. 创建 Git tag
4. 推送 tag 到远程
5. GitHub Actions 自动发布

---

## 问题反馈

### Bug 报告

请包含以下信息：

1. **版本信息**：`mcporter call unified-memory memory_version '{}'`
2. **复现步骤**：清晰的重现步骤
3. **期望行为**：你期望的行为
4. **实际行为**：实际发生的行为
5. **日志**：相关的错误日志

### 功能请求

请包含以下信息：

1. **使用场景**：你想要解决的问题
2. **建议方案**：你期望的解决方案
3. **替代方案**：其他可能的方案

---

## 许可证

贡献 Unified Memory 即表示你同意你的代码遵循 MIT 许可证。

---

*最后更新: 2026-04-09 | v5.0.0*
