# 🧠 Unified Memory — 快速安装指南

> 5 分钟内让你的 AI Agent 拥有持久记忆能力

---

## 📋 前置要求

| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| Node.js | v22+ | 运行环境和 MCP Server |
| Git | 任意 | 克隆仓库 |
| Ollama | 可选 | 向量嵌入模型，无则降级为 BM25 |

> **提示**: 没有 Ollama 也能正常运行，系统会自动切换到 BM25 全文搜索模式。

---

## ⚡ 一键安装

### 方式 1: 自动安装脚本（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

或手动运行：

```bash
git clone https://github.com/mouxangithub/unified-memory.git \
  ~/.openclaw/workspace/skills/unified-memory

cd ~/.openclaw/workspace/skills/unified-memory
npm install --ignore-scripts --no-peer-dependencies
```

### 方式 2: 符号链接（开发模式）

```bash
git clone https://github.com/mouxangithub/unified-memory.git \
  ~/projects/unified-memory

ln -s ~/projects/unified-memory \
    ~/.openclaw/workspace/skills/unified-memory
```

---

## 🔧 配置

### 环境变量（可选）

创建 `~/.openclaw/skills/unified-memory/.env`：

```bash
# Ollama 配置（可选）
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# 记忆存储路径（可选）
MEMORY_DATA_DIR=~/.openclaw/workspace/memory/

# 日志级别
LOG_LEVEL=info
```

### OpenClaw 集成

重启 OpenClaw 即可自动加载：

```bash
openclaw gateway restart
```

### 其他 AI Agent（MCP 协议）

在 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/index.js"]
    }
  }
}
```

---

## ✅ 验证安装

```bash
cd ~/.openclaw/workspace/skills/unified-memory

# 健康检查
node src/cli/index.js health

# 或通过 MCP 协议
mcporter call unified-memory memory_health '{}'
```

---

## 🚀 快速开始

### 1. 存储记忆

```bash
mcporter call unified-memory memory_store \
  '{"content": "用户叫刘选权，擅长 JavaScript", "category": "user_info"}'
```

### 2. 搜索记忆

```bash
mcporter call unified-memory memory_search \
  '{"query": "刘选权 擅长"}'
```

### 3. 列出所有记忆

```bash
mcporter call unified-memory memory_list '{}'
```

### 4. 删除记忆

```bash
mcporter call unified-memory memory_delete \
  '{"memory_id": "mem_xxx"}'
```

---

## 🧩 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Unified Memory v4.0                      │
├─────────────────────────────────────────────────────────────┤
│  L0: 对话录制  →  transcript_first.js                       │
│       ↓                                                      │
│  L1: 记忆提取  →  extract.js + memory_types/                 │
│       ↓                                                      │
│  L2: 场景归纳  →  scene_block.js                            │
│       ↓                                                      │
│  L3: 用户画像  →  profile.js / persona_generator.js          │
├─────────────────────────────────────────────────────────────┤
│  搜索: BM25 + Vector + Hybrid + QMD + MMR + Rerank         │
│  存储: JSON文件 + WAL + Tier分层 + 去重                     │
│  智能: 噪声过滤 + 意图路由 + 自适应跳过 + 反思学习           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 示例代码

详见 [`examples/`](./examples/) 目录：

- `basic_usage.js` — 基础 CRUD 操作
- `enhanced_memory_example.js` — 增强记忆系统
- `layered_compression_example.js` — 分层压缩
- `workflow_complete.js` — 完整工作流

---

## 🐛 故障排除

### MCP Server 启动失败

```bash
# 检查 Node 版本
node -v  # 需要 v22+

# 手动启动调试
node src/index.js
```

### 向量搜索不工作

```bash
# 检查 Ollama 状态
curl http://127.0.0.1:11434/api/tags

# 安装嵌入模型
ollama pull nomic-embed-text
```

### 权限错误

```bash
# 确保目录可写
chmod 755 ~/.openclaw/workspace/memory/
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE)
