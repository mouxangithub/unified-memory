# Unified Memory v5 — Skill for OpenClaw

> 🧠 AI Agent 统一记忆系统 | 一句话安装 | MCP 协议

## 一句话安装配置命令（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install && \
OLLAMA_BASE_URL=http://localhost:11434 && \
LLM_PROVIDER=ollama && LLM_MODEL=minimax-m2.7:cloud && \
EMBED_PROVIDER=ollama && EMBED_MODEL=nomic-embed-text:latest && \
VECTOR_ENGINE=lancedb && node src/gbrain_mcp_server.js
```

---

## 功能概述

| 功能 | 工具 | 说明 |
|------|------|------|
| 🧠 记忆存储 | `remember` | 自动实体检测+关联 |
| 🔍 语义搜索 | `search` | 混合搜索+过滤 |
| 📊 图谱查询 | `graph_stats` | 关联网络统计 |
| 🧹 记忆清理 | `cleanup` | 清理低价值记忆 |
| 💬 上下文 | `get_context` | 系统状态 |

---

## 环境变量配置

创建 `.env` 文件：

```bash
# ─── LLM 配置 ───
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434

# ─── Embedding 配置 ───
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434
EMBED_DIMENSION=768

# ─── 存储配置 ───
VECTOR_ENGINE=lancedb
DATA_DIR=~/.openclaw/workspace/memory

# ─── 日志配置 ───
LOG_LEVEL=info
```

---

## OpenClaw MCP 配置

### 方式 1: mcp-config.json

```json
{
  "mcpServers": {
    "unified-memory-v5": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "minimax-m2.7:cloud",
        "EMBED_PROVIDER": "ollama",
        "EMBED_MODEL": "nomic-embed-text:latest",
        "VECTOR_ENGINE": "lancedb"
      }
    }
  }
}
```

### 方式 2: SKILL.md 安装 (Hermes)

```bash
mkdir -p ~/.hermes/skills/memory/unified-memory
cp SKILL.md ~/.hermes/skills/memory/unified-memory/
```

---

## MCP 接口兼容

- ✅ **OpenClaw** - 直接配置 `mcp.servers`
- ✅ **Claude Desktop** - 配置 `mcpServers`
- ✅ **Hermes** - 安装 SKILL.md 到 `~/.hermes/skills/`
- ✅ **其他 MCP 客户端** - 通用 stdio 协议

---

## 高级功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **API Gateway** | `src/advanced/api_gateway/` | JWT/API Key认证、限流、OpenAPI |
| **Version Control** | `src/advanced/version_control/` | 乐观锁、冲突解决、差异计算 |
| **Cache Manager** | `src/advanced/cache_manager/` | L1/L2多级缓存、淘汰策略 |
| **Monitoring** | `src/advanced/monitoring/` | Prometheus指标、健康检查 |
| **Backup/Restore** | `src/advanced/backup_restore/` | 增量/全量备份、恢复 |
| **Archival** | `src/advanced/archival/` | 冷热分层、自动归档 |
| **Benchmark** | `src/advanced/benchmark/` | 性能基准测试、对比分析 |

---

## 快速使用

```javascript
// Node.js
const { exec } = require('child_process');

// 启动 MCP 服务器
exec('node src/gbrain_mcp_server.js', {
  env: {
    OLLAMA_BASE_URL: 'http://localhost:11434',
    ...process.env
  }
});
```

---

## 测试

```bash
npm test
```

---

## 许可证

MIT
