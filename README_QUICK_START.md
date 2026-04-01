---
title: Unified Memory — Quick Start Guide
---

<!-- Language Toggle -->
[English](./README.md) · **[中文](./README_CN.md)** · [日本語](./README_JA.md)

---

# 🚀 Quick Start | 快速入门

> **English** | [中文](#中文快速入门) | [日本語](./README_JA.md)

---

## 🌟 3-Step Installation | 3步安装

```bash
# Step 1: Navigate to skill directory
cd /root/.openclaw/workspace/skills/unified-memory-ts/

# Step 2: Run installer (auto-installs deps + configures everything)
bash scripts/install.sh

# Step 3: Verify installation
node src/cli/index.js health
```

**That's it!** You now have a fully functional AI memory system. 🎉

---

## 📖 Basic Commands | 基本命令

### Store a Memory | 存储记忆

```bash
# Store a simple memory
node src/cli/index.js store "Alice prefers tea over coffee"

# Store with category
node src/cli/index.js store "Meeting with Bob tomorrow" --category "schedule"

# Store with importance (0-1)
node src/cli/index.js store "Q1 deadline is March 31" --importance 0.9
```

### Search Memories | 搜索记忆

```bash
# Basic search (BM25 + Vector hybrid)
node src/cli/index.js search "coffee preferences"

# Search with limit
node src/cli/index.js search "meeting" --limit 5

# Search specific category
node src/cli/index.js search "Alice" --category "preferences"
```

### System Status | 系统状态

```bash
# Health check
node src/cli/index.js health

# Memory statistics
node src/cli/index.js stats

# List all memories
node src/cli/index.js list
```

### Manage Memories | 管理记忆

```bash
# Update a memory
node src/cli/index.js update <memory_id> "New content"

# Delete a memory
node src/cli/index.js delete <memory_id>

# Export memories
node src/cli/index.js export --format json
```

---

## ✅ Verification Tests | 验证测试

```bash
# Test 1: Health check
node src/cli/index.js health
# Expected: Shows system status with all components healthy

# Test 2: Store first memory
node src/cli/index.js store "My first memory - $(date)"
# Expected: Memory stored successfully with an ID

# Test 3: Search for it
node src/cli/index.js search "first memory"
# Expected: Returns the memory you just stored

# Test 4: Check stats
node src/cli/index.js stats
# Expected: Shows count of memories, categories, etc.
```

---

## 🔧 Optional: Start Web Dashboard | 可选：启动 Web 面板

```bash
# Start REST API server (port 38080)
node src/api/server.js

# Start Web UI dashboard (port 38081) - in another terminal
node src/webui/dashboard.js

# Access dashboard at http://localhost:38081
```

---

## 🔗 Documentation Index | 文档索引

> 🌍 [English](./README.md) · **[中文](./README_CN.md)** · [日本語](./README_JA.md)

| Document | Language | Description |
|----------|----------|-------------|
| [README.md](./README.md) | 🇺🇸 | Main documentation (English) |
| [README_CN.md](./README_CN.md) | 🇨🇳 | 主文档（中文） |
| [SKILL.md](./SKILL.md) | 🇺🇸 | Technical deep-dive (English) |
| [docs/index.md](./docs/index.md) | 🌍 | **📚 All docs index** — 全部文档索引 |
| [docs/en/](./docs/en/) | 🇺🇸 | English technical docs |
| [docs/zh/](./docs/zh/) | 🇨🇳 | 中文技术文档 |
| [docs/CONFIG.md](./docs/CONFIG.md) | 🌍 | Configuration guide |

**Jump to specific docs:**
- [docs/en/HOOK_INTEGRATION.md](./docs/en/HOOK_INTEGRATION.md) — Hook integration
- [docs/zh/HOOK_INTEGRATION.md](./docs/zh/HOOK_INTEGRATION.md) — Hook 集成指南
- [docs/en/MCP_INTEGRATION.md](./docs/en/MCP_INTEGRATION.md) — MCP integration
- [docs/zh/MCP_INTEGRATION.md](./docs/zh/MCP_INTEGRATION.md) — MCP 集成指南

---

## ❓ FAQ | 常见问题

### Q: Ollama is not running, what should I do?
**A:** Vector search will fall back to BM25-only mode. To enable full features:
```bash
# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull nomic-embed-text
```

### Q: "Permission denied" when running install.sh
**A:** Make the script executable:
```bash
chmod +x scripts/install.sh
```

### Q: Where is my data stored?
**A:** By default in `~/.openclaw/workspace/memory/`:
- `memories.json` - Main memory storage
- `config.json` - Configuration
- `backups/` - Automatic backups

### Q: How to reset all memories?
```bash
rm ~/.openclaw/workspace/memory/memories.json
echo '[]' > ~/.openclaw/workspace/memory/memories.json
```

### Q: How to enable debug logging?
```bash
DEBUG=* node src/cli/index.js search "test"
```

---

## 📞 Support | 支持

- GitHub Issues: https://github.com/mouxangithub/unified-memory/issues
- Documentation: [README.md](./README.md)

---

# 中文快速入门

## 🌟 3步安装

```bash
# 第1步：进入技能目录
cd /root/.openclaw/workspace/skills/unified-memory-ts/

# 第2步：运行安装脚本（自动安装依赖和配置）
bash scripts/install.sh

# 第3步：验证安装
node src/cli/index.js health
```

**完成！** 你现在拥有了一个完整的 AI 记忆系统。🎉

---

## 📖 基本命令

### 存储记忆

```bash
# 存储简单记忆
node src/cli/index.js store "Alice喜欢茶而不是咖啡"

# 带分类存储
node src/cli/index.js store "明天和Bob开会" --category "日程"

# 带重要性存储 (0-1)
node src/cli/index.js store "Q1截止日期是3月31日" --importance 0.9
```

### 搜索记忆

```bash
# 基础搜索（BM25 + 向量混合）
node src/cli/index.js search "咖啡偏好"

# 带数量限制
node src/cli/index.js search "会议" --limit 5

# 搜索特定分类
node src/cli/index.js search "Alice" --category "偏好"
```

### 系统状态

```bash
# 健康检查
node src/cli/index.js health

# 记忆统计
node src/cli/index.js stats

# 列出所有记忆
node src/cli/index.js list
```

---

## ✅ 验证测试

```bash
# 测试1：健康检查
node src/cli/index.js health
# 预期：显示所有组件正常

# 测试2：存储第一条记忆
node src/cli/index.js store "我的第一条记忆 - $(date)"
# 预期：成功存储并返回ID

# 测试3：搜索它
node src/cli/index.js search "第一条记忆"
# 预期：返回刚存储的记忆

# 测试4：查看统计
node src/cli/index.js stats
# 预期：显示记忆数量、分类等
```

---

## 🔧 可选：启动 Web 面板

```bash
# 启动 REST API 服务器（端口 38080）
node src/api/server.js

# 启动 Web UI 面板（端口 38081）- 在另一个终端
node src/webui/dashboard.js

# 访问面板：http://localhost:38081
```

---

## ❓ 常见问题

### Q: Ollama 没有运行怎么办？
**A:** 向量搜索会回退到纯 BM25 模式。启用全部功能：
```bash
# 安装并启动 Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull nomic-embed-text
```

### Q: 运行 install.sh 报 "Permission denied"
**A:** 给脚本添加执行权限：
```bash
chmod +x scripts/install.sh
```

### Q: 数据存储在哪里？
**A:** 默认在 `~/.openclaw/workspace/memory/`：
- `memories.json` - 主记忆存储
- `config.json` - 配置文件
- `backups/` - 自动备份

### Q: 如何重置所有记忆？
```bash
rm ~/.openclaw/workspace/memory/memories.json
echo '[]' > ~/.openclaw/workspace/memory/memories.json
```

### Q: 如何开启调试日志？
```bash
DEBUG=* node src/cli/index.js search "test"
```

---

## 📞 支持

- GitHub Issues: https://github.com/mouxangithub/unified-memory/issues
- 文档：[README_CN.md](./README_CN.md)

---

*其他语言版本：[English](#english) | [中文](#中文快速入门)*
