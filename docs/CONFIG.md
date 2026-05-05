# Unified Memory v5 配置文件

## 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# =============================================================================
# Unified Memory v5 — 环境配置
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# LLM 配置 (大型语言模型)
# ─────────────────────────────────────────────────────────────────────────────

# LLM 提供商: ollama | openai | minimax | kimi | custom
LLM_PROVIDER=ollama

# LLM 模型
LLM_MODEL=minimax-m2.7:cloud

# LLM API 地址
LLM_BASE_URL=http://localhost:11434

# LLM API Key (如需要)
LLM_API_KEY=your-api-key

# 最大输出tokens
LLM_MAX_TOKENS=8192

# 温度参数 (0-1，越低越确定性)
LLM_TEMPERATURE=0.7

# ─────────────────────────────────────────────────────────────────────────────
# Embedding 配置 (向量嵌入)
# ─────────────────────────────────────────────────────────────────────────────

# Embedding 提供商: ollama | openai | cohere | local
EMBED_PROVIDER=ollama

# Embedding 模型
EMBED_MODEL=nomic-embed-text:latest

# Embedding API 地址
EMBED_BASE_URL=http://localhost:11434

# Embedding 向量维度 (nomic-embed-text 为 768)
EMBED_DIMENSION=768

# 向量批量大小
EMBED_BATCH_SIZE=32

# ─────────────────────────────────────────────────────────────────────────────
# Ollama 配置 (统一配置，同时适用于 LLM 和 Embedding)
# ─────────────────────────────────────────────────────────────────────────────

# Ollama 服务地址
OLLAMA_BASE_URL=http://localhost:11434

# Ollama 模型列表 (逗号分隔)
OLLAMA_MODELS=minimax-m2.7:cloud,nomic-embed-text:latest

# Ollama 上下文窗口
OLLAMA_CONTEXT_SIZE=8192

# ─────────────────────────────────────────────────────────────────────────────
# 存储配置
# ─────────────────────────────────────────────────────────────────────────────

# 数据存储目录
DATA_DIR=/root/.openclaw/workspace/memory

# 向量数据库路径
VECTOR_DB_PATH=/root/.unified-memory/vector.lance

# 记忆图谱存储路径
GRAPH_DB_PATH=/root/.unified-memory/graph.json

# 备份目录
BACKUP_DIR=/root/.unified-memory/backups

# 日志级别: debug | info | warn | error
LOG_LEVEL=info

# ─────────────────────────────────────────────────────────────────────────────
# 向量引擎配置
# ─────────────────────────────────────────────────────────────────────────────

# 向量引擎: lancedb | chromadb | faiss | builtin
VECTOR_ENGINE=lancedb

# LanceDB 配置
LANCEDB_DB_PATH=/root/.unified-memory/lancedb

# ChromaDB 配置
CHROMA_DB_PATH=/root/.unified-memory/chroma

# ─────────────────────────────────────────────────────────────────────────────
# MCP 服务配置
# ─────────────────────────────────────────────────────────────────────────────

# MCP 服务端口 (HTTP 模式)
MCP_PORT=38421

# MCP 服务地址 (stdio | http)
MCP_MODE=stdio

# MCP 服务器名称
MCP_SERVER_NAME=gbrain-agent-brain

# ─────────────────────────────────────────────────────────────────────────────
# 性能配置
# ─────────────────────────────────────────────────────────────────────────────

# 最大并发请求数
MAX_CONCURRENT=10

# 缓存大小 (MB)
CACHE_SIZE=512

# 搜索结果数量限制
SEARCH_LIMIT=20

# 记忆重要性阈值
IMPORTANCE_THRESHOLD=0.1

# 记忆最大保留天数
MAX_AGE_DAYS=30
```

---

## 快速配置模板

### 方式 1: Ollama 本地模型 (推荐开发环境)

```bash
# LLM 和 Embedding 共用 Ollama
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434

EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434
```

### 方式 2: OpenAI (生产环境)

```bash
# LLM 使用 OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxx

# Embedding 使用 OpenAI
EMBED_PROVIDER=openai
EMBED_MODEL=text-embedding-3-small
EMBED_BASE_URL=https://api.openai.com/v1
```

### 方式 3: MiniMax (国内生产环境)

```bash
# MiniMax API
LLM_PROVIDER=minimax
LLM_MODEL=minimax-m2.7
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_API_KEY=xxx

# 向量使用 MiniMax
EMBED_PROVIDER=minimax
EMBED_MODEL=embo-01
```

---

## 代码中使用配置

```javascript
import { config } from './config.js';

// 获取 LLM 配置
const llmConfig = {
  provider: config.get('LLM_PROVIDER'),
  model: config.get('LLM_MODEL'),
  baseUrl: config.get('LLM_BASE_URL'),
  apiKey: config.get('LLM_API_KEY'),
  maxTokens: config.get('LLM_MAX_TOKENS'),
  temperature: config.get('LLM_TEMPERATURE'),
};

// 获取 Embedding 配置
const embedConfig = {
  provider: config.get('EMBED_PROVIDER'),
  model: config.get('EMBED_MODEL'),
  baseUrl: config.get('EMBED_BASE_URL'),
  dimension: config.get('EMBED_DIMENSION'),
};

// 获取 Ollama 配置
const ollamaConfig = {
  baseUrl: config.get('OLLAMA_BASE_URL'),
  models: config.get('OLLAMA_MODELS').split(','),
};
```

---

## 配置优先级

1. **环境变量** (最高优先级)
2. **.env 文件**
3. **config.json 默认配置**
4. **内置默认值** (最低优先级)

---

## 配置检查命令

```bash
# 检查当前配置
node -e "
import { config } from './src/config.js';
console.log('LLM:', config.get('LLM_PROVIDER'), config.get('LLM_MODEL'));
console.log('Embed:', config.get('EMBED_PROVIDER'), config.get('EMBED_MODEL'));
console.log('Ollama:', config.get('OLLAMA_BASE_URL'));
"
```
