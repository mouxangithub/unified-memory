# 🧠 Unified Memory v5

> AI Agent 的统一记忆系统 | **自动记忆** | MCP 协议 | 一句话安装

**让 AI 拥有记忆，让记忆成为智能的基石。**

---

## ⚡ 一句话安装配置（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install && \
OLLAMA_BASE_URL=http://localhost:11434 && \
LLM_PROVIDER=ollama && LLM_MODEL=minimax-m2.7:cloud && \
EMBED_PROVIDER=ollama && EMBED_MODEL=nomic-embed-text:latest && \
VECTOR_ENGINE=lancedb && \
node src/gbrain_mcp_server.js
```

> ⚡ **安装后自动开启**：自动记忆（重要性 > 0.7 自动存储）+ 实体检测 + 相似记忆关联

---

## ✨ 核心能力

| 功能 | 说明 |
|------|------|
| 🧠 **记忆存储** | 情景/语义/实体记忆，**自动评估重要性** |
| 🤖 **自动记忆** | 重要性评分 > 0.7 时自动存储，智能判断 |
| 🔍 **语义搜索** | 向量 + BM25 混合搜索，RRF 融合 |
| 🔗 **关系图谱** | 记忆关联网络，发现隐藏联系 |
| 📊 **实体检测** | 自动识别人物/组织/地点/概念 |
| 🔌 **MCP 接口** | 标准协议，兼容 OpenClaw/Claude/Hermes |

---

## 🧠 自动记忆功能

### 工作原理

```
用户输入 → 重要性评分 → 评分 > 0.7？→ ✅ 自动存储
                                      ↓ 否
                                  ❌ 不存储（返回分析）
```

### 重要性评分算法（7维度）

| 维度 | 权重 | 说明 |
|------|------|------|
| 内容长度 | +0.1 | 10-500词适当加分 |
| 决策/偏好信号 | +0.2 | "决定"、"偏好"、"需要"等 |
| 情感/情绪信号 | +0.15 | "重要"、"紧急"、"担心"等 |
| 事实/信息性内容 | +0.15 | 陈述句加分 |
| 项目/任务关联 | +0.15 | "项目"、"任务"、"计划"等 |
| 实体检测 | +0.1 | 检测到实体加分 |
| 问句 | -0.1 | 问句内容降低分数 |

### 示例

| 用户输入 | 评分 | 结果 |
|----------|------|------|
| "我决定了，下次去上海出差住浦东香格里拉" | 0.82 | ✅ 自动存储 |
| "我需要买咖啡豆，G7 曼特宁那个" | 0.78 | ✅ 自动存储 |
| "今天天气怎么样？" | 0.35 | ❌ 不存储 |
| "顺便帮我查一下明天是否下雨" | 0.42 | ❌ 不存储 |

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

# ─── 自动记忆配置 ───
AUTO_MEMORY_THRESHOLD=0.7  # 重要性阈值，默认 0.7

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
AUTO_MEMORY_THRESHOLD=0.7
EOF

# 启动服务（自动记忆功能已内置）
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
          "EMBED_MODEL": "nomic-embed-text:latest",
          "VECTOR_ENGINE": "lancedb",
          "AUTO_MEMORY_THRESHOLD": "0.7"
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
        "EMBED_MODEL": "nomic-embed-text:latest",
        "VECTOR_ENGINE": "lancedb",
        "AUTO_MEMORY_THRESHOLD": "0.7"
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
        VECTOR_ENGINE: lancedb
        AUTO_MEMORY_THRESHOLD: 0.7
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
| `remember` | 存储记忆 | text, category, importance, **auto** |
| `search` | 语义搜索 | query, limit, entity, project, topic |
| `get_context` | 获取状态 | - |
| `graph_stats` | 图谱统计 | - |
| `cleanup` | 清理记忆 | threshold, max_age_days |
| `auto_analyze` | **重要性分析** | text（仅分析不存储） |

### 手动控制

```javascript
// 手动指定重要性（跳过自动评估）
await remember({
  text: "用户偏好：喜欢冷萃咖啡",
  importance: 0.9,  // 强制存储
  auto: false       // 禁用自动评估
});

// 预分析（仅查看评分，不存储）
await auto_analyze({
  text: "用户决定去上海出差"
});
// 返回: { score: 0.75, reasons: ["决策信号", "项目相关"], suggestion: "建议存储" }
```

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
| **自动记忆** | | |
| `AUTO_MEMORY_THRESHOLD` | 重要性阈值 | 0.7 |
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
│   ├── gbrain_mcp_server.js     # MCP 服务器入口（自动记忆）
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

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| **v1.1.0** | 2026-05-05 | 🆕 自动记忆功能 - 重要性评分 > 0.7 自动存储 |
| v1.0.0 | 2026-04-20 | 初始版本 - 基础记忆、搜索、图谱功能 |

---

> "让 AI 拥有记忆，让记忆成为智能的基石。"
---

## 高级功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **API Gateway** | `src/advanced/api_gateway/` | JWT/API Key认证、限流、日志、OpenAPI |
| **Version Control** | `src/advanced/version_control/` | 乐观锁、冲突解决、差异计算 |
| **Cache Manager** | `src/advanced/cache_manager/` | L1/L2多级缓存、淘汰策略 |
| **Monitoring** | `src/advanced/monitoring/` | Prometheus指标、健康检查 |
| **Backup/Restore** | `src/advanced/backup_restore/` | 增量/全量备份、恢复 |
| **Archival** | `src/advanced/archival/` | 冷热分层、自动归档 |
| **Benchmark** | `src/advanced/benchmark/` | 性能基准测试、对比分析 |

### 快速使用

```python
# API Gateway
from api_gateway import create_app
app = create_app()

# Version Control
from version_control import VersionManager
vm = VersionManager()

# Cache Manager
from cache_manager import CacheManager
cm = CacheManager()

# Monitoring
from monitoring import MetricsCollector, PrometheusExporter
collector = MetricsCollector()

# Backup/Restore
from backup_restore import BackupManager
bm = BackupManager(config)

# Benchmark
from benchmark import BenchmarkRunner
runner = BenchmarkRunner(config)
```