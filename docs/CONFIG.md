# Unified Memory v5 — 完整配置指南

## 一句话配置（发给 AI）

```
请帮我配置 Unified Memory v5 的环境变量：
- LLM: provider=ollama, model=minimax-m2.7:cloud, base_url=http://localhost:11434
- Embedding: provider=ollama, model=nomic-embed-text:latest, base_url=http://localhost:11434
- 向量引擎: lancedb
- 数据目录: ~/.unified-memory/
```

---

## 环境变量完整列表

### LLM 配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|----------|------|--------|--------|
| `LLM_PROVIDER` | LLM 提供商 | ollama | ollama, openai, siliconflow, minimax, custom |
| `LLM_MODEL` | 模型名称 | minimax-m2.7:cloud | - |
| `LLM_BASE_URL` | API 地址 | http://localhost:11434 | - |
| `LLM_API_KEY` | API 密钥 | - | - |
| `LLM_MAX_TOKENS` | 最大输出 | 8192 | - |
| `LLM_TEMPERATURE` | 温度参数 | 0.7 | 0-1 |

### Embedding 配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|----------|------|--------|--------|
| `EMBED_PROVIDER` | 向量提供商 | ollama | ollama, openai, jina, siliconflow, custom |
| `EMBED_MODEL` | 向量模型 | nomic-embed-text | - |
| `EMBED_BASE_URL` | API 地址 | http://localhost:11434 | - |
| `EMBED_DIMENSION` | 向量维度 | 768 | - |
| `EMBED_BATCH_SIZE` | 批量大小 | 32 | - |

### Ollama 统一配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `OLLAMA_BASE_URL` | Ollama 服务地址 | http://localhost:11434 |
| `OLLAMA_HOST` | Ollama 主机 (别名) | http://localhost:11434 |
| `OLLAMA_LLM_MODEL` | Ollama LLM 模型 | minimax-m2.7:cloud |
| `OLLAMA_EMBED_MODEL` | Ollama Embedding 模型 | nomic-embed-text |
| `OLLAMA_MODELS` | 模型列表 (逗号分隔) | - |
| `OLLAMA_CONTEXT_SIZE` | 上下文窗口 | 8192 |

### 向量引擎配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|----------|------|--------|--------|
| `VECTOR_ENGINE` | 向量引擎 | lancedb | lancedb, chromadb, faiss, builtin |
| `VECTOR_DB_PATH` | 向量数据库路径 | ~/.unified-memory/ | - |
| `LANCEDB_DB_PATH` | LanceDB 路径 | ~/.unified-memory/lancedb | - |
| `CHROMA_DB_PATH` | ChromaDB 路径 | ~/.unified-memory/chroma | - |

### 存储配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `DATA_DIR` | 数据存储目录 | ~/.openclaw/workspace/memory |
| `GRAPH_DB_PATH` | 图谱存储路径 | ~/.unified-memory/graph.json |
| `BACKUP_DIR` | 备份目录 | ~/.unified-memory/backups |
| `LOG_DIR` | 日志目录 | ~/.openclaw/workspace/memory/logs |

### MCP 服务配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|----------|------|--------|--------|
| `MCP_PORT` | HTTP 模式端口 | 38421 | - |
| `MCP_MODE` | 服务模式 | stdio | stdio, http |
| `MCP_SERVER_NAME` | 服务器名称 | gbrain-agent-brain | - |

### 性能配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `MAX_CONCURRENT` | 最大并发请求 | 10 |
| `CACHE_SIZE` | 缓存大小 (MB) | 512 |
| `SEARCH_LIMIT` | 搜索结果限制 | 20 |
| `IMPORTANCE_THRESHOLD` | 重要性阈值 | 0.1 |
| `MAX_AGE_DAYS` | 最大保留天数 | 30 |
| `LOG_LEVEL` | 日志级别 | info |

### API Key 配置

| 环境变量 | 说明 | 适用提供商 |
|----------|------|-----------|
| `OPENAI_API_KEY` | OpenAI API Key | openai |
| `JINA_API_KEY` | Jina API Key | jina |
| `SILICONFLOW_API_KEY` | SiliconFlow API Key | siliconflow |
| `MINIMAX_API_KEY` | MiniMax API Key | minimax |

---

## 快速配置模板

### 方式 1: Ollama 本地 (开发环境) ⭐推荐

```bash
# LLM + Embedding 共用 Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest

# 向量引擎
VECTOR_ENGINE=lancedb
LANCEDB_DB_PATH=~/.unified-memory/lancedb

# 存储
DATA_DIR=~/.unified-memory/data
GRAPH_DB_PATH=~/.unified-memory/graph.json
```

### 方式 2: OpenAI (生产环境)

```bash
# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxx

# Embedding
EMBED_PROVIDER=openai
EMBED_MODEL=text-embedding-3-small
EMBED_BASE_URL=https://api.openai.com/v1

# 向量引擎
VECTOR_ENGINE=lancedb
```

### 方式 3: MiniMax (国内生产)

```bash
# LLM
LLM_PROVIDER=minimax
LLM_MODEL=minimax-m2.7
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_API_KEY=xxx

# Embedding (用 SiliconFlow 或 Jina)
EMBED_PROVIDER=siliconflow
EMBED_MODEL=BAAI/bge-m3
EMBED_BASE_URL=https://api.siliconflow.cn/v1
EMBED_API_KEY=xxx
```

### 方式 4: SiliconFlow 一站式 (国内)

```bash
# LLM + Embedding 共用 SiliconFlow
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=xxx

EMBED_PROVIDER=siliconflow
EMBED_MODEL=BAAI/bge-m3
EMBED_BASE_URL=https://api.siliconflow.cn/v1
EMBED_API_KEY=xxx
```

---

## 代码引用配置

```javascript
// 从 config.js 读取配置
import { EMBED_PROVIDERS, LLM_PROVIDERS, getConfig } from './src/config.js';

// 获取当前 LLM 配置
const llmProvider = LLM_PROVIDERS.find(p => p.name === process.env.LLM_PROVIDER || 'ollama');

// 获取当前 Embedding 配置
const embedProvider = EMBED_PROVIDERS.find(p => p.name === process.env.EMBED_PROVIDER || 'ollama');

// 直接获取环境变量
const baseUrl = process.env.LLM_BASE_URL || process.env.OLLAMA_BASE_URL;
const model = process.env.LLM_MODEL;
```

---

## 配置优先级

```
1. 环境变量 (最高优先级)
   ↓
2. .env 文件
   ↓
3. config.js 默认值 (最低优先级)
```

---

## 验证配置

```bash
# 检查配置是否生效
node -e "
import { EMBED_PROVIDERS, LLM_PROVIDERS } from './src/config.js';
console.log('=== LLM 配置 ===');
console.log('Provider:', LLM_PROVIDERS[0].name);
console.log('Model:', LLM_PROVIDERS[0].model);
console.log('BaseURL:', LLM_PROVIDERS[0].baseURL);
console.log('');
console.log('=== Embed 配置 ===');
console.log('Provider:', EMBED_PROVIDERS[0].name);
console.log('Model:', EMBED_PROVIDERS[0].model);
console.log('BaseURL:', EMBED_PROVIDERS[0].baseURL);
"
```

---

## 一键配置命令

```bash
# 克隆后一键配置 (Ollama 本地)
cd unified-memory && \
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