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
