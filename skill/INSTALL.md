# 安装指南

## 前置条件

- Node.js 18+
- OpenClaw 平台
- Unified Memory 技能（已安装）

## 安装步骤

### 1. 克隆或复制项目

```bash
# 克隆（推荐）
cd /root/.openclaw/workspace
git clone <repo-url> memory-optimization

# 或复制现有文件
cp -r /path/to/memory-optimization /root/.openclaw/workspace/
```

### 2. 安装依赖

```bash
cd /root/.openclaw/workspace/memory-optimization
npm install
```

### 3. 验证安装

```bash
node index.js
# 输出可用模块列表

npm run sync:dry-run
# 干运行同步测试
```

### 4. 初始同步

```bash
# 干运行确认无误后
npm run sync:manual
```

### 5. 设置定时任务

```bash
npm run crontab
# 将输出复制到 crontab
crontab -e
```

## 目录结构

```
/root/.openclaw/workspace/memory-optimization/
├── sync/               # 同步模块
├── api/                # API模块
├── dedup/              # 去重模块
├── monitor/            # 监控模块
├── scripts/            # 脚本
├── logs/               # 日志目录
├── docs/               # 文档
├── skill/              # ClawHub发布包
├── config.json          # 配置文件
├── index.js            # 主入口
└── package.json        # 项目配置
```

## 卸载

```bash
# 删除项目目录
rm -rf /root/.openclaw/workspace/memory-optimization

# 移除 crontab
crontab -e
# 删除相关行
```

## 故障排查

### 找不到 Unified Memory

确保 Unified Memory 已安装在：`/root/.openclaw/skills/unified-memory`

### 同步失败

```bash
# 检查权限
ls -la /root/.openclaw/workspace/memory
ls -la /root/.openclaw/skills/unified-memory

# 查看日志
tail -20 logs/sync_*.jsonl
```

### 依赖问题

```bash
npm install
# 如遇权限问题
sudo npm install --unsafe-perm
```
