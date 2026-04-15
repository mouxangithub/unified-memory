# 快速开始指南

[English](../../en/getting-started/quickstart.md) · [中文](./quickstart.md)

本指南将帮助您在 5 分钟内开始使用 Unified Memory。

## 🚀 安装

### 选项 1: 使用安装脚本 (推荐)
```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### 选项 2: 使用 npm
```bash
# 全局安装
npm install -g unified-memory

# 或在项目中本地安装
npm install unified-memory
```

### 选项 3: 手动安装
```bash
# 克隆仓库
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 安装依赖
npm install

# 构建项目
npm run deploy
```

## 📦 验证安装

```bash
# 检查安装是否成功
unified-memory --version
# 应该输出: v5.2.0

# 或如果本地安装
node -e "console.log(require('unified-memory').version)"
```

## 🔧 基础配置

在 `~/.unified-memory/config.json` 创建配置文件：

```json
{
  "storage": {
    "mode": "json",
    "memoryFile": "~/.unified-memory/memories.json",
    "vectorStore": {
      "backend": "lancedb",
      "path": "~/.unified-memory/vector.lance"
    }
  },
  "transaction": {
    "enable": true,
    "recoveryLog": "~/.unified-memory/transaction-recovery.log"
  }
}
```

## 💡 您的第一个记忆

### 使用 JavaScript/TypeScript
```javascript
import { addMemory, searchMemories } from 'unified-memory';

// 添加第一个记忆
const memoryId = await addMemory({
  text: "记得查看季度报告",
  tags: ["工作", "提醒", "报告"],
  metadata: {
    priority: "高",
    category: "工作",
    createdBy: "user123"
  }
});

console.log(`记忆已添加，ID: ${memoryId}`);

// 搜索记忆
const results = await searchMemories("季度报告");
console.log("搜索结果:", results);
```

### 使用 CLI
```bash
# 通过 CLI 添加记忆
unified-memory add "记得查看季度报告" --tags 工作,提醒,报告

# 搜索记忆
unified-memory search "季度报告"

# 列出所有记忆
unified-memory list
```

## 🔍 基础搜索示例

### 简单文本搜索
```javascript
const results = await searchMemories("会议记录");
```

### 带过滤器的搜索
```javascript
const results = await searchMemories("项目", {
  filters: {
    tags: ["工作", "紧急"],
    metadata: {
      priority: "高"
    }
  },
  limit: 10
});
```

### 混合搜索 (BM25 + 向量)
```javascript
const results = await searchMemories("重要截止日期", {
  searchType: "hybrid",  // 选项: "bm25", "vector", "hybrid"
  vectorWeight: 0.7,     // 向量相似度权重 (0-1)
  bm25Weight: 0.3        // BM25 相关性权重 (0-1)
});
```

## 📊 查看记忆

### 获取所有记忆
```javascript
const allMemories = await getAllMemories({
  limit: 50,
  offset: 0,
  sortBy: "createdAt",
  sortOrder: "desc"
});
```

### 按 ID 获取记忆
```javascript
const memory = await getMemory(memoryId);
console.log(memory);
```

### 获取记忆统计
```javascript
const stats = await getMemoryStats();
console.log(stats);
// 输出: { total: 150, byTag: { work: 50, personal: 100 }, ... }
```

## 🔄 原子事务示例

Unified Memory v5.2.0 保证原子写入：

```javascript
import { beginTransaction, commitTransaction, rollbackTransaction } from 'unified-memory';

try {
  // 开始事务
  const tx = await beginTransaction();
  
  // 原子性地添加多个记忆
  await addMemory({
    text: "事务中的第一个记忆",
    tags: ["事务", "测试"]
  }, { transaction: tx });
  
  await addMemory({
    text: "事务中的第二个记忆",
    tags: ["事务", "测试"]
  }, { transaction: tx });
  
  // 提交 - 两个记忆都原子性地保存
  await commitTransaction(tx);
  console.log("事务提交成功");
  
} catch (error) {
  // 如果任何操作失败，事务回滚
  await rollbackTransaction(tx);
  console.error("事务回滚:", error);
}
```

## 🔌 插件系统快速开始

### 与 Workspace Memory 同步
```bash
# 手动同步
npm run sync:manual

# 定时同步 (每日凌晨2点)
npm run sync
```

### 统一查询接口
```bash
# 跨所有记忆系统搜索
npm run query:unified -- "搜索关键词"

# 在端口 3851 启动查询服务器
npm run query:unified -- --server 3851
```

### 健康监控
```bash
# 检查系统健康
npm run monitor

# 查看仪表板
npm run monitor:dashboard
```

## 🧪 测试您的设置

### 运行基础测试
```bash
# 验证核心功能
npm run verify

# 运行单元测试
npm run test:unit

# 运行集成测试
npm run test:integration
```

### 测试原子写入
```bash
# 测试事务安全性
npm run test:unit -- --test atomic-transactions
```

## 🚨 故障排除

### 常见问题

1. **"Module not found" 错误**
   ```bash
   # 重新安装依赖
   npm install
   ```

2. **向量存储初始化失败**
   ```bash
   # 重新初始化向量存储
   rm -rf ~/.unified-memory/vector.lance
   unified-memory init
   ```

3. **权限错误**
   ```bash
   # 修复权限
   chmod 755 ~/.unified-memory
   ```

### 获取帮助

- 查看[故障排除指南](../guides/troubleshooting.md)
- 搜索[GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
- 查阅[常见问题](../reference/faq.md)

## 📈 下一步

完成快速开始后，探索：

1. **[高级功能](../guides/advanced-features.md)** - 了解高级功能
2. **[API 文档](../api/overview.md)** - 完整的 API 参考
3. **[插件系统](../guides/plugins.md)** - 使用插件扩展功能
4. **[性能调优](../reference/configuration.md)** - 为您的用例优化

---

**需要帮助？** 加入我们的社区或在 GitHub 上提出问题！

[← 返回文档](../../README_CN.md) · [下一步: 高级功能 →](../guides/advanced-features.md)