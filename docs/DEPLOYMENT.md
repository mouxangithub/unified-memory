# 部署指南

## 环境要求

- **Node.js**: 18.0.0+
- **npm**: 9.0.0+
- **内存**: 推荐 2GB+
- **磁盘**: 预留 1GB 用于日志和缓存

## 生产环境部署

### 1. 准备工作

```bash
# 创建部署目录
sudo mkdir -p /opt/memory-optimization
sudo chown $USER:$USER /opt/memory-optimization

# 进入目录
cd /opt/memory-optimization

# 如果使用 Git 克隆
git clone <repo-url> .
# 或复制现有文件
cp -r /path/to/memory-optimization/* .
```

### 2. 安装依赖

```bash
npm install --production
```

### 3. 配置

编辑 `config.json`：

```json
{
  "workspacePath": "/root/.openclaw/workspace/memory",
  "unifiedMemoryPath": "/root/.openclaw/skills/unified-memory",
  "sync": {
    "enabled": true,
    "schedule": "0 2 * * *",
    "batchSize": 100
  },
  "monitor": {
    "healthCheckInterval": 3600,
    "alertThreshold": 3
  }
}
```

### 4. 设置定时任务

```bash
# 生成 crontab 配置
npm run crontab

# 编辑 crontab
crontab -e

# 添加以下内容：
0 2 * * * cd /opt/memory-optimization && node sync/sync_cron.js --scheduled >> logs/cron.log 2>&1
0 * * * * cd /opt/memory-optimization && node monitor/health_check.js --check >> logs/health.log 2>&1
```

### 5. 初始化同步状态

```bash
# 干运行验证
npm run sync:dry-run

# 确认无误后执行首次同步
npm run sync:manual
```

## Docker 部署（可选）

### Dockerfile

```dockerfile
FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

CMD ["node", "index.js"]
```

### 构建和运行

```bash
docker build -t memory-optimization .
docker run -d \
  --name memory-optimization \
  -v /root/.openclaw/workspace/memory:/root/.openclaw/workspace/memory \
  -v /root/.openclaw/skills/unified-memory:/root/.openclaw/skills/unified-memory \
  memory-optimization
```

## 验证部署

### 检查服务状态

```bash
# 健康检查
npm run monitor:dashboard

# 查看同步日志
tail -20 logs/sync_*.jsonl
```

### 性能基准测试

```bash
# 测试查询性能
node api/unified_query_api.js --stats

# 测试去重性能
node dedup/cross_system_dedup.js --stats
```

## 监控设置

### 日志轮转

使用 `logrotate` 管理日志：

```
/opt/memory-optimization/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

### 告警配置

当健康检查返回 `unhealthy` 状态时，可配置告警：

```javascript
// scripts/alert.js
const monitor = new MemoryHealthMonitor();
const result = await monitor.checkHealth();

if (result.overallStatus === 'unhealthy') {
  // 发送告警（邮件/钉钉/飞书等）
  await sendAlert(result);
}
```

## 备份策略

### 关键文件

- `config.json` - 配置文件
- `sync/sync_state.json` - 同步状态
- `logs/` - 日志目录

```bash
# 每日备份脚本
tar -czf backup_$(date +%Y%m%d).tar.gz \
  config.json \
  sync/sync_state.json \
  logs/
```

## 升级

```bash
# 拉取新版本
git pull

# 更新依赖
npm install

# 运行测试
npm test

# 部署
npm run sync:dry-run
npm run sync:manual
```

## 回滚

```bash
# 查看版本
git log --oneline

# 回滚到上一个版本
git revert HEAD

# 或回滚到指定版本
git revert <commit-hash>
```

## 故障排查

### 服务无响应

```bash
# 检查 Node 进程
ps aux | grep node

# 查看错误日志
tail -50 logs/error.log
```

### 同步失败

```bash
# 检查目录权限
ls -la /root/.openclaw/workspace/memory
ls -la /root/.openclaw/skills/unified-memory

# 手动运行同步查看详细错误
npm run sync:manual --verbose
```

### 性能下降

```bash
# 检查资源使用
top -p $(pgrep -f memory-optimization)

# 清理缓存
node api/unified_query_api.js --clear-cache
node dedup/cross_system_dedup.js --clear-cache
```
