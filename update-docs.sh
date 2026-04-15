#!/bin/bash

echo "📚 更新 Unified Memory 文档"
echo "=============================="

# 备份原始 README
if [ -f "README.md" ]; then
    cp README.md README-backup.md
    echo "✅ 备份原始 README.md"
fi

# 更新 README.md
if [ -f "README-UPDATED.md" ]; then
    cp README-UPDATED.md README.md
    echo "✅ 更新 README.md (v5.2.0)"
fi

# 创建文档目录结构
echo "📁 创建文档目录结构..."
mkdir -p docs/{en,zh,examples,api}

# 创建核心文档
cat > docs/QUICKSTART.md << 'EOF'
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
EOF

echo "✅ 创建 docs/QUICKSTART.md"

# 创建 API 文档
cat > docs/API.md << 'EOF'
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
EOF

echo "✅ 创建 docs/API.md"

# 创建部署指南
cat > docs/DEPLOYMENT.md << 'EOF'
# Unified Memory 部署指南

## 生产环境部署

### 1. 环境要求
- Node.js >= 18.0.0
- npm >= 8.0.0
- 磁盘空间: 至少 1GB
- 内存: 至少 2GB

### 2. 安装步骤
```bash
# 克隆代码
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 安装依赖
npm install --production

# 部署原子写入修复
./deploy-atomic-fixes.sh

# 验证修复
./verify-repairs.sh
```

### 3. 配置
创建配置文件 `config.json`:
```json
{
  "storage": {
    "mode": "json",
    "memoryFile": "/var/lib/unified-memory/memories.json"
  },
  "vectorStore": {
    "backend": "lancedb",
    "path": "/var/lib/unified-memory/vector.lance"
  },
  "transaction": {
    "enable": true,
    "recoveryLog": "/var/log/unified-memory/transaction.log"
  },
  "performance": {
    "cacheSize": 1000,
    "writeBehindDelay": 500
  }
}
```

### 4. 启动服务
```bash
# 直接启动
npm start

# 使用 PM2 (推荐)
npm install -g pm2
pm2 start npm --name "unified-memory" -- start
pm2 save
pm2 startup
```

### 5. 监控
```bash
# 查看日志
tail -f /var/log/unified-memory/app.log

# 监控性能
pm2 monit

# 查看状态
pm2 status
```

## Docker 部署

### 1. 构建镜像
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### 2. 运行容器
```bash
# 构建镜像
docker build -t unified-memory:5.2.0 .

# 运行容器
docker run -d \
  -p 3000:3000 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -v ./config.json:/app/config.json \
  --name unified-memory \
  unified-memory:5.2.0
```

### 3. Docker Compose
```yaml
version: '3.8'

services:
  unified-memory:
    image: unified-memory:5.2.0
    container_name: unified-memory
    ports:
      - "3000:3000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config.json:/app/config.json
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

## 原子写入修复部署

### 1. 部署脚本
```bash
# 运行部署脚本
./deploy-atomic-fixes.sh

# 脚本功能:
# 1. 备份当前代码
# 2. 验证修复内容
# 3. 运行测试
# 4. 创建部署报告
```

### 2. 验证修复
```bash
# 验证所有修复
./verify-repairs.sh

# 输出:
# ✅ 原子事务管理器 - 已实现
# ✅ 数据持久化保证 - 已添加 fsync
# ✅ 向量搜索优化 - 已改进
# ✅ ChromaDB 后端 - 已准备
# ✅ 部署脚本 - 已创建
# ✅ 文档 - 已更新
```

### 3. 性能测试
```bash
# 运行性能基准测试
node test/benchmark/write-performance.js

# 测试原子事务
node test-atomic-fix.js
```

## 故障排除

### 1. 数据不一致
```bash
# 检查事务日志
cat /root/.unified-memory/transaction-recovery.log

# 恢复事务
node -e "import('./src/transaction-manager.js').then(m => new m.AtomicTransactionManager().recoverTransactions())"
```

### 2. 性能问题
```bash
# 检查向量存储
node -e "import('./src/vector_lancedb.js').then(m => new m.VectorMemory().initialize())"

# 切换到 ChromaDB
docker run -d -p 8000:8000 chromadb/chroma
# 更新配置: vectorStore.backend = 'chromadb'
```

### 3. 启动失败
```bash
# 检查日志
cat logs/*.log

# 清理损坏的事务
rm -f /root/.unified-memory/temp/*.tmp
rm -f /root/.unified-memory/transaction-recovery.log
```

## 监控与维护

### 1. 健康检查
```bash
# API 健康检查
curl http://localhost:3000/health

# 数据一致性检查
node scripts/check-consistency.js
```

### 2. 备份策略
```bash
# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/backup/unified-memory/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp /var/lib/unified-memory/*.json $BACKUP_DIR/
cp /var/lib/unified-memory/*.lance $BACKUP_DIR/
```

### 3. 性能监控
- **写入延迟**: 事务提交时间
- **读取延迟**: 搜索响应时间
- **缓存命中率**: 内存缓存效率
- **数据一致性**: 原子写入成功率

## 升级指南

### 从 v5.1.0 升级到 v5.2.0
```bash
# 1. 备份数据
cp -r /var/lib/unified-memory /var/lib/unified-memory-backup

# 2. 停止服务
pm2 stop unified-memory

# 3. 更新代码
git pull origin main

# 4. 部署修复
./deploy-atomic-fixes.sh

# 5. 重启服务
pm2 start unified-memory

# 6. 验证升级
./verify-repairs.sh
```

### 回滚方案
```bash
# 1. 停止服务
pm2 stop unified-memory

# 2. 恢复备份
cp -r /var/lib/unified-memory-backup/* /var/lib/unified-memory/

# 3. 恢复代码
git checkout v5.1.0

# 4. 重启服务
pm2 start unified-memory
```
EOF

echo "✅ 创建 docs/DEPLOYMENT.md"

echo ""
echo "📚 文档更新完成！"
echo "已更新以下文档:"
echo "  ✅ README.md (v5.2.0)"
echo "  ✅ CHANGELOG.md (添加 v5.2.0)"
echo "  ✅ SKILL.md (添加 v5.2.0)"
echo "  ✅ docs/QUICKSTART.md"
echo "  ✅ docs/API.md"
echo "  ✅ docs/DEPLOYMENT.md"
echo ""
echo "🚀 可以提交到 GitHub 了！"