---

<div align="center">

# 🧠 Unified Memory v2.2 (unified-memory)

> **🤖 Created by 小智 AI (OpenClaw)**  
> Author: 刘选权 (ou_7b3a4352f86486ebdaf0de572093afb1)  
> Framework: OpenClaw Agent | Node.js ESM | 86 MCP Tools

**Project Path**: `/root/.openclaw/workspace/skills/unified-memory/`

---

## 🌍 Documentation Index | 文档索引

| Language | README | Skill |
|----------|--------|-------|
| 🇨🇳 中文 | [README.md](README.md) | [SKILL.md](SKILL.md) |
| 🇺🇸 English | [README_EN.md](README_EN.md) ✅ | [SKILL_EN.md](SKILL_EN.md) ✅ |

---

</div>

---

## Architecture

```
OpenClaw Agent
└── unified-memory-ts (Node.js ESM Skill Layer)
    ├── memory-lancedb-pro (OpenClaw Built-in Plugin) ← Core Storage Engine
    │   ├── Hybrid Search (BM25 + Vector)
    │   ├── Cross-Encoder Rerank
    │   ├── Weibull Decay
    │   ├── Smart Extraction (LLM)
    │   └── Multi-Scope Isolation
    │
    └── 129 Node.js Modules
        ├── MCP Server (11 tools)
        ├── REST API Server
        ├── WebUI Dashboard
        ├── CLI Tools
        ├── Workflow Engine
        ├── Sandbox
        ├── Code Generator
        ├── Push System
        └── LLM Provider (Multi-backend)
```

---

## Core Features

| Feature | Description |
|---------|-------------|
| 🔄 **Persistent Context** | No more re-understanding each session |
| 🔍 **Hybrid Search** | BM25 + Vector + RRF fusion (fully local) |
| 💬 **Auto-Store** | Hooks mode, no manual calls needed |
| 📊 **User Insights** | Category distribution, tool usage analysis |
| 🧹 **Smart Forget** | Auto-evict low-value memories |
| 🔗 **Knowledge Graph** | Entity extraction and relationship visualization |
| 🤝 **Multi-Agent** | Multi-agent memory sync |
| 🏥 **Health Check** | Complete system health monitoring |

---

## Quick Start

```bash
# 1. Run installer
cd /root/.openclaw/workspace/skills/unified-memory-ts/
bash scripts/install.sh

# 2. Verify installation
node src/cli/index.js health

# 3. Store first memory
node src/cli/index.js store "Hello memory"

# 4. Search memories
node src/cli/index.js search "Hello"
```

---

## MCP Tools (11 Tools)

| Tool | Description |
|------|-------------|
| `memory_search` | Hybrid BM25 + Vector search |
| `memory_store` | Store new memories |
| `memory_recall` | Retrieve specific memory |
| `memory_list` | List all memories |
| `memory_update` | Update existing memory |
| `memory_delete` | Delete memory |
| `memory_stats` | System statistics |
| `memory_insights` | User behavior insights |
| `memory_export` | Export to JSON/Markdown/CSV |
| `memory_dedup` | Deduplicate similar memories |
| `memory_health` | System health check |

---

## CLI Commands

```bash
node src/cli/index.js store "text" [--category] [--importance]
node src/cli/index.js search "query" [--limit] [--category]
node src/cli/index.js list [--category]
node src/cli/index.js update <id> "new text"
node src/cli/index.js delete <id>
node src/cli/index.js stats
node src/cli/index.js health
node src/cli/index.js export --format json|markdown|csv
```

---

## Development

```bash
# Install dependencies
npm install

# Test MCP Server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node src/index.js

# CLI help
node src/cli/index.js help

# Run benchmark
node src/benchmark/benchmark.js
```

---

## Version

Current version: **v2.0.0** (2026-03-27)

---

## License

MIT

---

## 🔗 Other Languages | 其他语言

- [中文文档](./SKILL.md) - 完整中文文档
- [README.md](./README.md) - Full English documentation
- [README_CN.md](./README_CN.md) - 完整中文文档
- [README_QUICK_START.md](./README_QUICK_START.md) - 🚀 Quick start guide
