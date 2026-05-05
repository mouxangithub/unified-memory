# 🧠 Unified Memory v5

> AI Agent 的统一记忆系统 | MCP 协议 | 一句话安装

**让 AI 拥有记忆，让记忆成为智能的基石。**

---

## ⚡ 一句话安装配置（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
1. git clone https://github.com/mouxangithub/unified-memory.git
2. cd unified-memory && npm install
3. 配置环境变量：
   - OLLAMA_BASE_URL=http://localhost:11434
   - LLM_PROVIDER=ollama, LLM_MODEL=minimax-m2.7:cloud
   - EMBED_PROVIDER=ollama, EMBED_MODEL=nomic-embed-text:latest
   - VECTOR_ENGINE=lancedb
4. 启动服务：node src/gbrain_mcp_server.js
5. 配置 OpenClaw/Claude/Hermes 使用 MCP 连接
```

---

## ✨ 核心能力

| 功能 | 说明 |
|------|------|
| 🧠 **记忆存储** | 情景/语义/实体记忆，自动提取实体和关系 |
| 🔍 **语义搜索** | 向量 + BM25 混合搜索，RRF 融合 |
| 🔗 **关系图谱** | 记忆关联网络，发现隐藏联系 |
| 📊 **实体检测** | 自动识别人物/组织/地点/概念 |
| 🔌 **MCP 接口** | 标准协议，兼容 OpenClaw/Claude/Hermes |

---

## ⚙️ 环境变量配置

创建 `.env` 文件：

```bash
# ─── LLM 配置 ───
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434
LLM_MAX_TOKENS=8192

# ─── Embedding 配置 ───
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434

# ─── 向量引擎 ───
VECTOR_ENGINE=lancedb

# ─── 存储 ───
DATA_DIR=~/.unified-memory/data
GRAPH_DB_PATH=~/.unified-memory/graph.json

# ─── 日志 ───
LOG_LEVEL=info
```

详细配置：[docs/CONFIG.md](docs/CONFIG.md)

---

## 🚀 快速开始

### 方式 1：直接运行

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install

# 配置环境变量
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
VECTOR_ENGINE=lancedb
EOF

# 启动服务
node src/gbrain_mcp_server.js
```

### 方式 2：配置到 AI 工具

**OpenClaw** (`~/.openclaw/openclaw.json`):
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

**Claude Desktop** (`claude_desktop_config.json`):
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

**Hermes** (`hermes.yaml`):
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


**Hermes SKILL.md**:
```bash
mkdir -p ~/.hermes/skills/memory/unified-memory
cp SKILL.md ~/.hermes/skills/memory/unified-memory/
```

---

## 🛠️ 可用工具

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `remember` | 存储记忆 | text, category, importance, entities |
| `search` | 语义搜索 | query, limit, entity, project, topic |
| `get_context` | 获取状态 | - |
| `graph_stats` | 图谱统计 | - |
| `cleanup` | 清理记忆 | threshold, max_age_days |

---

## 📋 完整配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| **LLM** | | |
| `LLM_PROVIDER` | 提供商 | ollama |
| `LLM_MODEL` | 模型名称 | minimax-m2.7:cloud |
| `LLM_BASE_URL` | API 地址 | http://localhost:11434 |
| `LLM_API_KEY` | API 密钥 | - |
| `LLM_MAX_TOKENS` | 最大输出 | 8192 |
| `LLM_TEMPERATURE` | 温度参数 | 0.7 |
| **Embedding** | | |
| `EMBED_PROVIDER` | 提供商 | ollama |
| `EMBED_MODEL` | 模型 | nomic-embed-text:latest |
| `EMBED_BASE_URL` | API 地址 | http://localhost:11434 |
| `EMBED_DIMENSION` | 向量维度 | 768 |
| **Ollama** | | |
| `OLLAMA_BASE_URL` | 服务地址 | http://localhost:11434 |
| `OLLAMA_HOST` | 主机别名 | http://localhost:11434 |
| **向量引擎** | | |
| `VECTOR_ENGINE` | 引擎类型 | lancedb |
| `VECTOR_DB_PATH` | 数据库路径 | ~/.unified-memory/ |
| **MCP** | | |
| `MCP_PORT` | HTTP 端口 | 38421 |
| `MCP_MODE` | 模式 | stdio |
| **性能** | | |
| `MAX_CONCURRENT` | 最大并发 | 10 |
| `SEARCH_LIMIT` | 结果限制 | 20 |
| `IMPORTANCE_THRESHOLD` | 重要性阈值 | 0.1 |
| `MAX_AGE_DAYS` | 保留天数 | 30 |

完整列表：[docs/CONFIG.md](docs/CONFIG.md)

---

## 📁 项目结构

```
unified-memory/
├── src/
│   ├── gbrain_mcp_server.js     # MCP 服务器入口
│   ├── gbrain-integration.js    # GBrain 集成模块
│   ├── memory_graph.js          # 记忆关联网络
│   ├── entity_detection.js      # 实体检测
│   ├── config.js                # 配置管理
│   ├── cache_semantic.js        # 向量 Embedding
│   └── brain_cli.js             # CLI 工具
├── docs/
│   ├── CONFIG.md               # 完整配置指南
│   ├── ARCHITECTURE.md         # 系统架构
│   └── MCP_INTERFACE.md        # MCP 接口规范
├── SKILL.md                    # OpenClaw Skill 定义
├── QUICK_START.md              # 快速安装指南
└── README.md
```

---

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 运行时 | Node.js 18+ |
| 协议 | MCP 1.0 (stdio) |
| LLM | ollama, openai, minimax, siliconflow |
| Embedding | ollama, openai, jina, siliconflow |
| 向量引擎 | LanceDB, ChromaDB, FAISS |
| 存储 | JSON (开发), PostgreSQL (生产) |

---

## 📦 安装

```bash
# 一键安装
npm install unified-memory

# 或克隆
git clone https://github.com/mouxangithub/unified-memory.git
```

---

## 📖 文档

- [一句话安装](QUICK_START.md) - 快速安装 + 配置
- [配置指南](docs/CONFIG.md) - 完整配置项列表
- [架构设计](docs/ARCHITECTURE.md) - 核心模块说明
- [MCP 接口](docs/MCP_INTERFACE.md) - 工具/资源/提示模板

---

## 🌐 链接

- **GitHub**: https://github.com/mouxangithub/unified-memory
- **npm**: 即将发布
- **ClawHub**: https://clawhub.ai/skill/unified-memory-v5

---

> "让 AI 拥有记忆，让记忆成为智能的基石。"