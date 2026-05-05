# Unified Memory v5 快速安装

## 一句话安装 + 配置（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install && \
OLLAMA_BASE_URL=http://localhost:11434 && \
LLM_PROVIDER=ollama && LLM_MODEL=minimax-m2.7:cloud && \
EMBED_PROVIDER=ollama && EMBED_MODEL=nomic-embed-text:latest && \
VECTOR_ENGINE=lancedb && node src/gbrain_mcp_server.js
```

---

## 环境变量配置

创建 `.env` 文件：

```bash
# ─────────────────────────────────────────────────────────────────────────────
# LLM 配置
# ─────────────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud

# ─────────────────────────────────────────────────────────────────────────────
# Embedding 配置
# ─────────────────────────────────────────────────────────────────────────────
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest

# ─────────────────────────────────────────────────────────────────────────────
# 向量引擎
# ─────────────────────────────────────────────────────────────────────────────
VECTOR_ENGINE=lancedb
LANCEDB_DB_PATH=~/.unified-memory/lancedb

# ─────────────────────────────────────────────────────────────────────────────
# 存储
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR=~/.unified-memory/data
GRAPH_DB_PATH=~/.unified-memory/graph.json

# ─────────────────────────────────────────────────────────────────────────────
# 日志
# ─────────────────────────────────────────────────────────────────────────────
LOG_LEVEL=info
```

---

## 完整配置项列表

### LLM 配置
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | 提供商 | ollama |
| `LLM_MODEL` | 模型 | minimax-m2.7:cloud |
| `LLM_BASE_URL` | API 地址 | http://localhost:11434 |
| `LLM_MAX_TOKENS` | 最大 tokens | 8192 |
| `LLM_TEMPERATURE` | 温度 | 0.7 |

### Embedding 配置
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EMBED_PROVIDER` | 提供商 | ollama |
| `EMBED_MODEL` | 模型 | nomic-embed-text:latest |
| `EMBED_BASE_URL` | API 地址 | http://localhost:11434 |
| `EMBED_DIMENSION` | 向量维度 | 768 |

### 向量引擎
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VECTOR_ENGINE` | 引擎 | lancedb |
| `VECTOR_DB_PATH` | 数据库路径 | ~/.unified-memory/ |

### MCP 服务
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MCP_PORT` | 端口 | 38421 |
| `MCP_MODE` | 模式 | stdio |

详细配置：[CONFIG.md](docs/CONFIG.md)

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
```

### 2. 安装依赖

```bash
npm install
```

### 3. 配置环境变量

```bash
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
VECTOR_ENGINE=lancedb
DATA_DIR=~/.unified-memory/data
LOG_LEVEL=info
EOF
```

### 4. 启动服务

```bash
node src/gbrain_mcp_server.js
```

---

## OpenClaw 配置

在 `~/.openclaw/openclaw.json` 添加：

```json
{
  "mcp": {
    "servers": {
      "agent-brain": {
        "command": "node",
        "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"],
        "env": {
          "OLLAMA_BASE_URL": "http://localhost:11434",
          "LLM_PROVIDER": "ollama",
          "LLM_MODEL": "minimax-m2.7:cloud",
          "EMBED_PROVIDER": "ollama",
          "EMBED_MODEL": "nomic-embed-text:latest"
        }
      }
    }
  }
}
```

重启：`openclaw gateway restart`

---

## Claude Desktop 配置

在 `claude_desktop_config.json` 添加：

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "minimax-m2.7:cloud",
        "EMBED_PROVIDER": "ollama",
        "EMBED_MODEL": "nomic-embed-text:latest"
      }
    }
  }
}
```

---

## Hermes 配置

### 方式 1: SKILL.md 安装 (推荐)

```bash
# 创建目录并安装
mkdir -p ~/.hermes/skills/memory/unified-memory
cp unified-memory/SKILL.md ~/.hermes/skills/memory/unified-memory/

# 验证
hermes skills list | grep unified
```

### 方式 2: MCP Server

```yaml
mcp:
  servers:
    - name: gbrain
      command: node
      args:
        - /path/to/unified-memory/src/gbrain_mcp_server.js
      env:
        OLLAMA_BASE_URL: http://localhost:11434
        LLM_PROVIDER: ollama
        LLM_MODEL: minimax-m2.7:cloud
        EMBED_PROVIDER: ollama
        EMBED_MODEL: nomic-embed-text:latest
```

---

## 验证安装

```bash
# 测试 MCP 服务
node -e "import('./src/gbrain_mcp_server.js').then(() => console.log('✅ OK'))"

# 或使用 CLI
node src/brain_cli.js --help
```

---

## 可用工具

| 工具 | 用途 | 参数 |
|------|------|------|
| `remember` | 存储记忆 | text, category, importance, entities, project, topics |
| `search` | 语义搜索 | query, limit, entity, project, topic |
| `get_context` | 获取状态 | - |
| `graph_stats` | 图谱统计 | - |
| `cleanup` | 清理记忆 | threshold, max_age_days |

---

## 快速参考

```bash
# 一行命令安装 + 配置 (Ollama 本地)
cd unified-memory && \
echo 'OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
VECTOR_ENGINE=lancedb' > .env && \
node src/gbrain_mcp_server.js
```