# Unified Memory v5 一句话安装

## AI Agent 快速安装命令

```bash
# 1. 克隆并安装
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install

# 2. 启动服务 (Node.js)
node src/gbrain_mcp_server.js

# 3. 配置 MCP 客户端
# OpenClaw: 添加到 mcp-config.json
# Claude Desktop: 添加到 claude_desktop_config.json
```

---

## 一句话说给 AI

```
"请帮我安装 Unified Memory v5：git clone https://github.com/mouxangithub/unified-memory.git，
cd unified-memory && npm install，然后启动 node src/gbrain_mcp_server.js，
最后配置 OpenClaw/Claude 使用 MCP 协议连接。"
```

---

## OpenClaw 配置

```bash
# 在 openclaw.json 中添加：
{
  "mcp": {
    "servers": {
      "unified-memory": {
        "command": "node",
        "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"]
      }
    }
  }
}
```

## ⚙️ 配置 (.env)

```bash
# LLM 配置
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434

# Embedding 配置
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434

# 向量引擎
VECTOR_ENGINE=lancedb
```

详细配置：[CONFIG.md](docs/CONFIG.md)

---

## 验证安装

```bash
# 测试 MCP 服务
node -e "import('./src/gbrain_mcp_server.js').then(() => console.log('OK'))"

# 或使用 CLI
node src/brain_cli.js --help
```

---

## 可用工具

| 工具 | 用途 |
|------|------|
| `remember` | 存储记忆（自动实体检测+关联） |
| `search` | 语义搜索记忆 |
| `get_context` | 获取当前状态 |
| `graph_stats` | 图谱统计 |
| `cleanup` | 清理低价值记忆 |

---

## 支持平台

- ✅ OpenClaw
- ✅ Claude Desktop
- ✅ Cursor AI
- ✅ Hermes
- ✅ 任意 MCP 客户端
