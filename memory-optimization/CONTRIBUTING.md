# 贡献指南

感谢您对记忆系统优化项目的兴趣！本文档帮助您了解如何参与贡献。

## 开发环境

### 前置条件

- Node.js 18+
- npm 9+

### 设置开发环境

```bash
# 克隆或进入项目目录
cd /root/.openclaw/workspace/memory-optimization

# 安装依赖
npm install

# 验证安装
node index.js
```

## 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 2. 开发与测试

```bash
# 干运行模式测试同步
npm run sync:dry-run

# 运行测试
npm run test

# 健康检查
npm run monitor:dashboard
```

### 3. 代码规范

- 使用 ES2022+ 语法
- 异步操作使用 `async/await`
- 所有函数需要 JSDoc 注释
- 错误处理要完善

**代码示例**：

```javascript
/**
 * 同步记忆到 Unified Memory
 * @param {Object} memory - 记忆对象
 * @param {string} memory.content - 记忆内容
 * @param {string} memory.type - 记忆类型
 * @returns {Promise<Object>} 同步结果
 */
async function syncMemory(memory) {
  try {
    const result = await storeToUnifiedMemory(memory);
    return { success: true, id: result.id };
  } catch (error) {
    console.error('同步失败:', error.message);
    return { success: false, error: error.message };
  }
}
```

### 4. 提交代码

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# feat: 新功能
git commit -m "feat: 添加实时同步功能"

# fix: 修复 bug
git commit -m "fix: 修复去重检查的性能问题"

# docs: 文档更新
git commit -m "docs: 更新 API 文档"

# refactor: 重构
git commit -m "refactor: 优化同步批处理逻辑"

# test: 测试
git commit -m "test: 添加去重模块单元测试"

# chore: 维护任务
git commit -m "chore: 更新依赖版本"
```

## 模块开发指南

### 添加新同步策略

在 `sync/` 目录添加新文件：

```javascript
// sync/strategy_xxx.js
class SyncStrategy {
  async execute(memories) {
    // 实现同步逻辑
  }
}
export default SyncStrategy;
```

### 添加新的去重算法

在 `dedup/` 目录扩展：

```javascript
// dedup/similarity_algorithm.js
export function calculateSimilarity(text1, text2) {
  // 实现相似度计算
}
```

### 添加新的监控指标

在 `monitor/health_check.js` 中添加检查项：

```javascript
async checkNewComponent() {
  const result = { healthy: true, metrics: {} };
  // 实现检查逻辑
  return result;
}
```

## 测试指南

### 运行所有测试

```bash
npm run test
```

### 干运行模式

所有同步操作都支持 `--dry-run` 模式，不会实际写入数据：

```bash
npm run sync:dry-run
node dedup/cross_system_dedup.js --test --dry-run
```

### 日志分析

同步日志位于 `logs/sync_*.jsonl`：

```bash
# 查看最近同步记录
tail -20 logs/sync_*.jsonl

# 查看错误记录
grep '"level":"error"' logs/sync_*.jsonl
```

## Pull Request 流程

1. Fork 本仓库
2. 创建功能分支
3. 编写代码和测试
4. 更新文档（如有必要）
5. 提交 Pull Request

### PR 模板

```markdown
## 描述
[简要描述这个 PR 解决的问题]

## 改动
- [改动点 1]
- [改动点 2]

## 测试
- [ ] 干运行测试通过
- [ ] 日志检查无错误

## 截图（如有 UI 变化）
[截图]
```

## 问题反馈

发现 bug 或有新功能建议？请通过 GitHub Issue 反馈。

报告问题时，请包含：

1. **环境信息**：Node.js 版本、操作系统
2. **复现步骤**：如何一步步复现问题
3. **预期行为**：您期望的行为
4. **实际行为**：实际发生的行为
5. **日志**：相关的错误日志

## 文档贡献

文档同样重要！如果您发现文档：

- 过期或不准确
- 缺少关键信息
- 语言可以更清晰

欢迎提交 PR 或 Issue。

## 许可证

通过提交代码，您同意您的贡献将遵循 MIT 许可证。
