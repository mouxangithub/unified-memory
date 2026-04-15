# Unified Memory 快速开始指南

## 安装

```bash
# 克隆仓库
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 安装依赖
npm install

# 运行测试
npm test
```

## 基本使用

### 添加记忆
```javascript
import { addMemory } from './src/storage.js';

const memory = await addMemory({
  text: '用户喜欢使用深色主题',
  category: 'preference',
  importance: 0.8,
  tags: ['ui', 'theme']
});
```

### 搜索记忆
```javascript
import { searchMemories } from './src/storage.js';

const results = await searchMemories('深色主题', {
  topK: 10,
  scope: 'USER'
});
```

### 获取所有记忆
```javascript
import { getAllMemories } from './src/storage.js';

const allMemories = await getAllMemories();
```

## 配置

### 基本配置
```json
{
  "storage": {
    "mode": "json",
    "memoryFile": "~/.unified-memory/memories.json"
  },
  "vectorStore": {
    "backend": "lancedb",
    "path": "~/.unified-memory/vector.lance"
  }
}
```

### 性能调优
```json
{
  "performance": {
    "cacheSize": 1000,
    "writeBehindDelay": 500,
    "vectorCache": true
  }
}
```

## 部署原子写入修复

```bash
# 一键部署
./deploy-atomic-fixes.sh

# 验证修复
./verify-repairs.sh
```

## 故障排除

### 常见问题
1. **数据不一致**: 运行部署脚本修复
2. **性能问题**: 检查向量存储配置
3. **启动失败**: 检查事务恢复日志

### 获取帮助
- GitHub Issues: https://github.com/mouxangithub/unified-memory/issues
- 文档: ./docs/
- 邮件: mouxan@163.com
