# Unified Memory API 参考

## 存储 API

### `addMemory(memory)`
添加新记忆。

**参数**:
- `memory`: 记忆对象
  - `text`: 记忆文本 (必填)
  - `category`: 分类 (可选)
  - `importance`: 重要性 (0-1, 默认 0.5)
  - `tags`: 标签数组 (可选)
  - `scope`: 范围 (USER/AGENT/TEAM/GLOBAL, 默认 USER)

**返回**: 添加的记忆对象 (包含 id)

**示例**:
```javascript
const memory = await addMemory({
  text: '用户偏好设置',
  category: 'preference',
  importance: 0.8,
  tags: ['ui', 'settings']
});
```

### `getMemory(id)`
获取指定记忆。

**参数**:
- `id`: 记忆 ID

**返回**: 记忆对象 或 `null`

### `getAllMemories()`
获取所有记忆。

**返回**: 记忆数组

### `searchMemories(query, options)`
搜索记忆。

**参数**:
- `query`: 搜索查询文本
- `options`: 搜索选项
  - `topK`: 返回数量 (默认 10)
  - `scope`: 搜索范围 (可选)
  - `category`: 分类过滤 (可选)

**返回**: 搜索结果数组

### `deleteMemory(id)`
删除记忆。

**参数**:
- `id`: 记忆 ID

**返回**: `true` (成功) 或 `false` (失败)

## 事务管理 API

### `AtomicTransactionManager`
原子事务管理器类。

**方法**:
- `beginTransaction()`: 开始新事务
- `prepareJsonWrite(txId, memory)`: 准备 JSON 写入
- `prepareVectorWrite(txId, memory, embedding)`: 准备向量写入
- `commitTransaction(txId)`: 提交事务
- `rollbackTransaction(txId)`: 回滚事务
- `recoverTransactions()`: 恢复未完成的事务

**示例**:
```javascript
import { AtomicTransactionManager } from './src/transaction-manager.js';

const txManager = new AtomicTransactionManager();
const txId = await txManager.beginTransaction();

try {
  await txManager.prepareJsonWrite(txId, memory);
  await txManager.prepareVectorWrite(txId, memory, embedding);
  await txManager.commitTransaction(txId);
} catch (error) {
  await txManager.rollbackTransaction(txId);
  throw error;
}
```

## 向量存储 API

### `VectorMemory`
向量存储类。

**方法**:
- `initialize()`: 初始化向量存储
- `upsert(memory)`: 插入或更新向量
- `search(query, topK)`: 搜索相似向量
- `delete(id)`: 删除向量
- `queryRowsWithFilter(filterFn)`: 带过滤的查询

## 配置 API

### `config`
配置对象。

**属性**:
- `storage.mode`: 存储模式 (json/sqlite)
- `storage.memoryFile`: 记忆文件路径
- `vectorStore.backend`: 向量存储后端 (lancedb/chromadb/faiss)
- `vectorStore.path`: 向量存储路径
- `transaction.enable`: 是否启用事务
- `performance.cacheSize`: 缓存大小

## 工具函数

### 部署工具
- `deploy-atomic-fixes.sh`: 一键部署原子写入修复
- `verify-repairs.sh`: 验证修复是否成功
- `test-atomic-fix.js`: 测试原子事务功能

### 测试工具
- `test/benchmark/write-performance.js`: 性能基准测试
- `test-all-functions.js`: 全面功能测试
